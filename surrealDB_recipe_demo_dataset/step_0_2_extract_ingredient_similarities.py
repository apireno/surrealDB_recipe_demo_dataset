import asyncio
import time
import ast
import os
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader,GeminiConstants,DATA_FOLDER
from gemini import GeminiHelper
from extraction_ref_data_helpers import RefDataHelper
from helpers import Helpers

out_folder = THIS_FOLDER + "/logging/ing_sim_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
gemini_constants = GeminiConstants()
args_loader = RecipeArgsLoader("STEP 0.2 - LLM Extract ingredients similarities",db_constants,embed_constants,recipe_constants,gemini_constants)
args_loader.LoadArgs()

Helpers.ensure_folders([out_folder,DATA_FOLDER])

ENTITY_REPLACEMENT_PROMPT = """
-Goal-
You are a culinary arts professor and linguist who excels at finding connections in data.
Given the list of entities contained in the attached file, use your knowledge as a chef out how they can be replaced with one another for substitution in a recipe.
The file will have the following sections:
    - Entities that have no matches as of yet between the delimiters: <{no_match_list_delimiter}> and </{no_match_list_delimiter}>
         -The format for these entities is:
            <{no_match_list_delimiter}> 
            [
                {{"ingredient":"<ingredient_name1>","flavor":"<flavor_name1>"}},
                {{"ingredient":"<ingredient_name2>","flavor":"<flavor_name2>"}},
                {{"ingredient":"<ingredient_name3>","flavor":"<flavor_name3>"}},
                ...
                {{"ingredient":"<ingredient_nameN>","flavor":"<flavor_nameN>"}}
            ]
            </{no_match_list_delimiter}>
    - Exhaustive list of the the permissible entities for substitutes <{full_list_delimiter}> and </{full_list_delimiter}>
        -The format for these entities is:
            <{full_list_delimiter}>
            [
                {{"ingredient":"<ingredient_name1>","flavor":"<flavor_name1>"}},
                {{"ingredient":"<ingredient_name2>","flavor":"<flavor_name2>"}},
                {{"ingredient":"<ingredient_name3>","flavor":"<flavor_name3>"}},
                ...
                {{"ingredient":"<ingredient_nameN>","flavor":"<flavor_nameN>"}}
            ]
            </{full_list_delimiter}>
    - Substitute matches that have already been identified but could be refined and/or additional substitutes could be found listed between the delimiters <{already_matched_delimeter}> and </{already_matched_delimeter}>.
        -The format for these entities is:
            <{already_matched_delimeter}>
            [
                {{"entity":"<source_entity1>", "sub":"<substitute_entityX>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
                {{"entity":"<source_entity2>", "sub":"<substitute_entityY>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
                {{"entity":"<source_entity3>", "sub":"<substitute_entity1Z>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
                ...
                {{"entity":"<source_entityN>", "sub":"<substitute_entityX>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}},
            ]
            </{already_matched_delimeter}>

    
DO NOT add any explanatory text outside of the instructions below in the specific format described.


-Steps-
- As a chef, for each of entities listed in the first section of the input file, identify all potential substitutes from the second section that would suffice entity if the entity wasn't available for a recipe.
- The entity and substitute must be *clearly related* to each other based on thier flavor or culinary use.
- For each pair of related entities, extract the following information:
    - source_entity: name of the source entity
    - substitute_entity: name of the substitute
    - relationship_rationale: explanation as to why you think substitute is a good match to the entity.
    - relationship_confidence: a numeric score between 1 and 10 indicating confidence the match.
    - Format each relationship as a an array of json objects with the following format:
        {{"entity":"<source_entity>", "sub":"<substitute_entity>", "rationale":"<relationship_rationale>", "confidence":<relationship_confidence>}}
- The top section of the file will be the entities that have yet to be matched between the delimiters: <{no_match_list_delimiter}> and </{no_match_list_delimiter}>; you MUST address these first!
- Only choose substitutes from the second section that begins are between the delimiters <{full_list_delimiter}> and </{full_list_delimiter}>.
- Do not dupilcate *explicit* combinations of entities and subs.
    -E.G.  This is invalid:
        [
            {{"entity":"lemon", "sub":"lime", "rationale":"lemon tastes like lime"}},
            {{"entity":"lemon", "sub":"lime", "rationale":"limes and lemon are sour"}}
        ]
    -E.G. This is valid however since the lemon and lime are reversed and hence not explicitly the same combination:
        [
            {{"entity":"lemon", "sub":"lime", "rationale":"lemon tastes like lime"}},
            {{"entity":"lime", "sub":"lemon", "rationale":"lime tastes like lemon"}}
        ]
- If an entity can be substituted with multipe other substititutes indicate that with multiple entries.
    -E.G. 
        [
            {{"entity":"lemon", "sub":"lime"}},
            {{"entity":"lemon", "sub":"yuzu"}},
            {{"entity":"lemon", "sub":"vinegar"}},
        ]
- Due to max tokens in output we need to call this in a loop. So limit the results to the be the top {max_results} results.
- If no entries are left in the un-matched section then proceed to refine the matches and add more substitutes.
- When finished generating the whole list or reach the token count, output the completion delimiter: {completion_delimiter}

###################
-Examples-
######################
Example 1:
entity type: ingredient
defining property: flavor
entity list:
<input>
<{no_match_list_delimiter}>
[
{{'ingredient':'lemon','flavor':'tart, citrusy'}},
{{'ingredient':'lime','flavor':'tart, citrusy'}},
{{'ingredient':'vinegar','flavor':'sour'}},
{{'ingredient':'parsley','flavor':'savory'}},
{{'ingredient':'cilantro','flavor':'citrus'}},
{{'ingredient':'oregano','flavor':'earthy'}},
{{'ingredient':'mustard','flavor':'spicy'}},
{{'ingredient':'pepper','flavor':'spicy'}},
]
</{no_match_list_delimiter}>
<{full_list_delimiter}>
[
{{'ingredient':'lemon','flavor':'tart, citrusy'}},
{{'ingredient':'oil','flavor':'N/A'}},
{{'ingredient':'butter','flavor':'buttery'}},
{{'ingredient':'lime','flavor':'tart, citrusy'}},
{{'ingredient':'vinegar','flavor':'sour'}},
{{'ingredient':'parsley','flavor':'savory'}},
{{'ingredient':'cilantro','flavor':'citrus'}},
{{'ingredient':'oregano','flavor':'earthy'}},
{{'ingredient':'mustard','flavor':'spicy'}},
{{'ingredient':'pepper','flavor':'spicy'}},
]
</{full_list_delimiter}>
<{already_matched_delimeter}>
[
{{"entity":"oil", "sub":"butter", "rationale":"both can be used for lubrication", "confidence":7}},
{{"entity":"butter", "sub":"oil", "rationale":"both can be used for lubrication", "confidence":7}},
]
</{already_matched_delimeter}>
</input>
######################
<output>
[
{{"entity":"lemon", "sub":"lime", "rationale":"both provide acid", "confidence":9}},
{{"entity":"lemon", "sub":"vinegar", "rationale":"both provide acid ", "confidence":8}},
{{"entity":"vinegar", "sub":"lemon", "rationale":"both provide acid", "confidence":8}},
{{"entity":"vinegar", "sub":"lime", "rationale":"both provide acid", "confidence":8}},
{{"entity":"lime", "sub":"lemon", "rationale":"both provide acid ", "confidence":8}},
{{"entity":"lime", "sub":"vinegar", "rationale":"both provide acid ", "confidence":8}},
{{"entity":"parsley", "sub":"cilantro", "rationale":"cilantro and parsley are herbs from the same family but cilantro has a stronger distinct flavor", "confidence":5}},
{{"entity":"parsley", "sub":"oregano", "rationale":"oregano and parsley are herbs from different families but both are common in italian cooking", "confidence":5}},
{{"entity":"pepper", "sub":"mustard",  "rationale":"both supply heat but the flavors are distinct", "confidence":5}},
]
</output>
"""

