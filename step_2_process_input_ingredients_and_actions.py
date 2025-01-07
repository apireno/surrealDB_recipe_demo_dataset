from database import *
import time
import asyncio
from surrealdb import AsyncSurrealDB
from surql_ref_data import SurqlReferenceData
from surql_ddl import SurqlDDL
from constants import Constants


constants = Constants()
constants.LoadArgs("Process master ingredients and actions import")

out_folder = Constants.THIS_FOLDER + "/ins_ing_acts_{0}".format(time.strftime("%Y%m%d-%H%M%S"))


async def process_ingredients_actions(truncated_ingredients):


    async with AsyncSurrealDB(constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(constants.DB_PARAMS.username,constants.DB_PARAMS.password)
        await db.use(constants.DB_PARAMS.namespace, constants.DB_PARAMS.database)


        cooking_actions_with_parent =  SurqlReferenceData.extract_cooking_actions_with_parent()
        
        print("Inserting {0} cooking actions".format(len(cooking_actions_with_parent)) )
        #embeddingModel = EmbeddingModel(constants.MODEL_PATH)

        refDataProcessor = SurqlReferenceData(db)
        out = await db.query(SurqlDDL.DDL_ACTION)
        out = await refDataProcessor.insert_cooking_actions()

        print("Inserting {0} ingredients".format(len(truncated_ingredients)) )
        out = await db.query(SurqlDDL.DDL_INGREDIENT)
        for ingredient in truncated_ingredients:
            print("ingredient {0}".format(ingredient)) 
            out = await refDataProcessor.insert_ingredient(ingredient)
       
    print(
        """ 
        Step 2 -- Insert ingredients and cooking actions    
        Complete 
        """)


async def main():

    print("""
          STEP 2 ingredients and actions
          DB_PARAMS {URL} N: {NS} DB: {DB} USER: {DB_USER}

          DB_USER_ENV_VAR {DB_USER_ENV_VAR}
          DB_PASS_ENV_VAR {DB_PASS_ENV_VAR}

          MODEL_PATH {MODEL_PATH}
          INGREDIENTS_PATH {INGREDIENTS_PATH}
          MODEL_PATH {MODEL_PATH}
          RECIPE_FILE {RECIPE_FILE}
          REVIEW_FILE {REVIEW_FILE}

          RECIPE_SAMPLE_RATIO {RECIPE_SAMPLE_RATIO}
          REVIEW_SAMPLE_RATIO {REVIEW_SAMPLE_RATIO}

          """.format(
              URL = constants.DB_PARAMS.url,
              DB_USER = constants.DB_PARAMS.username,
              NS = constants.DB_PARAMS.namespace,
              DB = constants.DB_PARAMS.database,
              DB_USER_ENV_VAR = constants.DB_USER_ENV_VAR,
              DB_PASS_ENV_VAR = constants.DB_PASS_ENV_VAR,
              MODEL_PATH = constants.MODEL_PATH,
              INGREDIENTS_PATH = constants.PREV_EXTRACTED_INGREDIENTS_FILE,
              RECIPE_FILE = constants.RECIPE_FILE,
              REVIEW_FILE = constants.REVIEW_FILE,
              RECIPE_SAMPLE_RATIO = constants.RECIPE_SAMPLE_RATIO,
              REVIEW_SAMPLE_RATIO = constants.REVIEW_SAMPLE_RATIO
          )
          )
    

    truncated_ingredients = []
    try:
        with open(constants.PREV_EXTRACTED_INGREDIENTS_FILE, 'r') as file:
            truncated_ingredients = file.read().splitlines()
    except:
        truncated_ingredients = []


    await process_ingredients_actions(truncated_ingredients)



if __name__ == "__main__":
    asyncio.run(main())


    