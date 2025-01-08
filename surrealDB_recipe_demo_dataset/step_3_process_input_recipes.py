
import asyncio
from surrealdb import AsyncSurrealDB
import pandas as pd
import numpy as np
import ast
import time
from helpers import Helpers
from datetime import datetime,timedelta
from surrealdb import AsyncSurrealDB
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader
from surql_recipes_steps import SurqlRecipesAndSteps
from recipe_data_surql_ddl import RecipeDataSurqlDDL

out_folder = THIS_FOLDER + "/process_recipes_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
args_loader = RecipeArgsLoader("Input recipes and steps",db_constants,embed_constants,recipe_constants)
args_loader.LoadArgs()


step_insert_durations = []
recipe_insert_durations = []
recipe_full_transation_method_durations = []

async def process_recipe(dataProcessor:SurqlRecipesAndSteps,row,counter,total_count,start_time):
    percentage = counter/total_count
    method_start_time = time.time() 
    recipe_insert_duration = 0
    #try:
    steps = Helpers.fix_json_quotes(row.steps)
    step_ids = []
    for index, step in enumerate(steps):
        step_start_time = time.time()
        out = await dataProcessor.insert_step(
            row.id,index,step
        )
        step_insert_durations.append(
            time.time() - step_start_time
        )
        step_ids.append(
            {
                "recipe_id" : row.id,
                "sort_order" : index
            }
        )
        
    recipe_start_time = time.time()
    out = await dataProcessor.insert_recipe(
                        row.id,
                        row.name,
                        row.contributor_id,
                        row.minutes,
                        ast.literal_eval(row.tags),
                        step_ids,
                        ast.literal_eval(row.ingredients),
                        row.description,
                        ast.literal_eval(row.nutrition),
                        (datetime.strptime(row.submitted, "%Y-%m-%d") + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                                )
    
    recipe_insert_duration = time.time() - recipe_start_time
    recipe_insert_durations.append(recipe_insert_duration)

    # except Exception as e:
    #     await Helpers.logError(row,"recipe",e,out_folder)
        


    current_time = time.time() 
    elapsed_duration = current_time - start_time
    elapsed_duration_minutes = elapsed_duration/60
    average_duration = elapsed_duration / counter if counter else 0
    average_duration_ms = average_duration * 1000
    this_method_duration = current_time - method_start_time
    this_method_duration_ms = this_method_duration * 1000
    recipe_full_transation_method_durations.append(this_method_duration)

    est_time_remaining = average_duration * (total_count - counter)
    est_time_remaining_minutes = est_time_remaining / 60
    avg_step_insertion_duration = np.mean(step_insert_durations)
    avg_step_insertion_duration_ms = avg_step_insertion_duration * 1000
    recipe_insert_duration_ms = recipe_insert_duration * 1000

    print("process_recipe-{counter}/{total_count}\t{percent}\test_remaining\t{est_time_remaining}\telapsed\t{elapsed_duration}\tlast_duration\t{this_method_duration}\tavg_duration\t{average_duration}\tavg_step_ins_duration\t{avg_step_insertion_duration}\trec_ins_duration\t{recipe_insert_duration}\t-{row}-|".format(
                counter = counter,
                total_count = total_count,
                percent = f"{percentage:.2%}",
                elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                average_duration = f"{average_duration_ms:.3f} ms",
                this_method_duration = f"{this_method_duration_ms:.3f} ms",
                est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                avg_step_insertion_duration = f"{avg_step_insertion_duration_ms:.3f} ms",
                recipe_insert_duration = f"{recipe_insert_duration_ms:.3f} ms",
                row = row.id
                ), end="\r", flush=True) 
    


async def process_recipes(recipe_df,batch_size=1,total_records=0,offset=0):

    #embeddingModel = EmbeddingModel(constants.MODEL_PATH)

    if total_records==0 :
        total_records = len(recipe_df)
    start_time = time.time()
    async with AsyncSurrealDB(db_constants.DB_PARAMS.url) as db:

        auth_token = await db.sign_in(db_constants.DB_PARAMS.username,db_constants.DB_PARAMS.password)
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)

        out = await db.query(RecipeDataSurqlDDL.DDL_STEP)
        out = await db.query(RecipeDataSurqlDDL.DDL_RECIPE)

        #dataProcessor = SurqlRecipesAndSteps(db,embeddingModel)
        dataProcessor = SurqlRecipesAndSteps(db)
        
        for i in range(offset, total_records, batch_size):
            batch = recipe_df[i : i + batch_size].itertuples()
            tasks = [process_recipe(dataProcessor,row,i,total_records,start_time) for row in batch]
            await asyncio.gather(*tasks)

    
    current_time = time.time() 
    elapsed_duration = current_time - start_time
    elapsed_duration_minutes = elapsed_duration/60
    average_duration = elapsed_duration / total_records if total_records else 0
    average_duration_ms = average_duration * 1000
    
    min_recipe_full_transation_method_duration = np.min(recipe_full_transation_method_durations)
    min_recipe_full_transation_method_duration_ms = min_recipe_full_transation_method_duration * 1000

    max_recipe_full_transation_method_duration = np.max(recipe_full_transation_method_durations)
    max_recipe_full_transation_method_duration_ms = max_recipe_full_transation_method_duration * 1000


    avg_step_insertion_duration = np.mean(step_insert_durations)
    avg_step_insertion_duration_ms = avg_step_insertion_duration * 1000

    min_step_insertion_duration = np.min(step_insert_durations)
    min_step_insertion_duration_ms = min_step_insertion_duration * 1000

    max_step_insertion_duration = np.max(step_insert_durations)
    max_step_insertion_duration_ms = max_step_insertion_duration * 1000

    avg_recipe_insertion_duration = np.mean(recipe_insert_durations)
    avg_recipe_insertion_duration_ms = avg_recipe_insertion_duration * 1000

    min_recipe_insertion_duration = np.min(recipe_insert_durations)
    min_recipe_insertion_duration_ms = min_recipe_insertion_duration * 1000

    max_recipe_insertion_duration = np.max(recipe_insert_durations)
    max_recipe_insertion_duration_ms = max_recipe_insertion_duration * 1000

    print(
        """


        
        step 3 process input recipes and steps                                                                                                        
        total elapsed {elapsed_duration}                                                                                                         
        full recipe transaction x{num_recipes} (avg,min,max) ({average_duration},{min_recipe_full_transation_method_duration},{max_recipe_full_transation_method_duration})
        step x{num_steps} (avg,min,max) ({avg_step_insertion_duration},{min_step_insertion_duration},{max_step_insertion_duration}) 
        recipe (avg,min,max) ({avg_recipe_insertion_duration},{min_recipe_insertion_duration},{max_recipe_insertion_duration})                                                                                    
        """.format(
        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
        average_duration = f"{average_duration_ms:.3f} ms",
        min_recipe_full_transation_method_duration = f"{min_recipe_full_transation_method_duration_ms:.3f} ms",
        max_recipe_full_transation_method_duration = f"{max_recipe_full_transation_method_duration_ms:.3f} ms",
        avg_step_insertion_duration = f"{avg_step_insertion_duration_ms:.3f} ms",
        min_step_insertion_duration = f"{min_step_insertion_duration_ms:.3f} ms",
        max_step_insertion_duration = f"{max_step_insertion_duration_ms:.3f} ms",
        avg_recipe_insertion_duration = f"{avg_recipe_insertion_duration_ms:.3f} ms",
        min_recipe_insertion_duration = f"{min_recipe_insertion_duration_ms:.3f} ms",
        max_recipe_insertion_duration = f"{max_recipe_insertion_duration_ms:.3f} ms",
        num_recipes = total_records,
        num_steps = len(step_insert_durations),
        )) 


