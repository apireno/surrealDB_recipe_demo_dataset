import asyncio
import time
import ast
import os
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader,GeminiConstants
from gemini import GeminiHelper

out_folder = THIS_FOLDER + "/logging/ing_sim_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
data_folder = THIS_FOLDER + "/data"
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
gemini_constants = GeminiConstants()
args_loader = RecipeArgsLoader("STEP 0.2 - LLM Extract ingredients similarities",db_constants,embed_constants,recipe_constants,gemini_constants)
args_loader.LoadArgs()


ENTITY_REPLACEMENT_PROMPT = """
-Goal-
You are a data processor and researcher who excels at finding connections in data.
Given the list of entities contained in the attached file, reason out how they can be replaced with one another for substitution in {parent_entity}.
Also if you notice that any of the entities can be created by combining other entities in the list indicate them as well.

DO NOT add any explanatory text outside of the instructions below in the specific format described.


-Steps-
1. For each of entities listed, identify all replacement entities (source_entity, target_entity) that are *clearly related* to each other based on thier {property_name}.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity
- target_entity: name of the target entity
- {property_name}: the shared {property_name} in a few words
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
-Format each relationship as a an array of json objects with the following format:
 {{"in":"{entity_type}:`<source_entity>`", "out":"{entity_type}:`<target_entity>`", "{property_name}":"<property_value>", "description":"<relationship_description>", "strength":<relationship_strength>}}
2. We want to generate at least one replacement per entity so should have at least {entity_list_count} results.
3. Do not dupilcate combinations of in and out's. So if you have already identified the relationship between in:Lemon, out:Lime do not list it again. However it is OK to list Lemon->Lime and Lime-Lemon.
3. Due to max tokens in output we need to call this in a loop. So limit the results to the be the top {max_results} results.
4. When finished generating the whole list or reach the token count, output the completion delimiter: {completion_delimiter}

Additional considerations: Make sure to identify all cross-relationships between the entities. Only use objects that are explicily enumerated in the object list. Take special note of any hierarchal representations within the relationships. When in doubt be generous and add extra relationships but indicate the weakness with the strength score.


Additional considerations: 
attempt to indentify at least one replacement for every entity. Take special note of any hierarchal representations within the relationships. When in doubt be generous and add extra relationships but indicate the weakness with the strength score.

 
###################
-Examples-
######################
Example 1:
entity type: ingredient
defining property: flavor
entity list:
<input>
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
{exisiting_relations_delimiter}
[
{{"in":"ingredient:`oil`", "out":"ingredient:`butter`", "description":"both can be used for lubrication", "strength":7}},
]
</input>
######################
<output>
[
{{"in":"ingredient:`lemon`", "out":"ingredient:`lime`", "description":"both provide acid", "strength":9}},
{{"in":"ingredient:`lemon`", "out":"ingredient:`vinegar`", "description":"both provide acid but lemon is less so", "strength":8}},
{{"in":"ingredient:`parsley`", "out":"ingredient:`cilantro`", "description":"cilantro and parsley are herbs from the same family but cilantro has a stronger distinct flavor", "strength":5}},
{{"in":"ingredient:`parsley`", "out":"ingredient:`oregano`", "description":"oregano and parsley are herbs from different families but both are common in italian cooking", "strength":5}},
{{"in":"ingredient:`pepper`", "out":"ingredient:`mustard`",  "description":"both supply heat but the flavors are distinct", "strength":5}},
]
</output>
######################
-Real Data-
######################
entity type: {entity_type}
defining property: {property_name}
######################
Output:"""

CONTINUE_PROMPT = """MANY entities and relationships were missed in the last extraction. Try to identify relationships that may be weaker or were not apparent at your first attempt. Make sure to have at least one relationship for each entity even if it is to itself. AND make sure to add any entities mentioned in relationships. Remember to ONLY emit entities that match any of the previously extracted types and do NOT extract the entities from the examples sections. Add them below using the same format. Do not add any explanatory text outside of the instructions you were given as the OUTPUT.
Due to max tokens in output we need to call this in a loop. So limit the results to the top {max_results} remaining results.
Again only return maximum of {max_results} relationships! Do not exceed  {max_results} rows returned!
And remember to ALWAYS end your response with the completion delimiter: {completion_delimiter}\n"""

CHECK_LOOP_PROMPT = "It appears some entities and relationships may have still been missed. For instance we need at least one result per entity.  Answer YES | NO if there are still entities or relationships that need to be added. ONLY answer with 'YES' or 'NO' and nothing else!\n"



TARGET_INGREDIENTS_MATCH_RATIO = 5
MAX_LOOP_COUNT = 100
PROMPT_BATCH_SIZE = 200
EXISITING_RELATIONS_DELIMITER = "# RELATIONS ALREADY CREATED:"

def rsq(s):
    return s.replace("'", "")

def write_enriched_ingredients_to_file(ingredient_list,ingredient_file):
    with open(ingredient_file, "w") as f:
        f.write("[\n")
        for item in ingredient_list:
            f.write(f"{{'ingredient':'{item["ingredient"].replace("'"," ")}','flavor':'{item["flavor"].replace("'"," ")}'}},\n")
        f.write("]")
def write_ingredients_and_matches_to_file(ingredient_list,ingredient_match_list,ingredient_file):
    write_enriched_ingredients_to_file(ingredient_list,ingredient_file)
    with open(ingredient_file, "a") as f:
        f.write(f"{EXISITING_RELATIONS_DELIMITER}\n") 
    write_matched_ingredients_to_file(ingredient_match_list,ingredient_file, file_mode="a")



