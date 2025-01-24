

import asyncio
from surrealdb import AsyncSurrealDB
import numpy as np
import time
from helpers import Helpers
from collections import defaultdict
from surrealdb import AsyncSurrealDB
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader,DATA_FOLDER
from surql_recipes_steps import SurqlRecipesAndSteps
from surql_ref_data import SurqlReferenceData

out_folder = THIS_FOLDER + "/logging/step_ingred_extraction_normal_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
args_loader = RecipeArgsLoader("STEP 5a - Step ingredient normalization",db_constants,embed_constants,recipe_constants)
args_loader.LoadArgs()


ingredient_processing_durations = []
ingredient_sql_durations = []
ingredient_parsing_durations = []
step_update_durations = []

async def process_recipe_ingredient_normalization():




    start_time = time.time()
    async with AsyncSurrealDB(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(db_constants.DB_PARAMS.username,db_constants.DB_PARAMS.password)
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)
        
        refDataProcessor =  SurqlReferenceData(db)
        list_ingredient_result = await refDataProcessor.select_all_ingredients()

        total_ingredients = len(list_ingredient_result[0]["result"])
        

        step_normalized_ingredients = defaultdict(list)
        #recipe_normalized_ingredients = {}
        i = 0
        print("Parsing {0} ingredients".format(total_ingredients))
        for ingredient in list_ingredient_result[0]["result"]:
            i += 1

            ingredient_start_time = time.time()

            recipeDataProcessor = SurqlRecipesAndSteps(db)

            outcome = await recipeDataProcessor.select_steps_that_use_ingredient(ingredient["name"])
            ingredient_sql_duration = Helpers.time_str_to_seconds(outcome[0]["time"])
            ingredient_sql_durations.append(ingredient_sql_duration)


            ingredient_parsing_start_time = time.time()
            
            for step in outcome[0]["result"]:
                step_id =  str(step["id"])
                step_normalized_ingredients[step_id].append(ingredient["id"])

                
            
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

            print(i,end="\r", flush=True)

            # print("coll_ingr-{counter}/{total_count}:{percent}\t\test_remaining:{est_time_remaining}\t\telapsed:{elapsed_duration}\t\tlast_duration:{this_method_duration}\t\tlast_sql_duration:{ingredient_sql_duration}\t\tlast_parse_duration:{ingredient_parsing_duration}\t\tavg_duration:{average_duration}\t\t-{row}\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t".format(
            #             counter = i,
            #             total_count = total_ingredients,
            #             percent = f"{percentage:.2%}",
            #             elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
            #             average_duration = f"{average_duration_ms:.3f} ms",
            #             this_method_duration = f"{ingredient_processing_duration_ms:.3f} ms",
            #             ingredient_sql_duration = f"{ingredient_sql_duration_ms:.3f} ms",
            #             ingredient_parsing_duration = f"{ingredient_parsing_duration_ms:.3f} ms",
            #             est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
            #             row = ingredient["name"]
            #             ), end="\r", flush=True) 
            

    print("Done parsing {0} ingredients".format(total_ingredients))
    i = 0
    N = len(step_normalized_ingredients)
    print("")
    print("")
    async with AsyncSurrealDB(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(db_constants.DB_PARAMS.username,db_constants.DB_PARAMS.password)
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)
        recipeDataProcessor = SurqlRecipesAndSteps(db)

        for key, value in step_normalized_ingredients.items():
            i += 1
            step_start_time = time.time()
            try:
                outcome = await recipeDataProcessor.update_step_normalized_ingredients(key,value)  
            
            except Exception as e:
                 await Helpers.logError(
                     [key,value],"update_step_norm_ing",e,out_folder
                 )
            
            current_time = time.time() 
            percentage = i/N

            elapsed_duration = current_time - start_time
            elapsed_duration_minutes = elapsed_duration/60
            average_duration = elapsed_duration / i if i else 0
            average_duration_ms = average_duration * 1000

            step_update_duration = current_time - step_start_time
            step_update_durations.append(step_update_duration)
            step_update_duration_ms = step_update_duration*1000


            est_time_remaining = average_duration * (N - i)
            est_time_remaining_minutes = est_time_remaining / 60

            str_to_format = "updating_steps-:{counter}/{total_count}:{percent}\t\test_remaining:{est_time_remaining}\t\ttelapsed:{elapsed_duration}\t\tlast_duration:{this_method_duration}\t\tavg_duration:{average_duration}\t\t-{row}\t\t-{value}"
            Helpers.print_update(str_to_format.format(
                        counter = i,
                        total_count = N,
                        percent = f"{percentage:.2%}",
                        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                        average_duration = f"{average_duration_ms:.3f} ms",
                        this_method_duration = f"{step_update_duration_ms:.3f} ms",
                        est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                        row = key,
                        value = len(value)
                        )) 
            
    
    current_time = time.time() 
    elapsed_duration = current_time - start_time
    elapsed_duration_minutes = elapsed_duration/60
    
    avg_ingredient_processing_duration = np.mean(ingredient_processing_durations)
    avg_ingredient_processing_duration_ms = avg_ingredient_processing_duration * 1000

    min_ingredient_processing_duration = np.min(ingredient_processing_durations)
    min_ingredient_processing_duration_ms = min_ingredient_processing_duration * 1000

    max_ingredient_processing_duration = np.max(ingredient_processing_durations)
    max_ingredient_processing_duration_ms = max_ingredient_processing_duration * 1000


    avg_step_update_duration = np.mean(step_update_durations)
    avg_step_update_duration_ms = avg_step_update_duration * 1000

    min_step_update_duration = np.min(step_update_durations)
    min_step_update_duration_ms = min_step_update_duration * 1000

    max_step_update_duration = np.max(step_update_durations)
    max_step_update_duration_ms = max_step_update_duration * 1000


    avg_ingredient_sql_duration = np.mean(ingredient_sql_durations)
    avg_ingredient_sql_duration_ms = avg_ingredient_sql_duration * 1000

    min_ingredient_sql_duration = np.min(ingredient_sql_durations)
    min_ingredient_sql_duration_ms = min_ingredient_sql_duration * 1000

    max_ingredient_sql_duration = np.max(ingredient_sql_durations)
    max_ingredient_sql_duration_ms = max_ingredient_sql_duration * 1000

    print(
        """       


        step 5a normalize step ingredients                                                                                                 
        total elapsed {elapsed_duration}                                                                                                         
        ingredient search (avg,min,max) ({avg_ingredient_processing_duration},{min_ingredient_processing_duration},{max_ingredient_processing_duration}) 
        ingredient search sql (avg,min,max) ({avg_ingredient_sql_duration},{min_ingredient_sql_duration},{max_ingredient_sql_duration}) 
        step update (avg,min,max) ({avg_step_update_duration},{min_step_update_duration},{max_step_update_duration})                                                       
        """.format(
        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
        avg_ingredient_processing_duration = f"{avg_ingredient_processing_duration_ms:.3f} ms",
        min_ingredient_processing_duration = f"{min_ingredient_processing_duration_ms:.3f} ms",
        max_ingredient_processing_duration = f"{max_ingredient_processing_duration_ms:.3f} ms",
        avg_step_update_duration = f"{avg_step_update_duration_ms:.3f} ms",
        min_step_update_duration = f"{min_step_update_duration_ms:.3f} ms",
        max_step_update_duration = f"{max_step_update_duration_ms:.3f} ms",
        avg_ingredient_sql_duration = f"{avg_ingredient_sql_duration_ms:.3f} ms",
        min_ingredient_sql_duration = f"{min_ingredient_sql_duration_ms:.3f} ms",
        max_ingredient_sql_duration = f"{max_ingredient_sql_duration_ms:.3f} ms"
        )) 




async def main():

    args_loader.print()
    await process_recipe_ingredient_normalization()


if __name__ == "__main__":
    asyncio.run(main())


    