CONTINUE_PROMPT = """MANY entities and substitutes were missed in the last extraction. 
Tackle the entities listed in the first section that is between the <{no_match_list_delimiter}> delimiters first.
Only choose substititutes from the section between the <{full_list_delimiter}> delimiters.
If there entity list in the <{no_match_list_delimiter}> section is empty then move on to identify additional substitutes that are not yet listed in the <{already_matched_delimeter}> section.
Entities and substitutes are only valid if they exist in the  <{full_list_delimiter}> section.
Do NOT extract the entities from the examples sections. 
Do not add any explanatory text outside of the instructions you were given as the OUTPUT.
Due to max tokens in output we need to call this in a loop. So limit the results to the top {max_results} remaining results; you will find more matches in another loop.
Again only return maximum of {max_results} relationships! Do not exceed  {max_results} rows returned!
And remember to ALWAYS end your response with the completion delimiter: {completion_delimiter}\n"""

CHECK_LOOP_PROMPT = "It appears some entities and substitutes may have still been missed. For instance we need at least one result per entity.  Answer YES | NO if there are still entities or relationships that need to be added. ONLY answer with 'YES' or 'NO' and nothing else!\n"



TARGET_INGREDIENTS_MATCH_RATIO = 10
MAX_LOOP_COUNT = 200
PROMPT_BATCH_SIZE = 200


