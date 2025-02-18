
import asyncio
from surrealdb import AsyncSurreal
import numpy as np
import time
from helpers import Helpers
from collections import defaultdict
from surrealdb import AsyncSurreal
from surrealDB_embedding_model.embedding_model_constants import DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, ArgsLoader,DATA_FOLDER
from surql_recipes_steps import SurqlRecipesAndSteps
from surql_ref_data import SurqlReferenceData

out_folder = THIS_FOLDER + "/logging/rec_ing_normal_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
recipe_constants = RecipeDataConstants()

Helpers.ensure_folders([out_folder])

ingredient_processing_durations = []
ingredient_parsing_durations = []
recipe_update_durations = []

async def process_recipe_ingredient_normalization():




    start_time = time.time()
    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)
        
        refDataProcessor =  SurqlReferenceData(db)
        list_ingredient_result = await refDataProcessor.select_all_ingredients()

        total_ingredients = len(list_ingredient_result)
        

        recipe_normalized_ingredients = defaultdict(list)
        #recipe_normalized_ingredients = {}
        i = 0
        for ingredient in list_ingredient_result:
            i += 1

            ingredient_start_time = time.time()

            recipeDataProcessor = SurqlRecipesAndSteps(db)

            outcome = await recipeDataProcessor.select_recipes_that_use_ingredient(ingredient["name"])
           

            ingredient_parsing_start_time = time.time()
            
            for recipe in outcome:
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

            

            est_time_remaining = average_duration * (total_ingredients - i)
            est_time_remaining_minutes = est_time_remaining / 60


            str_to_format = "collecting_ingredients-{counter}/{total_count}:{percent}\t\test_remaining:{est_time_remaining}\t\telapsed:{elapsed_duration}\t\tlast_duration:{this_method_duration}\t\tlast_parse_duration:{ingredient_parsing_duration}\t\tavg_duration:{average_duration}\t\t-{row}"
            Helpers.print_update(str_to_format.format(
                        counter = i,
                        total_count = total_ingredients,
                        percent = f"{percentage:.2%}",
                        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                        average_duration = f"{average_duration_ms:.3f} ms",
                        this_method_duration = f"{ingredient_processing_duration_ms:.3f} ms",
                        ingredient_parsing_duration = f"{ingredient_parsing_duration_ms:.3f} ms",
                        est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                        row = ingredient["name"]
                        )) 


    print("\n")

    i = 0
    N = len(recipe_normalized_ingredients)
    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)
        recipeDataProcessor = SurqlRecipesAndSteps(db)


        benchmark_log = out_folder + "/log.csv"
        with open(benchmark_log,"w") as log_file:
            log_file.write(
                    "counter,total_count,percent,est_time_remaining,elapsed,last_duration,avg_duration,row,val\n"
            )

                
            for key, value in recipe_normalized_ingredients.items():
                i += 1
                recipe_start_time = time.time()
                try:
                    outcome =  await recipeDataProcessor.update_recipe_normalized_ingredients(key,value) 
                
                except Exception as e:
                    await Helpers.logError(
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

                log_file.write(
                    "{counter},{total_count},{percent},{est_time_remaining},{elapsed_duration},{this_method_duration},{average_duration},{row},{value}\n".format(
                            counter = i,
                            total_count = N,
                            percent = f"{percentage:.2%}",
                            elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                            average_duration = f"{average_duration_ms:.3f} ms",
                            this_method_duration = f"{recipe_update_duration_ms:.3f} ms",
                            est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                            row = key,
                            value = len(value)
                            )
                )
                print("updating_recipes-{counter}/{total_count}:{percent}\t\test_remaining:{est_time_remaining}\t\telapsed:{elapsed_duration}\t\tlast_duration:{this_method_duration}\t\tavg_duration:{average_duration}\t\t-{row}\t\t-{value}\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t".format(
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



    

    
    print(
        """
        step 4 Recipe ingredient normalization                                                                                                    
        total elapsed {elapsed_duration}                                                                                                         
        ingredient_processing (avg,min,max) ({avg_ingredient_processing_duration},{min_ingredient_processing_duration},{max_ingredient_processing_duration})
        recipe_update (avg,min,max) ({avg_recipe_update_duration},{min_recipe_update_duration},{max_recipe_update_duration})                                                                                  
        """.format(
        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
        avg_ingredient_processing_duration = f"{avg_ingredient_processing_duration_ms:.3f} ms",
        min_ingredient_processing_duration = f"{min_ingredient_processing_duration_ms:.3f} ms",
        max_ingredient_processing_duration = f"{max_ingredient_processing_duration_ms:.3f} ms",
        avg_recipe_update_duration = f"{avg_recipe_update_duration_ms:.3f} ms",
        min_recipe_update_duration = f"{min_recipe_update_duration_ms:.3f} ms",
        max_recipe_update_duration = f"{max_recipe_update_duration_ms:.3f} ms"
        )) 



async def main():

    args_loader = ArgsLoader("STEP 4 - Recipe ingredient normalization",db_constants,recipe_constants)
    args_loader.LoadArgs()
    args_loader.print()
    await process_recipe_ingredient_normalization()


if __name__ == "__main__":
    asyncio.run(main())


    