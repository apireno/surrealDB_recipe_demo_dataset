import asyncio
import time
import math
import ast
import os
import pandas as pd
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader,GeminiConstants
from gemini import GeminiHelper

out_folder = THIS_FOLDER + "/logging/ing_extract_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
data_folder = THIS_FOLDER + "/data"
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
gemini_constants = GeminiConstants()
args_loader = RecipeArgsLoader("STEP 0.1 - LLM Extract ingredients from data",db_constants,embed_constants,recipe_constants,gemini_constants)
args_loader.LoadArgs()


GEMINI_INGREDIENT_STEMMING_PROMPT = """
You are a data cleanser.
Please simplify the following list of ingredients in the attached file.
The goal is to have a much shorter list of ingredients that are easier to search.
To acheive this please target reducing the number of ingredients by a ratio of {target_ingredient_reduction_ratio}
The name of the ingredient should be reduced to its stem for use in full-text search. 
This will help ensure that searches for any variations of a word will still return relevant results.
If there are suprflous adjectives in the item then remove the adjective and only return the noun.
Do not return words that are not ingredients after reduction. 
For example if you seperate French bread into French and bread, only return bread.
If a full text search would pull the value when searching with another item on the list consider it a duplicate and remove it and only retain the stemmed version.
Make sure that the list does not include duplicates due to tense or pluralization. 
E.G. don't return both egg and eggs, only return egg.
E.G. don't return both bake and baking, only return "baking soda" if that was the ingredient.
don't return any plurals!
don't return any plurals!
don't return any plurals!
don't return any plurals!
don't return any plurals!
Ssimplify the words to eliminate redundant puntuation.
E.G. don't return both 7up and 7-up, only return 7up.
Remove overyly specific ingredients.
Remove any items that are not edible. 
For instance remove tools or adjectives that have lost thier meaning as ingredients due to stemming.
E.G. cantaloupe sherbet should be reduced to sherbert and cantaloupe as two seperate items. 
E.G. bean curd skin is too specific and should be reduced to bean curd.
E.G. berry bread is too specific and should be reduced to bread.
E.G. candy bars with almonds and candy bars should be reduced to candy bar.
E.G. canned whole kernel corn should be reduced to corn.
E.G. filet mignon steak should be reduced to filet mignon.
Return the results in a array of lowercase strings.
ONLY return the array.
The array of objects should have this format:
["lemon","lime","sugar"]
Do not add explanatory text or object names.
When finished, output the completion delimiter: {completion_delimiter}
<example>
    <input_from_attachment> 
        Lemon
        lemons
        lime
        lime juice
        sugar
        granulated sugar
        olive oil
        extra virgin olive oil
        baking soda
        baking powder
    </input_from_attachment>
    <output>
        ["lemon","lime","sugar""olive oil","baking soda","baking powder"]
    </output>
    {completion_delimiter}
</example>
"""

GEMINI_INGREDIENT_FLAVOR_PROMPT = """
You are a data cleanser.
Please enrich the of ingredients in the attached file by returning thier flavors where the flavor is missing.
Also correct the flavor to more closely align with the other entities.
Choose the word for the flavor that is most commonly used in the culinary world.
For instance: lemon, lime, vinegar, and orange should all have the flavor "sour", rather than a mix of "sour", "tart" and "acid".
You can apply more than one flavor to a single ingredient.
For instance orange flavor is both "acid" and "sweet" so return "acid sweet" for orange.
If an ingredient doesn't have a flavor per se return "N/A" as the flavor.


The input file has the list of ingredients in the format of:
[
    {{"ingredient":`<ingredient_name1>`,"flavor":`<flavor_name1>`}},
    {{"ingredient":`<ingredient_name2>`,"flavor":`<flavor_name2>`}},
    {{"ingredient":`<ingredient_name3>`,"flavor":`<flavor_name3>`}},
    ...
    {{"ingredient":`<ingredient_nameN>`,"flavor":`<flavor_nameN>`}}
]

Only return the flavor of the ingredients that are explictly listed.
Return the results in a json array of objects and only return the array.
The array of objects should have the same format as the input file, here is an example:
[{{"ingredient":"lemon","flavor":"adid"}},{{"ingredient":"sugar","flavor":"sweet"}},{{"ingredient":"orange","flavor":"acid sweet"}}]
Do not add explanatory text or object names.
When finished, output the completion delimiter: {completion_delimiter}
<example>
    <input_from_attachment> 
        [
        {{"ingredient":"lemon","flavor":"adid"}},
        {{"ingredient":"lime"}},
        {{"ingredient":"sugar","flavor":"sweet"}}
        ]
    </input_from_attachment>
    <output>
        [{{"ingredient":"lemon","flavor":"adid"}},{{"ingredient":"lime","flavor":"adid"}},{{"ingredient":"sugar","flavor":"sweet"}}]
    </output>
    {completion_delimiter}
</example>
"""

