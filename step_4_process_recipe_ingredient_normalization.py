from database import *
import time
import asyncio
from surrealdb import AsyncSurrealDB
from surql_recipes_steps import SurqlRecipesAndSteps
from surql_ref_data import SurqlReferenceData
from constants import Constants
from helpers import Helpers
import numpy as np
from collections import defaultdict




out_folder = Constants.THIS_FOLDER + "/rec_ing_normal_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
constants = Constants()
constants.LoadArgs("Input Embeddings Model")


ingredient_processing_durations = []
ingredient_sql_durations = []
ingredient_parsing_durations = []
recipe_update_durations = []

async def process_recipe_ingredient_normalization():




    start_time = time.time()
    async with AsyncSurrealDB(constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(constants.DB_PARAMS.username,constants.DB_PARAMS.password)
        await db.use(constants.DB_PARAMS.namespace, constants.DB_PARAMS.database)
        
        refDataProcessor =  SurqlReferenceData(db)
        list_ingredient_result = await refDataProcessor.select_all_ingredients()

        total_ingredients = len(list_ingredient_result[0]["result"])
        

        recipe_normalized_ingredients = defaultdict(list)
        #recipe_normalized_ingredients = {}
        i = 0
        for ingredient in list_ingredient_result[0]["result"]:
            i += 1

            ingredient_start_time = time.time()

            recipeDataProcessor = SurqlRecipesAndSteps(db)

            outcome = await recipeDataProcessor.select_recipes_that_use_ingredient(ingredient["name"])
            ingredient_sql_duration = Helpers.time_str_to_seconds(outcome[0]["time"])
            ingredient_sql_durations.append(ingredient_sql_duration)


            ingredient_parsing_start_time = time.time()
            
            for recipe in outcome[0]["result"]:
                recipe_id =  str(recipe["id"])
                recipe_normalized_ingredients[recipe_id].append(ingredient["id"])

                
            
            current_time = time.time() 
            percentage = i/total_ingredients

            elapsed_duration = current_time - start_time
            elapsed_duration_minutes = elapsed_duration/60
            average_duration = elapsed_duration / i if i else 0
            average_duration_ms = average_duration * 1000

            ingredient_processing_duration = current_time - ingredient_start_time
            ingredient_processing_durations.append(ingredient_processing_duration)
            ingredient_processing_duration_ms = ingredient_processing_duration*1000

            ingredient_parsing_duration = current_time - ingredient_parsing_start_time
            ingredient_parsing_duration_ms = ingredient_parsing_duration*1000

            ingredient_sql_duration_ms = ingredient_sql_duration*1000


            est_time_remaining = average_duration * (total_ingredients - i)
            est_time_remaining_minutes = est_time_remaining / 60

            print("collecting_ingredients-{counter}/{total_count}\t{percent}\test_remaining\t{est_time_remaining}\telapsed\t{elapsed_duration}\tlast_duration\t{this_method_duration}\tlast_sql_duration\t{ingredient_sql_duration}\tlast_parse_duration\t{ingredient_parsing_duration}\tavg_duration\t{average_duration}\t-{row}\t\t\t\t\t\t\t\t\t\t\t\t".format(
                        counter = i,
                        total_count = total_ingredients,
                        percent = f"{percentage:.2%}",
                        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                        average_duration = f"{average_duration_ms:.3f} ms",
                        this_method_duration = f"{ingredient_processing_duration_ms:.3f} ms",
                        ingredient_sql_duration = f"{ingredient_sql_duration_ms:.3f} ms",
                        ingredient_parsing_duration = f"{ingredient_parsing_duration_ms:.3f} ms",
                        est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                        row = ingredient["name"]
                        ), end="\r", flush=True) 



    i = 0
    N = len(recipe_normalized_ingredients)
    async with AsyncSurrealDB(constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(constants.DB_PARAMS.username,constants.DB_PARAMS.password)
        await db.use(constants.DB_PARAMS.namespace, constants.DB_PARAMS.database)
        recipeDataProcessor = SurqlRecipesAndSteps(db)

        for key, value in recipe_normalized_ingredients.items():
            i += 1
            recipe_start_time = time.time()
            try:
                outcome = await recipeDataProcessor.update_recipe_normalized_ingredients(key,value)  
            
            except Exception as e:
                 Helpers.logError(
                     [key,value],"update_rec_norm_ing",e,out_folder
                 )
            
            current_time = time.time() 
            percentage = i/N

            elapsed_duration = current_time - start_time
            elapsed_duration_minutes = elapsed_duration/60
            average_duration = elapsed_duration / i if i else 0
            average_duration_ms = average_duration * 1000

            recipe_update_duration = current_time - recipe_start_time
            recipe_update_durations.append(recipe_update_duration)
            recipe_update_duration_ms = recipe_update_duration*1000


            est_time_remaining = recipe_update_duration * (N - i)
            est_time_remaining_minutes = est_time_remaining / 60

            print("updating_recipes-{counter}/{total_count}\t{percent}\test_remaining\t{est_time_remaining}\telapsed\t{elapsed_duration}\tlast_duration\t{this_method_duration}\tavg_duration\t{average_duration}\t-{row}\t-{value}\t\t\t\t\t\t\t\t\t\t\t\t".format(
                        counter = i,
                        total_count = N,
                        percent = f"{percentage:.2%}",
                        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                        average_duration = f"{average_duration_ms:.3f} ms",
                        this_method_duration = f"{recipe_update_duration_ms:.3f} ms",
                        est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                        row = key,
                        value = len(value)
                        ), end="\r", flush=True) 
            
    
    current_time = time.time() 
    elapsed_duration = current_time - start_time
    elapsed_duration_minutes = elapsed_duration/60
    
    avg_ingredient_processing_duration = np.mean(ingredient_processing_durations)
    avg_ingredient_processing_duration_ms = avg_ingredient_processing_duration * 1000

    min_ingredient_processing_duration = np.min(ingredient_processing_durations)
    min_ingredient_processing_duration_ms = min_ingredient_processing_duration * 1000

    max_ingredient_processing_duration = np.max(ingredient_processing_durations)
    max_ingredient_processing_duration_ms = max_ingredient_processing_duration * 1000


    avg_recipe_update_duration = np.mean(recipe_update_durations)
    avg_recipe_update_duration_ms = avg_recipe_update_duration * 1000

    min_recipe_update_duration = np.min(recipe_update_durations)
    min_recipe_update_duration_ms = min_recipe_update_duration * 1000

    max_recipe_update_duration = np.max(recipe_update_durations)
    max_recipe_update_duration_ms = max_recipe_update_duration * 1000


    avg_ingredient_sql_duration = np.mean(ingredient_sql_durations)
    avg_ingredient_sql_duration_ms = avg_ingredient_sql_duration * 1000

    min_ingredient_sql_duration = np.min(ingredient_sql_durations)
    min_ingredient_sql_duration_ms = min_ingredient_sql_duration * 1000

    max_ingredient_sql_duration = np.max(ingredient_sql_durations)
    max_ingredient_sql_duration_ms = max_ingredient_sql_duration * 1000

    
    print("""
          STEP 4 normalize ingredients for recipes
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




async def main():

    print("""
          STEP 4
          DB_PARAMS {URL} N-{NS} DB-{DB}
          PREV_EXTRACTED_INGREDIENTS_FILE {PREV_EXTRACTED_INGREDIENTS_FILE}
          MODEL_PATH {MODEL_PATH}
          RECIPE_FILE {RECIPE_FILE}
          REVIEW_FILE {REVIEW_FILE}
          RECIPE_SAMPLE_RATIO {RECIPE_SAMPLE_RATIO}
          REVIEW_SAMPLE_RATIO {REVIEW_SAMPLE_RATIO}
          
          
          
          """.format(
              URL = constants.DB_PARAMS.url,
              NS = constants.DB_PARAMS.namespace,
              DB = constants.DB_PARAMS.database,
              PREV_EXTRACTED_INGREDIENTS_FILE = constants.PREV_EXTRACTED_INGREDIENTS_FILE,
              MODEL_PATH = constants.MODEL_PATH,
              RECIPE_FILE = constants.RECIPE_FILE,
              REVIEW_FILE = constants.REVIEW_FILE,
              RECIPE_SAMPLE_RATIO = constants.RECIPE_SAMPLE_RATIO,
              REVIEW_SAMPLE_RATIO = constants.REVIEW_SAMPLE_RATIO
          )
          )
    await process_recipe_ingredient_normalization()


if __name__ == "__main__":
    asyncio.run(main())


    