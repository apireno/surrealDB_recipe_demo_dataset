import asyncio
import time
import math
import ast
import os
from surrealDB_embedding_model.embedding_model_constants import DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, ArgsLoader,GeminiConstants,DATA_FOLDER
from gemini import GeminiHelper
from extraction_ref_data_helpers import RefDataHelper
from helpers import Helpers

out_folder = THIS_FOLDER + "/logging/act_heir_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
recipe_constants = RecipeDataConstants()
gemini_constants = GeminiConstants()


Helpers.ensure_folders([out_folder,DATA_FOLDER])




GEMINI_ACTION_HEIRARCHY_PROMPT = """
-Goal-

You are a culinary arts professor and linguist who excels at finding connections in data.
Given the list of entities contained in the attached file, use your knowledge as a chef out how they can be they can be organized into a heiarchy.

For instance "chopping", "slicing", "mincing" and "dicing" are all knife skills that we could broadly call "cutting".
While "washing" and "thawing" are all entities that could be considered "prepping"
So in this instance we would have a 2-level heirachy of "prep"->"wash","thaw" and "cut"->"mince","slice","chop"

The file will have the following sections:
    - Entities that have no matches as of yet between the delimiters: <{no_match_list_delimiter}> and </{no_match_list_delimiter}>
         -The format for these entities is:
            <{no_match_list_delimiter}> 
            [
                "entity1",
                "entity2",
                "entity3",
                ...
                "entityN",
            ]
            </{no_match_list_delimiter}>
    - Exhaustive list of the the permissible entities for substitutes <{full_list_delimiter}> and </{full_list_delimiter}>
        -The format for these entities is:
            <{full_list_delimiter}>
            [
                "entity1",
                "entity2",
                "entity3",
                ...
                "entityN",
            ]
            </{full_list_delimiter}>
    - Substitute matches that have already been identified but could be refined and/or additional substitutes could be found listed between the delimiters <{already_matched_delimeter}> and </{already_matched_delimeter}>.
        -The format for these entities is:
            <{already_matched_delimeter}>
            [
                {{"entity":"<source_entity1>", "parent":"<parent_entityX>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
                {{"entity":"<source_entity2>", "parent":"<parent_entityY>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
                {{"entity":"<source_entity3>", "parent":"<parent_entity1Z>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
                ...
                {{"entity":"<source_entityN>", "parent":"<parent_entityX>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
            ]
            </{already_matched_delimeter}>

    
DO NOT add any explanatory text outside of the instructions below in the specific format described.



-Steps-
- As a chef, for each of entities listed in the first section of the input file, identify all the parent from the second section.
- If a parent action cannot be identified then indicate the parent as the enitity itself. I.E. the top of the heirachy should have both parent and entity fields equal eachother
- There field entity should be unique in your output, IE every entity should only have one parent.
- For each of the entity to parent entity pairs extracted extract the following information:
    -entity: the name of the entity
    -parent: the name of the parent entity
    -relationship_rationale: your rationale for the parent <> entity relationship 
    -relationship_confidence: a numeric score of 1-10 indicating your confidence in the relationship
    -Format each relationship as a an array of json objects with the following format:
    {{"entity":"<entity>", "parent":"<parent_entity>",  "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}}
- The top section of the file will be the entities that have yet to be matched between the delimiters: <{no_match_list_delimiter}> and </{no_match_list_delimiter}>; you MUST address these first!
- Only choose parents from the second section that begins are between the delimiters <{full_list_delimiter}> and </{full_list_delimiter}>.
- Do not dupilcate *explicit* combinations of entities and subs.
    -E.G.  This is invalid:
        [
            {{"entity":"chop", "parent":"cut", "rationale":"chopping is a form of cutting which are knife skills"}},
            {{"entity":"chop", "parent":"prepare", "rationale":"chopping is a form of prepping"}},
        ]
    -E.G. This is valid however since the lemon and lime are reversed and hence not explicitly the same combination:
        [
            {{"entity":"chop", "parent":"cut", "rationale":"chopping is a form of cutting which are knife skills"}},
            {{"entity":"cut", "parent":"prepare", "rationale":"cutting is a form of prepping"}},
            {{"entity":"prepare", "parent":"prepare", "rationale":"prepping is the top of the heirarchy"}},
        ]

- Due to max tokens in output we need to call this in a loop. So limit the results to the be the top {max_results} results.
- Again only return maximum of {max_results} relationships! Do not exceed  {max_results} rows returned!
- If no entries are left in the un-matched section then proceed to refine the matches and double check your work.
- When finished generating the whole list or reach the token count, output the completion delimiter: {completion_delimiter}


 
###################
-Examples-
######################
Example 1:

<{no_match_list_delimiter}> 
[
"chop",
"slice",
"mince",
"dice",
"cut",
"thaw",
]
</{no_match_list_delimiter}>
<{full_list_delimiter}> 
[
"chop",
"slice",
"mince",
"dice",
"cut",
"thaw",
"wash",
"prep",
]
</{full_list_delimiter}>
<{already_matched_delimeter}>
[
    {{"entity":"chop", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"slice", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"mince", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"dice", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"cut", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"thaw", "parent":"",  "rationale":"", "confidence":0}},
    {{"entity":"wash", "parent":"prep",  "rationale":"Washing is a form of prep before yuu cook. You may wash after but in a culinary vocabulary it is likely meant as prep.", "confidence":7}},
    {{"entity":"prep", "parent":"prep",  "rationale":"Prepping is a top of a heirarchy for all prep work", "confidence":10}},
]
</{already_matched_delimeter}>
######################
<output>
[
    {{"entity":"chop", "parent":"cut",  "rationale":"chopping is a form of cutting in a culinary vocabulary", "confidence":9}},
    {{"entity":"slice", "parent":"cut",  "rationale":"slicing is a form of cutting in a culinary vocabulary", "confidence":9}},
    {{"entity":"mince", "parent":"cut",  "rationale":"mincing is a form of cutting" in a culinary vocabulary, "confidence":9}},
    {{"entity":"dice", "parent":"cut",  "rationale":"dicing is a form of cutting in a culinary vocabulary", "confidence":9}},
    {{"entity":"cut", "parent":"cut",  "rationale":"Cutting a braod definition for using a knife. I am resonably confident it should be a first order member of the heirarchy", "confidence":7}},
    {{"entity":"thaw", "parent":"prep",  "rationale":"Thawing is something you must do before you cook and hence prep work", "confidence":9}},
]
</output>
"""