TARGET_INGREDIENTS_LIST_SIZE = 1200
MAX_LOOP_COUNT = 5

def count_items_with_value(array_of_dicts, key, values):
    count = 0
    for dict_item in array_of_dicts:
        for value in values:
            if key in dict_item and dict_item[key] == value:
                count += 1
    return count


def write_enriched_ingredients_to_file(ingredient_list,ingredient_file):
    with open(ingredient_file, "w") as f:
        f.write("[\n")
        for item in ingredient_list:
            f.write(f"{{'ingredient':'{item["ingredient"].replace("'"," ")}','flavor':'{item["flavor"].replace("'"," ")}'}},\n")
        f.write("]")
        
def process_ingredient_enrichment_for_chunk(ingredient_list_len,gemini_processor,chunk,temp_ingredient_file,chunk_i,loop_counter=0):
    # Process the chunk here


    if loop_counter>MAX_LOOP_COUNT:
        print("Max loop count reached")
        return
    

    print(f"\nProcessing enrich chunk starting at index loop try {loop_counter} chunk {chunk_i}/{ingredient_list_len}: {chunk[0]["ingredient"]}-{chunk[-1]["ingredient"]}") 
    

    #this is the message prompt
    messages = []
    prompt_text = GEMINI_INGREDIENT_FLAVOR_PROMPT.format(completion_delimiter=gemini_constants.COMPLETION_DELEMITER)
    messages.append( 
                {"role": "user", "parts": [{"text": prompt_text}]}
    )

    #generate chuncked list of ingredients

    write_enriched_ingredients_to_file(chunk,temp_ingredient_file)

    attached_file = gemini_processor.attach_file(temp_ingredient_file)
    
    #generate a response from the LLM
    ai_response_text = gemini_processor.generate_content_until_complete(messages,attached_file)
    try:    
        item_list =  ast.literal_eval(ai_response_text)
        for item in item_list:
            item['ingredient'] = item['ingredient'].strip()
            item['flavor'] = item['flavor'].strip()
        return item_list
    except Exception as e:
        loop_counter += 1
        print("bad json")
        print(e)
        print(ai_response_text)
        return process_ingredient_enrichment_for_chunk(ingredient_list_len,gemini_processor,chunk,temp_ingredient_file,chunk_i,loop_counter=loop_counter)



def process_ingredient_enrichment(ingredient_list,loop_counter=0,debug_file=None):

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    num_not_processed = count_items_with_value(
        ingredient_list, "flavor", ["N/A", "", None])
    
    if loop_counter>MAX_LOOP_COUNT:

        print(
            f""" 
            Step 2a -- extracted cleaned ingredients    
            Complete 
            {len(ingredient_list)} ingredients
            {ingredient_list[0]["ingredient"]} - {ingredient_list[-1]["ingredient"]}
            {num_not_processed} N/A or null of {len(ingredient_list)} ingredients
            """)
        return ingredient_list
    else:
        print(f"Loop {loop_counter} of {MAX_LOOP_COUNT} enrichments {num_not_processed} N/A or null of {len(ingredient_list)} ingredients")
    
    temp_ingredient_file = out_folder + "/temp_ingredients_enrich.txt"
    initial_ingredient_file = out_folder + "/initial_ingredients_enrich.txt"

    if(loop_counter == 0):
        write_enriched_ingredients_to_file(ingredient_list,initial_ingredient_file)

    working_ingredient_file = out_folder + f"/working_ingredients_enrich_{loop_counter}.txt"
    write_enriched_ingredients_to_file(ingredient_list,working_ingredient_file)
    

    #to limit the tokens per call we will process 500 ingredients at a time
    chunk_size = math.floor( TARGET_INGREDIENTS_LIST_SIZE/10 )
    gemini_processor = GeminiHelper(gemini_constants,debug_file=debug_file)

    enriched_ingredients = []
    for i in range(0, len(ingredient_list), chunk_size): 
        chunk = ingredient_list[i: i + chunk_size]
        item_list = process_ingredient_enrichment_for_chunk(len(ingredient_list),gemini_processor,chunk,temp_ingredient_file,i)
        if len (item_list) > 0:
            enriched_ingredients.extend(item_list)
        else:
            print("too many loops on retries")
            return []

    if(len(ingredient_list)>len(enriched_ingredients)):
        enriched_ingredients = ingredient_list
    else:
        enriched_ingredients = sorted(enriched_ingredients, key=lambda x: x['ingredient'])

    write_enriched_ingredients_to_file(enriched_ingredients,working_ingredient_file)


    

    loop_counter += 1
    return process_ingredient_enrichment(enriched_ingredients,loop_counter=loop_counter,initial_ingredient_file=initial_ingredient_file,debug_file=debug_file)  




