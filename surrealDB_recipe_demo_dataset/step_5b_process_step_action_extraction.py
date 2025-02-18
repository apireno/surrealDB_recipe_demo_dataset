

import asyncio
from surrealdb import AsyncSurreal
import numpy as np
import time
from helpers import Helpers
from collections import defaultdict
from surrealdb import AsyncSurreal
from surrealDB_embedding_model.embedding_model_constants import DatabaseConstants,THIS_FOLDER
from surrealDB_embedding_model.database import Database
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel
from recipe_data_constants import RecipeDataConstants, ArgsLoader,DATA_FOLDER
from recipe_data_surql_ddl import RecipeDataSurqlDDL
from surql_recipes_steps import SurqlRecipesAndSteps
from surql_ref_data import SurqlReferenceData


out_folder = THIS_FOLDER + "/logging/step_action_extraction_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
recipe_constants = RecipeDataConstants()




action_processing_durations = []
step_update_durations = []

async def process_step_action_extraction():


    start_time = time.time()




    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)
        
        refDataProcessor =  SurqlReferenceData(db)
        stepDataProcessor = SurqlRecipesAndSteps(db)

        refDataProcessor =  SurqlReferenceData(db)
        embedDataProcessor = SurqlEmbeddingModel(db)
        embed_dimensions = await embedDataProcessor.get_model_dimensions() 
        outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_SEARCH_FUNCTIONS.format(embed_dimensions=embed_dimensions)))


        list_actions_result = await refDataProcessor.select_all_actions()
        actions = list_actions_result
        step_normalized_actions = defaultdict(list)
        i = 0
        total_actions = len(actions)
        for action in actions:
            i += 1
            action_processing_start_time = time.time()

            step_results = await stepDataProcessor.select_steps_that_use_action(action["id"])

            for step in step_results:
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


            est_time_remaining = average_duration * (total_actions - i)
            est_time_remaining_minutes = est_time_remaining / 60



            str_to_format = "parsing_action-{counter}/{total_count}:{percent}\t\test_remaining:{est_time_remaining}\t\telapsed:{elapsed_duration}\t\tlast_duration:{this_method_duration}\t\tavg_duration:{average_duration}\t\t-{row}"
            Helpers.print_update(str_to_format.format(
                        counter = i,
                        total_count = total_actions,
                        percent = f"{percentage:.2%}",
                        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                        average_duration = f"{average_duration_ms:.3f} ms",
                        this_method_duration = f"{action_processing_durations_ms:.3f} ms",
                        est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                        row = action["id"]
                        )) 




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


            print("updating_step_actions-{counter}/{total_count}:{percent}\t\test_remaining:{est_time_remaining}\t\telapsed:{elapsed_duration}\t\tlast_duration:{this_method_duration}\t\tavg_duration:{average_duration}\t\t-{row}\t\t-{icnt}\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t".format(
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
        {Ns} step update (avg,min,max) ({avg_step_update_duration},{min_step_update_duration},{max_step_update_duration})                                                       
        """.format(
        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
        avg_action_processing_duration = f"{avg_action_processing_duration_ms:.3f} ms",
        min_action_processing_duration = f"{min_action_processing_duration_ms:.3f} ms",
        max_action_processing_duration = f"{max_action_processing_duration_ms:.3f} ms",
        avg_step_update_duration = f"{avg_step_update_duration_ms:.3f} ms",
        min_step_update_duration = f"{min_step_update_duration_ms:.3f} ms",
        max_step_update_duration = f"{max_step_update_duration_ms:.3f} ms",
        Na = len(actions),
        Ns = len(step_normalized_actions)
        )) 


async def main():

    args_loader = ArgsLoader("STEP 5b - Step action extraction",db_constants,recipe_constants)
    args_loader.LoadArgs()
    args_loader.print()
    await process_step_action_extraction()



if __name__ == "__main__":
    asyncio.run(main())


    