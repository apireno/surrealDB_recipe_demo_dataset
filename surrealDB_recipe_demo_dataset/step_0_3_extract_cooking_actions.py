import asyncio
import time
import ast
import os
import pandas as pd
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader,GeminiConstants,DATA_FOLDER
from gemini import GeminiHelper
from extraction_ref_data_helpers import RefDataHelper
from helpers import Helpers

out_folder = THIS_FOLDER + "/logging/act_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
gemini_constants = GeminiConstants()
args_loader = RecipeArgsLoader("STEP 0.3 - LLM Extract cooking actions from data",db_constants,embed_constants,recipe_constants,gemini_constants)
args_loader.LoadArgs()

Helpers.ensure_folders([out_folder,DATA_FOLDER])



GEMINI_ACTION_STEMMING_PROMPT = """
You are a linguist and professor of culinary arts.
Please extract and simplify all the culinary actions (IE verbs) from the attached corpus.
You will be going in a loop and examining portions of the corpus with the already extracted actions listed above the new text.
The list of already parsed actions will be preceded with the delimiter {new_text_delimiter}.
The new text to be parsed will be preceded with the delimiter {existing_actions_delimiter}.
The goal is to have a much shorter list of actions that are easier to search.
To acheive this please target generating a total number of actions to a target of {target_action_list_size}.
The name of the action should be reduced to its stem for use in full-text search. 
This will help ensure that searches for any variations of a word will still return relevant results.
Do not return words that are not verbs. 
If a full text search would pull the value when searching with another item on the list consider it a duplicate and remove it and only retain the stemmed version.
Make sure that the list does not include duplicates due to conjucation. 
E.G. don't return cook,cooking,cooks,and cooked: only return "cook"
I repeat ONLY return the stem of the verb and NO alternate conjucations!
Remove overyly specific actions.
Remove any items that are not realted to the culinary arts.
Return the results in a array of lowercase strings.
Only list an action once. Do not return it again.
ONLY return the array.
The array of objects should have this format:
["cook","chop","saute"]
Do not add explanatory text or object names.
When finished, output the completion delimiter: {completion_delimiter}
<example>
    <input_from_attachment> 
        {existing_actions_delimiter}
        [
            "cook",
            "drain"
        ]
        {new_text_delimiter}
        in a medium skillet , cook bacon over medium heat until crisp,
		using a slotted spoon , remove bacon from skillet , and drain on paper towels,
		drain bacon grease from skillet,
		add 14 cup olive oil and marmalade to skillet,
		cook over medium heat , stirring with a wooden spoon until marmalade is melted , loosening brown bits from bottom of skillet while stirring,
		remove from heat , and stir in vinegar,
		set aside,
		preheat oven to 425,
		line a rimmed baking sheet with aluminum foil,
		spread asparagus in a single layer on prepared baking sheet,
		drizzle asparagus with remaining 1 12 tablespoons olive oil , tossing gently to coat,
		sprinkle evenly with salt,
		bake until asparagus is barely tender , 5 to 10 minutes,
		place asparagus on a large platter , or divide evenly among 6 salad plates,
		stir strawberries into marmalade mixture , tossing to coat,
		spoon strawberry mixture evenly over asparagus,
		top evenly with bacon , feta cheese , and pepper,
		serve immediately
    </input_from_attachment>
    <output>
        ["stir","preheat","spread","drizzle","sprinkle","divide","toss","spoon","top","serve","bake"]{completion_delimiter}
    </output>

    <explainations>
        We didn't return "cook" or "drain" as they were already known.
        Verbs like "remove" and "using" aren't cullinary actions so we didn't include them.
        "heat" was used as an adjective so we didn't include it.
        We retuced the words like "stirring" to "stir" and "tossing" to "toss" to eliminate tenses and conjugation.
    </explainations>
</example>
"""


GEMINI_ACTION_REFINE = """
    You are a linguist and professor of culinary arts.

    Your first task is to take this comprehensive list of culinary actions that your students provided and add the techniques and terminology they needed.
    This list is in the attached file.
    Your second task is to lemmatize the list to ensure that the list of culinary actions is reduced to the verb root.

    This means I don't want any variations that arise due to tense (past, present, future), mood (indicative, subjunctive, imperative), voice (active, passive), person (first, second, third), or number (singular, plural).

    For example, if the text contains 'running', 'ran', or 'runs', I want the LLM to return only 'run'. 
    Similarly, for 'eats', 'ate', 'eaten', I only want 'eat'.

    Essentially, I need you to strip away any suffixes or prefixes that change the verb from its most basic form. Can you help me achieve this?"

    The input text will be a JSON array of strings. 

    Output another JSON array of strings followed by this delimeter  {completion_delimiter}.

    So in this order:
    Step 1:
        As your chef persona, add all the culinary terminology for cooking actions that are missing from the input list.
    Step 2:
        As a linguist reduce the total list returned to the proper lemmas in a JSON array.

    
    <example>
        <input> 
            [
                "cook",
                "cooked",
                "cooks",
                "cooking",
                "drain",
                "drained",
                "drainer"
            ]
        </input>
        <output>
            ["cook","drain","spatchock","sous vide"]{completion_delimiter}
        </output>

        <explainations>
            You added missing techniques to the list of "spatchock","sous vide" based on your chef's knowlege.
            Cook and drain had too many conjucations so you only returned the lemmas due to your linguistic knowledge.
        </explainations>



"""