def process_ingredient_reduction(ingredient_list,loop_counter=0,debug_file=None):


    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    temp_ingredient_file = out_folder + "/temp_ingredients.txt"
    initial_ingredient_file = out_folder + "/initial_ingredients.txt"
    working_ingredient_file = out_folder + f"/working_ingredients{loop_counter}.txt"

    if(loop_counter == 0):
        with open(initial_ingredient_file, "w") as f:
            f.write("\n".join(ingredient_list))

    with open(working_ingredient_file, "w") as f:
        f.write("\n".join(ingredient_list))


    #to limit the tokens per call we will process in batches of chucnk_size
    chunk_size = TARGET_INGREDIENTS_LIST_SIZE
    gemini_processor = GeminiHelper(gemini_constants,debug_file=debug_file)

    target_ingredient_reduction_ratio = TARGET_INGREDIENTS_LIST_SIZE/len(ingredient_list) 

    if loop_counter<MAX_LOOP_COUNT and len(ingredient_list) > TARGET_INGREDIENTS_LIST_SIZE:
        ai_response_texts = []
        for i in range(0, len(ingredient_list), chunk_size): 
            chunk = ingredient_list[i: i + chunk_size]
            # Process the chunk here
            print(f"\nProcessing chunk starting at index {i}/{len(ingredient_list)}: {chunk[0]}-{chunk[-1]}") 
            

            #this is the message prompt
            messages = []
            prompt_text = GEMINI_INGREDIENT_STEMMING_PROMPT.format(completion_delimiter=gemini_constants.COMPLETION_DELEMITER,target_ingredient_reduction_ratio=target_ingredient_reduction_ratio)
            messages.append( 
                        {"role": "user", "parts": [{"text": prompt_text}]}
            )

            #generate chuncked list of ingredients
            with open(temp_ingredient_file, "w") as f:
                f.write("\n".join(chunk))

            attached_file = gemini_processor.attach_file(temp_ingredient_file)
            
            #generate a response from the LLM
            ai_response_text = gemini_processor.generate_content_until_complete(messages,attached_file)

            #append the ingredient list to the list of responses
            ai_response_texts.append(ai_response_text)



        #iterate through the ai responses and append the ingredients to the working ingredient list
        truncated_ingredients = []
        for item in ai_response_texts:
            item_list =  ast.literal_eval(item)
            item_list = [s.strip().lower() for s in item_list]
            truncated_ingredients.extend(item_list)
        truncated_ingredients = list(set(truncated_ingredients))
        truncated_ingredients.sort()
        with open(working_ingredient_file, "w") as f:
            f.write("\n".join(truncated_ingredients))

        
        print(f"Loop {loop_counter} -- {len(truncated_ingredients)} ingredients")

        loop_counter += 1
        return process_ingredient_reduction(truncated_ingredients,
                            loop_counter=loop_counter,
                            debug_file=debug_file)

    else:

        
        print(
            """ 

            
            Step 0.1 -- extracted cleaned ingredients    
            Complete 
            """)
        return ingredient_list



async def main():

    
    args_loader.print()
    
    use_original_file = True
    if use_original_file:
        recipe_df = pd.read_csv(recipe_constants.RECIPE_FILE)
        indredient_df = recipe_df["ingredients"].apply(lambda x: ast.literal_eval(x)).explode().unique()
        indredient_df.sort()
        ingredient_list = indredient_df.tolist()
    else:
        #working_file = data_folder + "/working_ingredients.txt"
        with open(recipe_constants.EXTRACTED_INGREDIENTS_FILE, 'r') as f:
            #ingredient_list = f.read().splitlines()
            enriched_ingredient_list =  ast.literal_eval(f.read())
            ingredient_list = [item["ingredient"] for item in enriched_ingredient_list]
       
       
        
    


    debug_file = out_folder + "/gemini_debug.txt"
    truncated_ingredient_list = process_ingredient_reduction(ingredient_list,debug_file=debug_file)
    
    enriched_ingredent_list = []
    for item in truncated_ingredient_list:
        enriched_ingredent_list.append({"ingredient":item,"flavor":""})

    enriched_ingredent_list = process_ingredient_enrichment(enriched_ingredent_list,debug_file=debug_file)


    write_enriched_ingredients_to_file(enriched_ingredent_list,recipe_constants.EXTRACTED_INGREDIENTS_FILE)

    
        

if __name__ == "__main__":
    asyncio.run(main())


    