import asyncio
import time
import math
import ast
import os
import pandas as pd
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader,GeminiConstants
from surql_ref_data import SurqlReferenceData
from recipe_data_surql_ddl import RecipeDataSurqlDDL
from gemini import GeminiHelper

out_folder = THIS_FOLDER + "/logging/act_heir_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
data_folder = THIS_FOLDER + "/data"
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
gemini_constants = GeminiConstants()
args_loader = RecipeArgsLoader("STEP 0.4 - LLM Extract action heirarchy",db_constants,embed_constants,recipe_constants,gemini_constants)
args_loader.LoadArgs()





GEMINI_ACTION_HEIRARCHY_PROMPT = """
-Goal-

You are a data processor and researcher who excels at finding connections in data.
Given the list of entities contained in the attached file, reason out how they can be organized into a heiarchy.
The entities in the file are all of the type {entity_type} which should only be considered via the vocabulary of the culinary arts.
The file will have the list of entities that haven't been processed listed with a confidence of 0.
DO NOT add any explanatory text outside of the instructions below in the specific format described.
Organize the entities in a heirarchy such that they are easily grouped and undestood relative to eachother.

For instance "chopping", "slicing", "mincing" and "dicing" are all knife skills that we could broadly call "cutting".
While "washing" and "thawing" are all entities that could be considered "prepping"
So in this instance we would have a 2-level heirachy of "prep"->"wash","thaw" and "cut"->"mince","slice","chop"

-Steps-

- For each of entities listed, identify a parent entity also in the list if none exits.
- Parents must be selected from within the overall list of entities. IE do NOT add any parents that are not in the entity list.
- If no parent can be found as it is logically the most broad definition in your heirarchy indicate itself as the parent.
- There field entity should be unique in your output, IE every entity should only have one parent.
- For each of the entity to parent entity pairs extracted extract the following information:
    -entity: the name of the entity
    -parent: the name of the parent entity
    -relationship_rationale: your rationale for the parent <> entity relationship 
    -relationship_confidence: a numeric score of 1-10 indicating your confidence in the relationship
    -Format each relationship as a an array of json objects with the following format:
    {{"entity":"{entity_type}:`<entity>`", "parent":"{entity_type}:`<parent_entity>`",  "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}}
- Due to size constraints only return the top {max_count} matches based on your confidence.
- There shouldn't be any orphaned entities. IE no entity should have itself as a parent and no child relationships.
- Output only the top {max_count} new matches in which the data is different than the input.
- When finished generating output the completion delimiter: {completion_delimiter}

 
###################
-Examples-
######################
Example 1:
entity type: cooking_action
<input>
[
    {{"entity":"cooking_action:`chop`", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"cooking_action:`slice`", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"cooking_action:`mince`", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"cooking_action:`dice`", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"cooking_action:`cut`", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"cooking_action:`thaw`", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"cooking_action:`wash`", "parent":"cooking_action:`prep`",  "rationale":"Washing is a form of prep before yuu cook. You may wash after but in a culinary vocabulary it is likely meant as prep.", "confidence":7}},
    {{"entity":"cooking_action:`prep`", "parent":"cooking_action:`prep`",  "rationale":"Prepping is a top of a heirarchy for all prep work", "confidence":10}},
]
</input>
######################
<output>
[
    {{"entity":"cooking_action:`chop`", "parent":"cooking_action:`cut`",  "rationale":"chopping is a form of cutting in a culinary vocabulary", "confidence":9}},
    {{"entity":"cooking_action:`slice`", "parent":"cooking_action:`cut`",  "rationale":"slicing is a form of cutting in a culinary vocabulary", "confidence":9}},
    {{"entity":"cooking_action:`mince`", "parent":"cooking_action:`cut`",  "rationale":"mincing is a form of cutting" in a culinary vocabulary, "confidence":9}},
    {{"entity":"cooking_action:`dice`", "parent":"cooking_action:`cut`",  "rationale":"dicing is a form of cutting in a culinary vocabulary", "confidence":9}},
    {{"entity":"cooking_action:`cut`", "parent":"cooking_action:`cut`",  "rationale":"Cutting a braod definition for using a knife. I am resonably confident it should be a first order member of the heirarchy", "confidence":7}},
    {{"entity":"cooking_action:`thaw`", "parent":"cooking_action:`prep`",  "rationale":"Thawing is something you must do before you cook and hence prep work", "confidence":9}},
]
</output>
"""

CONTINUE_PROMPT = """MANY entities have missing parents or more suitable parents to choose from the list. 
First tackle any entities that are missing parents or have a 0 confidence score.
If all of those are accounted for, try to identify better matches with low confidence scores. 
Make sure to have one and only one parent for every entity even if it is to itself. 
Make sure to not have any entities that only have themselves as a parent and no children. 
There field entity should be unique in your output, IE every entity should only have one parent.
Due to size constraints only return the top {max_count} matches based on your confidence.
And remember to ALWAYS end your response with the completion delimiter: {completion_delimiter}\n"""

CHECK_LOOP_PROMPT = "It appears some entities have missing parents or more suitable parents may have been missed. We need one and only one least one line per entity.  Answer YES | NO if there are still better parent<>child relationships that need to be added. ONLY answer with 'YES' or 'NO' and nothing else!\n"



PROMPT_BATCH_SIZE = 100
ENTITY_TYPE = "cooking_action"