async def main():


    
    print("""
          STEP 3 recipes
          DB_PARAMS {URL} N: {NS} DB: {DB} USER: {DB_USER}

          DB_USER_ENV_VAR {DB_USER_ENV_VAR}
          DB_PASS_ENV_VAR {DB_PASS_ENV_VAR}

          MODEL_PATH {MODEL_PATH}

          RECIPE_FILE {RECIPE_FILE}
          REVIEW_FILE {REVIEW_FILE}

          PREV_EXTRACTED_INGREDIENTS_FILE {PREV_EXTRACTED_INGREDIENTS_FILE}

          RECIPE_SAMPLE_RATIO {RECIPE_SAMPLE_RATIO}
          REVIEW_SAMPLE_RATIO {REVIEW_SAMPLE_RATIO}

          """.format(
              URL = db_constants.DB_PARAMS.url,
              DB_USER = db_constants.DB_PARAMS.username,
              NS = db_constants.DB_PARAMS.namespace,
              DB = db_constants.DB_PARAMS.database,
              DB_USER_ENV_VAR = db_constants.DB_USER_ENV_VAR,
              DB_PASS_ENV_VAR = db_constants.DB_PASS_ENV_VAR,
              MODEL_PATH = embed_constants.MODEL_PATH,
              RECIPE_FILE = recipe_constants.RECIPE_FILE,
              REVIEW_FILE = recipe_constants.REVIEW_FILE,
              PREV_EXTRACTED_INGREDIENTS_FILE = recipe_constants.PREV_EXTRACTED_INGREDIENTS_FILE,
              RECIPE_SAMPLE_RATIO = recipe_constants.RECIPE_SAMPLE_RATIO,
              REVIEW_SAMPLE_RATIO = recipe_constants.REVIEW_SAMPLE_RATIO

          )
          )
    
    recipe_df = pd.read_csv(recipe_constants.RECIPE_FILE)

    recipe_df = recipe_df.sample(frac=recipe_constants.RECIPE_SAMPLE_RATIO, random_state=1)

    print(recipe_df.describe())
    print(recipe_df.head())


    await process_recipes(recipe_df,batch_size=1)



if __name__ == "__main__":
    asyncio.run(main())


    