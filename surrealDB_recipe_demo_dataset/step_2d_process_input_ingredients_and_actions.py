import asyncio
import time
from surrealdb import AsyncSurrealDB
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader
from surql_ref_data import SurqlReferenceData
from recipe_data_surql_ddl import RecipeDataSurqlDDL

out_folder = THIS_FOLDER + "/logging/ing_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
args_loader = RecipeArgsLoader("STEP 2 - Insert reference data to DB ingredients and actions",db_constants,embed_constants,recipe_constants)
args_loader.LoadArgs()


async def process_ingredients_actions(truncated_ingredients):


    async with AsyncSurrealDB(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(db_constants.DB_PARAMS.username,db_constants.DB_PARAMS.password)
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)


        cooking_actions_with_parent =  SurqlReferenceData.extract_cooking_actions_with_parent()
        
        print("Inserting {0} cooking actions".format(len(cooking_actions_with_parent)) )
        #embeddingModel = EmbeddingModel(db_constants.MODEL_PATH)

        refDataProcessor = SurqlReferenceData(db)
        out = await db.query(RecipeDataSurqlDDL.DDL_ACTION)
        out = await refDataProcessor.insert_cooking_actions()

        print("Inserting {0} ingredients".format(len(truncated_ingredients)) )
        out = await db.query(RecipeDataSurqlDDL.DDL_INGREDIENT)
        for ingredient in truncated_ingredients:
            print("ingredient {0}".format(ingredient)) 
            out = await refDataProcessor.insert_ingredient(ingredient)
       
    print(
        """ 

        
        Step 2 -- Insert ingredients and cooking actions    
        Complete 
        """)


async def main():

    
    
    args_loader.print()

    truncated_ingredients = []
    try:
        with open(recipe_constants.EXTRACTED_INGREDIENTS_FILE, 'r') as file:
            truncated_ingredients = file.read().splitlines()
    except:
        truncated_ingredients = []


    await process_ingredients_actions(truncated_ingredients)



if __name__ == "__main__":
    asyncio.run(main())


    