MAX_LOOP_COUNT = 10
PROMPT_BATCH_SIZE = 100
NEW_TEXT_DELIMITER = "# Text to parse:\n"
EXISTING_ACTIONS_DELIMITER = "Already parsed actions:\n"
TARGET_ACTION_LIST_SIZE = 1000






def process_action_reduction(action_list,loop_counter=0,debug_file=None):



    print(f"\nProcessing action reduction loop {loop_counter}/{MAX_LOOP_COUNT} acts {len(action_list)}") 


    initial_action_file = out_folder + "/initial_actions.txt"
    working_action_file = out_folder + f"/working_actions{loop_counter}.txt"

    if(loop_counter == 0):
        RefDataHelper.write_list_to_file(action_list,initial_action_file)

    RefDataHelper.write_list_to_file(action_list,working_action_file)

    gemini_processor = GeminiHelper(gemini_constants,debug_file=debug_file)

    if loop_counter<MAX_LOOP_COUNT:
        prompt_text = GEMINI_ACTION_REFINE.format(
            completion_delimiter=gemini_constants.COMPLETION_DELEMITER,
        )
        messages = []
        messages.append( 
                    {"role": "user", "parts": [{"text": prompt_text}]}
        )
        attached_file = gemini_processor.attach_file(working_action_file)

        action_list = gemini_processor.generate_content_until_complete_with_post_process_function(
            RefDataHelper.convert_simple_array_text_to_unique_sorted_list,messages,attached_file)
        
        loop_counter += 1
        return process_action_reduction(action_list,loop_counter,debug_file=debug_file)
    else:
        print(
            """ 

            
            Step 0.3 -- refine actions    
            Complete 
            """)
        return action_list


def process_actions_extraction(step_list,action_list = [],debug_file=None):



    temp_action_file = out_folder + "/temp_steps.txt"
    initial_steps_file = out_folder + "/initial_steps_data.txt"
    working_action_file = out_folder + f"/init_action_extracts.txt"

    RefDataHelper.write_list_as_blurb_to_file(step_list,initial_steps_file)

    
    #to limit the tokens per call we will process in batches of chucnk_size
    
    gemini_processor = GeminiHelper(gemini_constants,debug_file=debug_file)

    for i in range(0, len(step_list), PROMPT_BATCH_SIZE): 
        chunk = step_list[i: i + PROMPT_BATCH_SIZE]
        # Process the chunk here
        print(f"\nProcessing chunk starting at index {i}-{i+PROMPT_BATCH_SIZE}/{len(step_list)} acts {len(action_list)}") 
        
        #this is the message prompt
        messages = []
        prompt_text = GEMINI_ACTION_STEMMING_PROMPT.format(
            completion_delimiter=gemini_constants.COMPLETION_DELEMITER,
            new_text_delimiter=NEW_TEXT_DELIMITER,
            existing_actions_delimiter=EXISTING_ACTIONS_DELIMITER,
            target_action_list_size=TARGET_ACTION_LIST_SIZE
            )
        messages.append( 
                    {"role": "user", "parts": [{"text": prompt_text}]}
        )
        RefDataHelper.write_action_steps_for_attach_to_file(
            action_list,chunk,EXISTING_ACTIONS_DELIMITER,NEW_TEXT_DELIMITER,temp_action_file
        )
        
        attached_file = gemini_processor.attach_file(temp_action_file)
        
        #generate a response from the LLM
        #ai_response_text = gemini_processor.generate_content_until_complete(messages,attached_file)

        item_list = gemini_processor.generate_content_until_complete_with_post_process_function(
            RefDataHelper.convert_simple_array_text_to_unique_sorted_list,messages,attached_file)
        
        action_list.extend(item_list)

        action_list = sorted(list(set(action_list)))

        RefDataHelper.write_list_to_file(action_list,working_action_file)
    
    print(
        """ 
        Step 0.3 -- extracted cleaned actions    
        Complete 
        """)
    return action_list


async def main():

        
    
    args_loader.print()

    debug_file = out_folder + "/gemini_debug.txt"
   
    recipe_df = pd.read_csv(recipe_constants.RECIPE_FILE).sample(frac=recipe_constants.RECIPE_SAMPLE_RATIO, random_state=1)
    steps_list = recipe_df["steps"].tolist()
    extracted_actions = process_actions_extraction(steps_list,debug_file=debug_file)
    extracted_actions = process_action_reduction(extracted_actions,debug_file=debug_file)
    RefDataHelper.write_list_to_file(extracted_actions,recipe_constants.EXTRACTED_COOKING_ACTIONS_FILE)
   
       
             

if __name__ == "__main__":
    asyncio.run(main())


    