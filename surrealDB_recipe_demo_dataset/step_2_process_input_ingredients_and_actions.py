import asyncio
import time
from surrealdb import AsyncSurreal
from surrealDB_embedding_model.embedding_model_constants import DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, ArgsLoader,DATA_FOLDER
from surql_ref_data import SurqlReferenceData
from recipe_data_surql_ddl import RecipeDataSurqlDDL
from helpers import Helpers
from extraction_ref_data_helpers import RefDataHelper
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel
from surrealDB_embedding_model.database import Database



out_folder = THIS_FOLDER + "/logging/sql_ing_act_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
recipe_constants = RecipeDataConstants()


Helpers.ensure_folders([out_folder])

async def process_ingredients(ingredient_list,ingredient_match_list):
    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)


        embedDataProcessor = SurqlEmbeddingModel(db)
        embed_dimensions = await embedDataProcessor.get_model_dimensions()

        outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_INGREDIENT.format(embed_dimensions=embed_dimensions)))
        print(f"Inserting {len(ingredient_list)} ingredients {len(ingredient_match_list)} substitutes")

        refDataProcessor = SurqlReferenceData(db)
        i = 0
        for ingredient in ingredient_list:
            outcome = await refDataProcessor.insert_ingredient(
                ingredient["ingredient"],ingredient["flavor"])
            


            i = i + 1
            str_to_format = "process_ingredient-{counter}/{total_count}\t{percent}\t-{row}\t-{flavor}"
            Helpers.print_update(
                str_to_format.format(
                        counter = i,
                        total_count = len(ingredient_list),
                        percent = f"{(i/len(ingredient_list)):.2%}",
                        row = ingredient["ingredient"],
                        flavor = ingredient["flavor"],
                        )

            )

        i = 0
        for ingredient_match in ingredient_match_list:
            outcome = await refDataProcessor.insert_ingredient_substitute(
                ingredient_match["entity"],
                ingredient_match["sub"],
                ingredient_match["rationale"],
                ingredient_match["confidence"]
            )

            
            i = i + 1
            str_to_format = "process_ingredient_match-{counter}/{total_count}\t{percent}\t-{row}\t-{sub}"
            Helpers.print_update(
                str_to_format.format(
                        counter = i,
                        total_count = len(ingredient_match_list),
                        percent = f"{(i/len(ingredient_match_list)):.2%}",
                        row = ingredient_match["entity"],
                        sub = ingredient_match["sub"],
                        )

            )
    print(
            """ 

            
            Step 2 -- Insert ingredients   
            Complete 
        """)
    
async def process_actions(action_list,action_match_list):



    low_confidence_list = [d for d in action_match_list if int(d['confidence']) <= 5]

    if len(low_confidence_list) > 0:
        print(f"Warning the following are matches are low confidence and will be removed")
        for item in low_confidence_list:
            print(item)
        

    action_match_list = [d for d in action_match_list if int(d['confidence']) > 5]

    parent_entities_that_dont_exist = RefDataHelper.find_unmatched_items(
        action_match_list,action_list,"parent",None
    )

    if len(parent_entities_that_dont_exist) > 0:
        print(f"Warning the following are parents that are missing from the list of actions. These will be added to the action list")
        for item in parent_entities_that_dont_exist:
            print(item)


        for match in parent_entities_that_dont_exist:
            action_list.append(match["parent"])

    

    



    
    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)


        embedDataProcessor = SurqlEmbeddingModel(db)
        embed_dimensions = await embedDataProcessor.get_model_dimensions()

        outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_ACTION.format(embed_dimensions=embed_dimensions)))
        print(f"Inserting {len(action_match_list)} actions")


        refDataProcessor = SurqlReferenceData(db)
        i = 0
        for action_match in action_match_list:
            outcome = await refDataProcessor.insert_cooking_action(
                action_match["entity"],action_match["parent"],action_match["rationale"],action_match["confidence"]
            )


            
            i = i + 1
            str_to_format = "process_action_and_match-{counter}/{total_count}\t{percent}\t-{row}\t-{parent}"
            Helpers.print_update(
                str_to_format.format(
                        counter = i,
                        total_count = len(action_match_list),
                        percent = f"{(i/len(action_match_list)):.2%}",
                        row = action_match["entity"],
                        parent = action_match["parent"],
                        ))

    print(
            """ 

            
            Step 2 -- Insert actions   
            Complete 
        """)

async def main():

    
        
    args_loader = ArgsLoader("STEP 2 - Insert reference data to DB ingredients and actions",db_constants,recipe_constants)
    args_loader.LoadArgs()
    args_loader.print()

    debug_file = out_folder + "/gemini_debug.txt"
    ingredient_list = RefDataHelper.convert_file_to_list(recipe_constants.EXTRACTED_INGREDIENTS_FILE)
    ingredient_match_list = RefDataHelper.convert_file_to_list(recipe_constants.MATCHED_INGREDIENTS_FILE)
    action_list = RefDataHelper.convert_file_to_list(recipe_constants.EXTRACTED_COOKING_ACTIONS_FILE)
    action_match_list = RefDataHelper.convert_file_to_list(recipe_constants.MATCHED_COOKING_ACTIONS_FILE)

    await process_ingredients(ingredient_list,ingredient_match_list)
    await process_actions(action_list,action_match_list)



if __name__ == "__main__":
    asyncio.run(main())


    