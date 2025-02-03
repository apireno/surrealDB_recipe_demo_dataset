
import asyncio
from surrealdb import AsyncSurreal
import pandas as pd
import numpy as np
import ast
import time
from helpers import Helpers
from datetime import datetime,timedelta
from surrealdb import AsyncSurreal
from surrealDB_embedding_model.embedding_model_constants import DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, ArgsLoader,DATA_FOLDER
from surql_recipes_steps import SurqlRecipesAndSteps
from recipe_data_surql_ddl import RecipeDataSurqlDDL
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel
from helpers import Helpers
from surrealDB_embedding_model.database import Database
import math

out_folder = THIS_FOLDER + "/logging/process_recipes_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
recipe_constants = RecipeDataConstants()

Helpers.ensure_folders([out_folder])


step_insert_durations = []
recipe_insert_durations = []
recipe_full_transation_method_durations = []





async def process_ddl(process_with_indexes = True):

    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:

        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)



        embedDataProcessor = SurqlEmbeddingModel(db)
        embed_dimensions = await embedDataProcessor.get_model_dimensions()
        
        #only recreate the tables if not picking up from a prev run...
        outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_STEP))

        outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_RECIPE))
        if process_with_indexes==True:
            outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_STEP_INDEX_DEFINE.format(embed_dimensions=embed_dimensions)))
            outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_RECIPE_INDEX_DEFINE.format(embed_dimensions=embed_dimensions)))

async def process_post_ddl(process_with_indexes = True):
    if process_with_indexes==False:
        async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
            dataProcessor = SurqlRecipesAndSteps(db)

            auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
            await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)

            embedDataProcessor = SurqlEmbeddingModel(db)
            embed_dimensions = await embedDataProcessor.get_model_dimensions()

            print("\n\nRe-applying indexes")
            outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_ANALYZER))
            
            outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_STEP_INDEX_DEFINE_CONCURRENTLY.format(embed_dimensions=embed_dimensions)))
            outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_RECIPE_INDEX_DEFINE_CONCURRENTLY.format(embed_dimensions=embed_dimensions)))
            building_indexes = True
            index_processing_durations = []
            indexing_start_time = time.time()

            while building_indexes==True:
                
                step_indexes = await dataProcessor.check_index_statuses("step")
                recipe_indexes = await dataProcessor.check_index_statuses("recipe")
                results = {
                    "any_index_processing":False,
                    "status_string":"",
                    "index_processing_durations":index_processing_durations
                }
                results = parse_index_result(step_indexes,indexing_start_time,results)
                results = parse_index_result(recipe_indexes,indexing_start_time,results)
            
                index_processing_durations = results["index_processing_durations"]
                building_indexes = (results["any_index_processing"] == True) 
                Helpers.print_update(results["status_string"])
                if building_indexes == True:
                    time.sleep(10)
                    
            print("\nIndexing times:")
            for index_processing_duration in index_processing_durations:
                print(f"{index_processing_duration["index"]} - {index_processing_duration["duration"]:.1f} s")