CONTINUE_PROMPT = """MANY entities have missing parents or more suitable parents to choose from the list. 
Tackle the entities first section that is between the <{no_match_list_delimiter}> delimiters.
Only choose parents from the section between the <{full_list_delimiter}> delimiters.
If there entity list in the <{no_match_list_delimiter}> section is empty then move on to identify better parents that have a higher confidence.
Again address items between the <{no_match_list_delimiter}> delimiters first! Do not refine your answers until that list is empty.
Entities and parents are only valid if they exist in the  <{full_list_delimiter}> section.
Do NOT extract the entities from the examples sections. 
Do not add any explanatory text outside of the instructions you were given as the OUTPUT.
Due to max tokens in output we need to call this in a loop. So limit the results to the top {max_results} remaining results; you will find more matches in another loop.
Again only return maximum of {max_results} relationships! Do not exceed  {max_results} rows returned!
And remember to ALWAYS end your response with the completion delimiter: {completion_delimiter}\n"""


CHECK_LOOP_PROMPT = "It appears some entities have missing parents or more suitable parents may have been missed. We need one and only one least one line per entity.  Answer YES | NO if there are still better parent<>child relationships that need to be added. ONLY answer with 'YES' or 'NO' and nothing else!\n"



PROMPT_BATCH_SIZE = 100
ENTITY_TYPE = "cooking_action"