def rsq(s):
    return s.replace("'", "")

def extend_action_to_action_match_list(action_list):
    action_match_list = []
    for item in action_list:
        action_match_list.append(
            {
                "entity":f"{ENTITY_TYPE}:`{item}`","parent":"", "rationale":"", "confidence":0
            }
        )
    return action_match_list


def write_actions_as_matched_actions_to_file(action_list,action_file,file_mode="w"):
    action_match_list = extend_action_to_action_match_list(action_list)
    write_matched_actions_to_file(action_match_list,action_file,file_mode = file_mode)


def write_actions_to_file(action_list,action_file,file_mode="w"):
     with open(action_file, file_mode) as f:
        f.write("[\n")
        for item in action_list:           
            f.write(f"'{item},\n")
        f.write("]")

def write_matched_actions_to_file(action_match_list,action_file,file_mode="w"):
    with open(action_file, file_mode) as f:
        f.write("[\n")
        for item in action_match_list:           
            f.write(f"{{'entity':'{rsq(item["entity"])}','parent':'{rsq(item["parent"])}','rationale':'{rsq(item["rationale"])}','confidence':{item["confidence"]}}},\n")
        f.write("]")



def get_matches(
    gemini_processor: GeminiHelper,
    prompt_messages,file_attachment):
    attached_file = gemini_processor.attach_file(file_attachment)
     #generate a response from the LLM
    return gemini_processor.generate_content_until_complete_with_post_process_function(
        ast.literal_eval,prompt_messages,attached_file
    )
    


def check_are_matches_complete(
    gemini_processor,
    prompt_messages,file_attachment):

    attached_file = gemini_processor.attach_file(file_attachment)
    ai_response = gemini_processor.generate_content(prompt_messages,attached_file)
    return (ai_response == "YES")


def process_action_matching(action_list,action_match_list=[],loop_counter=0,debug_file=None):
    
    max_loop_count = math.floor(2*len(action_list)/PROMPT_BATCH_SIZE)

    print(f"Loop {loop_counter} of {max_loop_count} enrichments  {len(action_match_list)} matches of {len(action_list)} actions")
    
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    working_actions_matches_file = out_folder + f"/working_actions_matches_{loop_counter}.txt"
    if(loop_counter == 0):
        action_match_list = extend_action_to_action_match_list(action_list)
        initial_action_file = out_folder + "/initial_action_match.txt"
        write_matched_actions_to_file(action_match_list,working_actions_matches_file)
        write_actions_as_matched_actions_to_file(action_list,initial_action_file)

    init_messages = []
    init_prompt_text = GEMINI_ACTION_HEIRARCHY_PROMPT.format(
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER,
        max_count = PROMPT_BATCH_SIZE,
        entity_type = ENTITY_TYPE
        )
    init_messages.append( 
                {"role": "user", "parts": [{"text": init_prompt_text}]}
    )

    check_are_matches_complete_messages = init_messages.copy()
    continue_prompt_messages = init_messages.copy()





    check_are_matches_complete_prompt_text = CHECK_LOOP_PROMPT
    
    check_are_matches_complete_messages.append( 
                    {"role": "user", "parts": [{"text": check_are_matches_complete_prompt_text}]}
        )
    

    continue_prompt_prompt_text = CONTINUE_PROMPT.format(  
        max_count = PROMPT_BATCH_SIZE,
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER
        )

    continue_prompt_messages.append( 
                    {"role": "user", "parts": [{"text": continue_prompt_prompt_text}]}
        )

    
   
    gemini_processor = GeminiHelper(gemini_constants,debug_file=debug_file)

    
    messages_to_use = []
    if(loop_counter == 0):
        messages_to_use = init_messages
    else:
        messages_to_use = continue_prompt_messages
    



    new_matches = get_matches(
        gemini_processor,messages_to_use,working_actions_matches_file
    )

    for new_match in new_matches:
        for i, old_match in enumerate(action_match_list):  # Use enumerate to get index
            if new_match["entity"].lower() == old_match["entity"].lower():
                action_match_list[i] = new_match  # Update the list directly using index
                break
            
    

    loop_counter += 1
    working_actions_matches_file = out_folder + f"/working_actions_matches_{loop_counter}.txt"
    write_matched_actions_to_file(action_match_list,working_actions_matches_file)
    continue_loop = check_are_matches_complete(gemini_processor,check_are_matches_complete_messages,working_actions_matches_file)




    if continue_loop and loop_counter<max_loop_count:
        return process_action_matching(action_list,action_match_list,loop_counter,debug_file)
    else:
        print(
            f""" 
            Step 0.4 -- extracted action heirarchy    
            Complete 
            {len(action_list)} actions
            {action_list[0]} - {action_list[-1]}
            {len(action_match_list)} matches
            """)
        return action_match_list
       


    



async def main():

    
    args_loader.print()

    with open(recipe_constants.EXTRACTED_COOKING_ACTIONS_FILE, 'r') as f:
            action_list =  ast.literal_eval(f.read())


    debug_file = out_folder + "/gemini_debug.txt"
    matched_list = process_action_matching(action_list,debug_file=debug_file)
    
    write_matched_actions_to_file(matched_list,recipe_constants.MATCHED_COOKING_ACTIONS_FILE)


        

if __name__ == "__main__":
    asyncio.run(main())


    