from database import *
import time
from datetime import datetime,timedelta
import ast
import asyncio
from surrealdb import AsyncSurrealDB
import pandas as pd
from surql_recipes_steps import SurqlRecipesAndSteps
from surql_ref_data import SurqlReferenceData
from surql_ddl import SurqlDDL
from embeddings import EmbeddingModel
from constants import Constants
from helpers import Helpers
import numpy as np
from collections import defaultdict




out_folder = Constants.THIS_FOLDER + "/rec_ing_normal_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
constants = Constants()
constants.LoadArgs("Input Embeddings Model")


action_processing_durations = []
action_sql_durations = []
step_update_durations = []

async def process_step_action_extraction():


    start_time = time.time()




    async with AsyncSurrealDB(constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(constants.DB_PARAMS.username,constants.DB_PARAMS.password)
        await db.use(constants.DB_PARAMS.namespace, constants.DB_PARAMS.database)
        
        refDataProcessor =  SurqlReferenceData(db)
        stepDataProcessor = SurqlRecipesAndSteps(db)

        list_actions_result = await refDataProcessor.select_all_actions()
        actions = list_actions_result[0]["result"]
        step_normalized_actions = defaultdict(list)
        i = 0
        total_actions = len(actions)
        for action in actions:
            i += 1
            action_processing_start_time = time.time()

            step_results = await stepDataProcessor.select_steps_that_use_action(action["id"])

            action_sql_duration = Helpers.time_str_to_seconds(step_results[0]["time"])
            action_sql_durations.append(action_sql_duration)

            steps = step_results[0]["result"]

            
            


            for step in steps:
                step_id = str(step["id"])
                step_normalized_actions[step_id].append(action["id"])



            current_time = time.time() 
            percentage = i/total_actions

            elapsed_duration = current_time - start_time
            elapsed_duration_minutes = elapsed_duration/60
            average_duration = elapsed_duration / i if i else 0
            average_duration_ms = average_duration * 1000

            action_processing_duration = current_time - action_processing_start_time
            action_processing_durations.append(action_processing_duration)
            action_processing_durations_ms = action_processing_duration*1000

            action_sql_duration_ms = action_sql_duration*1000

            est_time_remaining = average_duration * (total_actions - i)
            est_time_remaining_minutes = est_time_remaining / 60


            print("parsing_action-{counter}/{total_count}\t{percent}\test_remaining\t{est_time_remaining}\telapsed\t{elapsed_duration}\tlast_duration\t{this_method_duration}\tavg_duration\t{average_duration}\tthis_sql_duration\t{action_sql_duration}\t-{row}\t\t\t\t\t\t\t\t\t\t\t".format(
                        counter = i,
                        total_count = total_actions,
                        percent = f"{percentage:.2%}",
                        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                        average_duration = f"{average_duration_ms:.3f} ms",
                        this_method_duration = f"{action_processing_durations_ms:.3f} ms",
                        action_sql_duration = f"{action_sql_duration_ms:.3f} ms",
                        est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                        row = action["id"]
                        ), end="\r", flush=True) 




        i = 0
        N = len(step_normalized_actions)

        for key, value in step_normalized_actions.items():
            i += 1      
            step_update_start_time = time.time()
            outcome = await stepDataProcessor.update_step_actions(key,value) 

            current_time = time.time()
            percentage = i/N
            step_update_duration = current_time - step_update_start_time
            step_update_durations.append(step_update_duration)

            elapsed_duration = current_time - start_time
            elapsed_duration_minutes = elapsed_duration/60

            average_duration = elapsed_duration / i if i else 0
            average_duration_ms = average_duration * 1000


            step_update_duration_ms = step_update_duration * 1000


            est_time_remaining = average_duration * (N - i)
            est_time_remaining_minutes = est_time_remaining / 60


            print("updating_step_actions-{counter}/{total_count}\t{percent}\test_remaining\t{est_time_remaining}\telapsed\t{elapsed_duration}\tlast_duration\t{this_method_duration}\tavg_duration\t{average_duration}\t-{row}\t-{icnt}\t\t\t\t\t\t\t\t\t\t\t".format(
                        counter = i,
                        total_count = N,
                        percent = f"{percentage:.2%}",
                        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                        average_duration = f"{average_duration_ms:.3f} ms",
                        this_method_duration = f"{step_update_duration_ms:.3f} ms",
                        est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                        row = key,
                        icnt=len(value)
                        ), end="\r", flush=True) 
            

        
    current_time = time.time() 
    elapsed_duration = current_time - start_time
    elapsed_duration_minutes = elapsed_duration/60


    avg_action_processing_duration = np.mean(action_processing_durations)
    avg_action_processing_duration_ms = avg_action_processing_duration * 1000

    min_action_processing_duration = np.min(action_processing_durations)
    min_action_processing_duration_ms = min_action_processing_duration * 1000

    max_action_processing_duration = np.max(action_processing_durations)
    max_action_processing_duration_ms = max_action_processing_duration * 1000

    avg_action_sql_duration = np.mean(action_sql_durations)
    avg_action_sql_duration_ms = avg_action_sql_duration * 1000

    min_action_sql_duration = np.min(action_sql_durations)
    min_action_sql_duration_ms = min_action_sql_duration * 1000

    max_action_sql_duration = np.max(action_sql_durations)
    max_action_sql_duration_ms = max_action_sql_duration * 1000

    avg_step_update_duration = np.mean(step_update_durations)
    avg_step_update_duration_ms = avg_step_update_duration * 1000

    min_step_update_duration = np.min(step_update_durations)
    min_step_update_duration_ms = min_step_update_duration * 1000

    max_step_update_duration = np.max(step_update_durations)
    max_step_update_duration_ms = max_step_update_duration * 1000


    print(
        """  
        step 5b process step actions                                                                                                     
        total elapsed {elapsed_duration}                                                                                                         
        {Na} action search (avg,min,max) ({avg_action_processing_duration},{min_action_processing_duration},{max_action_processing_duration}) 
        {Na} action search sql (avg,min,max) ({avg_action_sql_duration},{min_action_sql_duration},{max_action_sql_duration}) 
        {Ns} step update (avg,min,max) ({avg_step_update_duration},{min_step_update_duration},{max_step_update_duration})                                                       
        """.format(
        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
        avg_action_processing_duration = f"{avg_action_processing_duration_ms:.3f} ms",
        min_action_processing_duration = f"{min_action_processing_duration_ms:.3f} ms",
        max_action_processing_duration = f"{max_action_processing_duration_ms:.3f} ms",
        avg_action_sql_duration = f"{avg_action_sql_duration_ms:.3f} ms",
        min_action_sql_duration = f"{min_action_sql_duration_ms:.3f} ms",
        max_action_sql_duration = f"{max_action_sql_duration_ms:.3f} ms",
        avg_step_update_duration = f"{avg_step_update_duration_ms:.3f} ms",
        min_step_update_duration = f"{min_step_update_duration_ms:.3f} ms",
        max_step_update_duration = f"{max_step_update_duration_ms:.3f} ms",
        Na = len(actions),
        Ns = len(step_normalized_actions)
        )) 


async def main():


    print("""
          STEP 5b extract actions from steps
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
    await process_step_action_extraction()



if __name__ == "__main__":
    asyncio.run(main())


    