NO_MATCH_LIST_DELIMITER = "NO_MATCHES"
FULL_LIST_DELIMITER = "ONLY_PERMISSIBLE_ENTITIES"
ALREADY_MATCHED_DELIMETER = "IDENTIFIED_MATCHES"



    

def get_matches(
    gemini_processor: GeminiHelper,
    prompt_messages,file_attachment,loop_counter=0):
    print(f"\nProcessing matching loop try {loop_counter}") 

    if loop_counter>MAX_LOOP_COUNT:
        print("Max loop count reached")
        return


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


def process_ingredient_matching(ingredient_list,ingredient_match_list=[],loop_counter=0,debug_file=None):
    
    
    
    target_match_count = len(ingredient_list) * TARGET_INGREDIENTS_MATCH_RATIO
    
    ingredient_unmatched_list = RefDataHelper.find_unmatched_items( 
                ingredient_list,ingredient_match_list,"ingredient","entity"
            )
    

    print(f"Loop {loop_counter} of {MAX_LOOP_COUNT} loops | substitutes matched: {len(ingredient_match_list)} of {target_match_count} target | unmatched: {len(ingredient_unmatched_list)} of {len(ingredient_list)} ingredients")
    
    
    init_messages = []

    init_prompt_text = ENTITY_REPLACEMENT_PROMPT.format(
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER,
        max_results = PROMPT_BATCH_SIZE,
        no_match_list_delimiter = NO_MATCH_LIST_DELIMITER,
        full_list_delimiter = FULL_LIST_DELIMITER,
        already_matched_delimeter = ALREADY_MATCHED_DELIMETER
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

    
    working_ingredient_matches_file = out_folder + f"/working_ingredients_match_{loop_counter}.txt"
    messages_to_use = []
    if(loop_counter == 0):
        initial_ingredient_file = out_folder + "/initial_ingredient_match.txt"
        RefDataHelper.write_enriched_ingredients_to_file(ingredient_list,initial_ingredient_file)


        RefDataHelper.write_ingredients_and_matches_to_file(ingredient_list,ingredient_match_list,ingredient_unmatched_list,NO_MATCH_LIST_DELIMITER,FULL_LIST_DELIMITER,ALREADY_MATCHED_DELIMETER,working_ingredient_matches_file)
        messages_to_use = init_messages
    else:
        messages_to_use = continue_prompt_messages



    new_matches_list = get_matches(
        gemini_processor,messages_to_use,working_ingredient_matches_file
    )

    #append new matches or replace them in the new list where both entity and sub match
    ingredient_match_list = RefDataHelper.merge_dicts_over_two_keys(
        ingredient_match_list,new_matches_list,"entity","sub"
    )
    ingredient_unmatched_list = RefDataHelper.find_unmatched_items( 
                ingredient_list,ingredient_match_list,"ingredient","entity"
            )
    #ingredient_match_list.extend(new_matches_list)

    loop_counter += 1
    working_ingredient_matches_file = out_folder + f"/working_ingredients_match_{loop_counter}.txt"
    RefDataHelper.write_ingredients_and_matches_to_file(ingredient_list,ingredient_match_list,ingredient_unmatched_list,NO_MATCH_LIST_DELIMITER,FULL_LIST_DELIMITER,ALREADY_MATCHED_DELIMETER,working_ingredient_matches_file)
    continue_loop = check_are_matches_complete(gemini_processor,check_are_matches_complete_messages,working_ingredient_matches_file)




    if continue_loop and loop_counter<MAX_LOOP_COUNT and len(ingredient_match_list)<target_match_count:
        return process_ingredient_matching(ingredient_list,ingredient_match_list,loop_counter,debug_file)
    else:
        print(
            f""" 
            Step 0.2 -- extracted cleaned ingredients    
            Complete 
            {len(ingredient_list)} ingredients
            {ingredient_list[0]["ingredient"]} - {ingredient_list[-1]["ingredient"]}
            {len(ingredient_match_list)} matches
            """)
        return ingredient_match_list
       


    



async def main():

    
    args_loader.print()

    debug_file = out_folder + "/gemini_debug.txt"
    enriched_ingredient_list = RefDataHelper.convert_enriched_ingredient_file_to_list(recipe_constants.EXTRACTED_INGREDIENTS_FILE)
    matched_list = process_ingredient_matching(enriched_ingredient_list,debug_file=debug_file)
    RefDataHelper.write_matched_ingredients_to_file(matched_list,recipe_constants.MATCHED_INGREDIENTS_FILE)


        

if __name__ == "__main__":
    asyncio.run(main())


    