async def process_recipe(dataProcessor:SurqlRecipesAndSteps,row,batch_number,counter,total_count,start_time,log_file):
    percentage = counter/total_count
    method_start_time = time.time() 
    recipe_insert_duration = 0
    #try:
    steps = Helpers.fix_json_quotes(row.steps)
    step_ids = []
    for index, step in enumerate(steps):
        step_start_time = time.time()
        outcome = await dataProcessor.insert_step(
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
    outcome = await dataProcessor.insert_recipe(
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




    log_file.write(
            f"{batch_number},{counter},{percentage:.2%},{row.id},{len(step_ids)},{elapsed_duration_minutes:.1f},{est_time_remaining_minutes:.1f},{(est_time_remaining_minutes+elapsed_duration_minutes):.1f},{this_method_duration_ms:.3f},{average_duration_ms:.3f},{recipe_insert_duration_ms:.3f},{(len(step_ids)*avg_step_insertion_duration_ms):.3f},{avg_step_insertion_duration_ms:.3f}\n"
    )

    


    str_to_format = "process_recipe-{batch_number}\t-{counter}\t/{total_count}\t{percent}\test_remaining:{est_time_remaining}\telapsed:{elapsed_duration}\tavg:{average_duration}\tavg_step_ins:{avg_step_insertion_duration}\trec_ins:{recipe_insert_duration}\t-{row}\t-{num_steps}\tlast:{this_method_duration}"
    Helpers.print_update(
        str_to_format.format(
                counter = counter,
                total_count = total_count,
                percent = f"{percentage:.2%}",
                elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                average_duration = f"{average_duration_ms:.3f} ms",
                this_method_duration = f"{this_method_duration_ms:.3f} ms",
                est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                avg_step_insertion_duration = f"{avg_step_insertion_duration_ms:.3f} ms",
                recipe_insert_duration = f"{recipe_insert_duration_ms:.3f} ms",
                row = row.id,
                num_steps = len(step_ids),
                batch_number = batch_number
                )

    )
    
async def process_recipe_batch(batch,batch_number,start_time,log_file):
    
    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)
        dataProcessor = SurqlRecipesAndSteps(db)
        i = 0
        for row in batch:
            i += 1
            await process_recipe(dataProcessor,row,batch_number,i,len(batch),start_time,log_file)



async def process_recipes(recipe_df,log_file,batch_size=1,total_records=0,offset=0):

    if total_records==0 :
        total_records = len(recipe_df)
    start_time = time.time()

    tasks = []
    for batch_number in range(offset, total_records, batch_size):
        batch = list(recipe_df[batch_number : batch_number + batch_size].itertuples())
        tasks +=[process_recipe_batch(batch,batch_number,start_time,log_file)]
            
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
        batch_size {batch_size}                                                                                                    
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
        batch_size = batch_size
        )) 

def parse_index_result(indexes,indexing_start_time,input_result):

    index_processing_durations = input_result["index_processing_durations"]
    any_index_processing = input_result["any_index_processing"]
    status_string = input_result["status_string"]
    


    for index in indexes:
        this_step_status_count = None
        this_step_status_error = None
        if "building" in index["status"]:
            this_step_status = index["status"]["building"]["status"]
            if "count" in index["status"]["building"]:
                this_step_status_count = index["status"]["building"]["count"]
            if "error" in index["status"]["building"]:
                this_step_status_error =  index["status"]["building"]["error"]

        else:
            this_step_status = "??"

        print(f"{index["index"]} {this_step_status}")
        status_string += f"{index["index"]} {this_step_status}"
        match this_step_status:
            case "built":
                index_processing_durations.append(
                    {"index":index["index"],"duration":(time.time()-indexing_start_time) }
                )
            case "initial":
                any_index_processing = True
                status_string += f" - count: {this_step_status_count}"
            case "error":
                status_string += f" - err: {this_step_status_error}"

        status_string += "\n"

    return {
        "index_processing_durations":index_processing_durations,
        "any_index_processing":any_index_processing,
        "status_string":status_string
    }
async def main():


    

    args_loader = ArgsLoader("STEP 3 Input recipes and steps into DB",db_constants,recipe_constants)
    args_loader.LoadArgs()
    args_loader.print()
    
    recipe_df = pd.read_csv(recipe_constants.RECIPE_FILE)

    recipe_df = recipe_df.sample(frac=recipe_constants.RECIPE_SAMPLE_RATIO, random_state=1)





    print(recipe_df.describe())
    print(recipe_df.head())

    total_records = len(recipe_df)
    num_conc = 1
    process_with_indexes = True
    batch_size = math.floor(len(recipe_df)/num_conc)
    benchmark_log = out_folder + "/log.csv"


    with open(benchmark_log,"w") as log_file:
        log_header = f"""
            total_count: {total_records} recipes (var steps per recipe)
            batch_size: {batch_size}
            url: {db_constants.DB_PARAMS.url}
            ns: {db_constants.DB_PARAMS.namespace}
            db: {db_constants.DB_PARAMS.database}
            now: {time.strftime("%Y%m%d-%H%M%S")}\n"""


        log_file.write(log_header)

        log_file.write(
                "batch,counter,percent,row_id,num_steps,elapsed[m],est_time_remaining[m],total_est[m],rec_and_steps[ms],avg[ms],rec_ins[ms],step_ins[ms],avg_step_ins[ms]\n"
        )
        log_file.flush()
        await process_ddl(process_with_indexes = process_with_indexes)
        await process_recipes(recipe_df,log_file,total_records=total_records,batch_size=batch_size)
        await process_post_ddl(process_with_indexes = process_with_indexes)



if __name__ == "__main__":
    asyncio.run(main())


    