def write_matched_ingredients_to_file(ingredient_match_list,ingredient_file,file_mode="w"):
   
   
    with open(ingredient_file, file_mode) as f:
        f.write("[\n")
        for item in ingredient_match_list:           
            f.write(f"{{'in':'{rsq(item["in"])}','out':'{rsq(item["out"])}','description':'{rsq(item["description"])}','strength':'{item["strength"]}'}},\n")
        f.write("]")
    

def get_matches(
    gemini_processor: GeminiHelper,
    prompt_messages,file_attachment,loop_counter=0):
    print(f"\nProcessing matching loop try {loop_counter}") 

    if loop_counter>MAX_LOOP_COUNT:
        print("Max loop count reached")
        return


    attached_file = gemini_processor.attach_file(file_attachment)
     #generate a response from the LLM
    ai_response_text = gemini_processor.generate_content_until_complete(prompt_messages,attached_file)
    try:    
        item_list =  ast.literal_eval(ai_response_text)
        
        # for item in item_list:
        #     item['ingredient'] = item['ingredient'].strip()
        #     item['flavor'] = item['flavor'].strip()
        return item_list
    except Exception as e:
        loop_counter += 1
        print("bad json")
        print(e)
        print(ai_response_text)
        return get_matches( gemini_processor,  prompt_messages,file_attachment,loop_counter)


def check_are_matches_complete(
    gemini_processor,
    prompt_messages,file_attachment):

    attached_file = gemini_processor.attach_file(file_attachment)
    ai_response = gemini_processor.generate_content(prompt_messages,attached_file)
    return (ai_response == "YES")


def process_ingredient_matching(ingredient_list,ingredient_match_list=[],loop_counter=0,debug_file=None):
    
    
    print(f"Loop {loop_counter} of {MAX_LOOP_COUNT} enrichments  {len(ingredient_match_list)} matches of {len(ingredient_list)} ingredients")
    
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    if(loop_counter == 0):
        initial_ingredient_file = out_folder + "/initial_ingredient_match.txt"
        write_enriched_ingredients_to_file(ingredient_list,initial_ingredient_file)

    init_messages = []
    init_prompt_text = ENTITY_REPLACEMENT_PROMPT.format(
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER,
        parent_entity = "recipe",
        property_name = "flavor",
        entity_type = "ingredient",
        max_results = PROMPT_BATCH_SIZE,
        exisiting_relations_delimiter = EXISITING_RELATIONS_DELIMITER,
        entity_list_count = len(ingredient_list) * TARGET_INGREDIENTS_MATCH_RATIO
        )
    init_messages.append( 
                {"role": "user", "parts": [{"text": init_prompt_text}]}
    )

    check_are_matches_complete_messages = init_messages.copy()
    continue_prompt_messages = init_messages.copy()





    check_are_matches_complete_prompt_text = CHECK_LOOP_PROMPT.format(
        max_results = PROMPT_BATCH_SIZE,
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER
        )
    
    check_are_matches_complete_messages.append( 
                    {"role": "user", "parts": [{"text": check_are_matches_complete_prompt_text}]}
        )
    

    continue_prompt_prompt_text = CONTINUE_PROMPT.format(  
        max_results = PROMPT_BATCH_SIZE,
        completion_delimiter=gemini_constants.COMPLETION_DELEMITER
        )

    continue_prompt_messages.append( 
                    {"role": "user", "parts": [{"text": continue_prompt_prompt_text}]}
        )

    
   
    gemini_processor = GeminiHelper(gemini_constants,debug_file=debug_file)

    
    working_ingredient_matches_file = out_folder + f"/working_ingredients_match_{loop_counter}.txt"
    messages_to_use = []
    if(loop_counter == 0):
        initial_ingredient_file = out_folder + "/initial_ingredient_match.txt"
        write_enriched_ingredients_to_file(ingredient_list,initial_ingredient_file)
        write_ingredients_and_matches_to_file(ingredient_list,ingredient_match_list,working_ingredient_matches_file)
        messages_to_use = init_messages
    else:
        messages_to_use = continue_prompt_messages



    new_matches_list = get_matches(
        gemini_processor,messages_to_use,working_ingredient_matches_file
    )
    ingredient_match_list.extend(new_matches_list)

    loop_counter += 1
    working_ingredient_matches_file = out_folder + f"/working_ingredients_match_{loop_counter}.txt"
    write_ingredients_and_matches_to_file(ingredient_list,ingredient_match_list,working_ingredient_matches_file)
    continue_loop = check_are_matches_complete(gemini_processor,check_are_matches_complete_messages,working_ingredient_matches_file)




    if continue_loop and loop_counter<MAX_LOOP_COUNT and len(ingredient_match_list)<TARGET_INGREDIENTS_MATCH_RATIO*len(ingredient_list):
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

    with open(recipe_constants.EXTRACTED_INGREDIENTS_FILE, 'r') as f:
            #ingredient_list = f.read().splitlines()
            enriched_ingredient_list =  ast.literal_eval(f.read())


    debug_file = out_folder + "/gemini_debug.txt"
    matched_list = process_ingredient_matching(enriched_ingredient_list,debug_file=debug_file)
    
    write_matched_ingredients_to_file(matched_list,recipe_constants.MATCHED_INGREDIENTS_FILE)


        

if __name__ == "__main__":
    asyncio.run(main())


    