NO_MATCH_LIST_DELIMITER = "NO_MATCHES"
FULL_LIST_DELIMITER = "ONLY_PERMISSIBLE_ENTITIES"
ALREADY_MATCHED_DELIMETER = "IDENTIFIED_MATCHES"




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


    action_unmatched_list = RefDataHelper.find_unmatched_items( 
                action_list,action_match_list,None,"entity"
            )
    


    print(f"Loop {loop_counter} of {max_loop_count} loops | substitutes matched: {len(action_match_list)} | unmatched: {len(action_unmatched_list)} of {len(action_list)} actions")
    

    init_messages = []
    init_prompt_text = GEMINI_ACTION_HEIRARCHY_PROMPT.format(
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER,
        no_match_list_delimiter = NO_MATCH_LIST_DELIMITER,
        full_list_delimiter = FULL_LIST_DELIMITER,
        already_matched_delimeter = ALREADY_MATCHED_DELIMETER,
        max_results = PROMPT_BATCH_SIZE,
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
        max_results = PROMPT_BATCH_SIZE,
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER,
        no_match_list_delimiter = NO_MATCH_LIST_DELIMITER,
        full_list_delimiter = FULL_LIST_DELIMITER,
        already_matched_delimeter = ALREADY_MATCHED_DELIMETER
        )

    continue_prompt_messages.append( 
                    {"role": "user", "parts": [{"text": continue_prompt_prompt_text}]}
        )


   
    gemini_processor = GeminiHelper(gemini_constants,debug_file=debug_file)

    
    working_action_matches_file = out_folder + f"/working_action_matches_{loop_counter}.txt"
    messages_to_use = []
    if(loop_counter == 0):
        initial_action_file = out_folder + "/initial_action_match.txt"
        RefDataHelper.write_list_to_file(action_list,initial_action_file)
        RefDataHelper.write_actions_and_matched_actions_to_file(
            action_list,
            action_match_list,
            action_unmatched_list, NO_MATCH_LIST_DELIMITER,FULL_LIST_DELIMITER,ALREADY_MATCHED_DELIMETER,
            working_action_matches_file)
        messages_to_use = init_messages
    else:
        messages_to_use = continue_prompt_messages



    new_matches_list = get_matches(
        gemini_processor,messages_to_use,working_action_matches_file
    )


    action_match_list = RefDataHelper.merge_dicts_over_single_key(
        action_match_list,new_matches_list,"entity"
    )

    action_unmatched_list = RefDataHelper.find_unmatched_items( 
                action_list,action_match_list,None,"entity"
            )
    

    loop_counter += 1
    working_action_matches_file = out_folder + f"/working_action_matches_{loop_counter}.txt"

    RefDataHelper.write_actions_and_matched_actions_to_file(
        action_list,
        action_match_list,
        action_unmatched_list, NO_MATCH_LIST_DELIMITER,FULL_LIST_DELIMITER,ALREADY_MATCHED_DELIMETER,
        working_action_matches_file)
    continue_loop = check_are_matches_complete(gemini_processor,check_are_matches_complete_messages,working_action_matches_file)




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

    args_loader = ArgsLoader("STEP 0.4 - LLM Extract action heirarchy",db_constants,recipe_constants,gemini_constants)
    args_loader.LoadArgs()
    args_loader.print()

    with open(recipe_constants.EXTRACTED_COOKING_ACTIONS_FILE, 'r') as f:
            action_list =  ast.literal_eval(f.read())


    debug_file = out_folder + "/gemini_debug.txt"
    matched_list = process_action_matching(action_list,debug_file=debug_file)
    
    RefDataHelper.write_matched_actions_to_file(matched_list,recipe_constants.MATCHED_COOKING_ACTIONS_FILE)


        

if __name__ == "__main__":
    asyncio.run(main())


    