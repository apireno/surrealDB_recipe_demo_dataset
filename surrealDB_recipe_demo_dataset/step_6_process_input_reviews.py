
import asyncio
from surrealdb import AsyncSurrealDB
import pandas as pd
import numpy as np
import time
import names
from datetime import datetime,timedelta
from surrealdb import AsyncSurrealDB
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader
from surql_recipes_steps import SurqlRecipesAndSteps
from surql_reviews import SurqlReviewsAndReviewers
from recipe_data_surql_ddl import RecipeDataSurqlDDL



out_folder = THIS_FOLDER + "/process_reviews_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
args_loader = RecipeArgsLoader("Input reviews",db_constants,embed_constants,recipe_constants)
args_loader.LoadArgs()


reviewer_insert_durations = []
review_insert_durations = []


async def process_reviewers(dataProcessor:SurqlReviewsAndReviewers,reviewer_ids):

    start_time = time.time()

    i = 0
    total_reviews = len(reviewer_ids)
    for reviewer_id in reviewer_ids:
        i += 1
        percentage = i/total_reviews
        reviewer_insert_start_time =  time.time()
        review_name = names.get_full_name()
        out = await dataProcessor.insert_reviewer(reviewer_id,review_name)


        current_time = time.time()
        elapsed_duration = current_time - start_time
        elapsed_duration_minutes = elapsed_duration/60
        average_duration = elapsed_duration / i if i else 0
        average_duration_ms = average_duration * 1000


        reviewer_insert_duration = current_time - reviewer_insert_start_time
        reviewer_insert_duration_ms = reviewer_insert_duration * 1000

        reviewer_insert_durations.append(reviewer_insert_duration)

        est_time_remaining = average_duration * (total_reviews - i)
        est_time_remaining_minutes = est_time_remaining / 60
            
        print("inserting_reviewers-{counter}/{total_count}\t{percent}\test_remaining\t{est_time_remaining}\telapsed\t{elapsed_duration}\tlast_duration\t{this_method_duration}\tavg_duration\t{average_duration}\t-{row}-\t{name}\t\t\t\t\t\t\t\t\t\t\t".format(
                    counter = i,
                    total_count = total_reviews,
                    percent = f"{percentage:.2%}",
                    elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                    average_duration = f"{average_duration_ms:.3f} ms",
                    this_method_duration = f"{reviewer_insert_duration_ms:.3f} ms",
                    est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                    row = reviewer_id,
                    name = review_name
                    ), end="\r", flush=True) 
        
        

async def process_review(dataProcessor:SurqlReviewsAndReviewers,row,counter,total_count,start_time):
    percentage = counter/total_count

    review_insert_start_time =  time.time()

    #try:
    out = await dataProcessor.insert_review(
                        row.user_id,
                        row.recipe_id,
                            (datetime.strptime(row.date, "%Y-%m-%d") + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        row.rating,
                        row.review )
    

    current_time = time.time()
    elapsed_duration = current_time - start_time
    elapsed_duration_minutes = elapsed_duration/60
    average_duration = elapsed_duration / counter if counter else 0
    average_duration_ms = average_duration * 1000


    review_insert_duration = current_time - review_insert_start_time
    review_insert_duration_ms = review_insert_duration * 1000

    review_insert_durations.append(review_insert_duration)

    est_time_remaining = average_duration * (total_count - counter)
    est_time_remaining_minutes = est_time_remaining / 60

    print("inserting_review-{counter}/{total_count}\t{percent}\test_remaining\t{est_time_remaining}\telapsed\t{elapsed_duration}\tlast_duration\t{this_method_duration}\tavg_duration\t{average_duration}\t-{row}-\t{name}\t\t\t\t\t\t\t\t\t\t\t".format(
                counter = counter,
                total_count = total_count,
                percent = f"{percentage:.2%}",
                elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
                average_duration = f"{average_duration_ms:.3f} ms",
                this_method_duration = f"{review_insert_duration_ms:.3f} ms",
                est_time_remaining = f"{est_time_remaining_minutes:.1f} min",
                row = row.recipe_id,
                name = row.user_id
                ), end="\r", flush=True)
    

    # except Exception as e:
    #     #logging.error(e)
    #     await logErrorRow(row,"review",e,out_folder)
        



async def process_reviews(review_df,batch_size=1,total_records=0,offset=0):
    if total_records==0 :
        total_records = len(review_df)

    
    start_time = time.time()



    async with AsyncSurrealDB(db_constants.DB_PARAMS.url) as db:

        auth_token = await db.sign_in(db_constants.DB_PARAMS.username,db_constants.DB_PARAMS.password)
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)


        dataProcessor = SurqlReviewsAndReviewers(db)

        for i in range(offset, total_records, batch_size):
            
            batch = review_df[i : i + batch_size].itertuples()
            tasks = [process_review(dataProcessor,row,i,total_records,start_time) for row in batch]
            await asyncio.gather(*tasks)


        




async def main():


    print("""
          

          
          STEP 6 import reviews
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

    review_df = pd.read_csv(recipe_constants.REVIEW_FILE)


    async with AsyncSurrealDB(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(db_constants.DB_PARAMS.username,db_constants.DB_PARAMS.password)
        await db.use(db_constants.DB_PARAMS.namespace, db_constants.DB_PARAMS.database)

        out = await db.query(RecipeDataSurqlDDL.DDL_REVIEWER)
        out = await db.query(RecipeDataSurqlDDL.DDL_REVIEW)
        
        recipeDataProcessor = SurqlRecipesAndSteps(db)
        reviewDataProcessor = SurqlReviewsAndReviewers(db)

        list_recipe_result = await recipeDataProcessor.select_all_recipe_ids()
        recipes = list_recipe_result[0]["result"]
        recipe_ids = [recipe["id"].id for recipe in recipes]
        review_df = review_df[review_df['recipe_id'].isin(recipe_ids)]
        reviewer_ids = review_df['user_id'].unique().tolist() 
        await process_reviewers(reviewDataProcessor,reviewer_ids)
    
    #sample 
    review_df = review_df.sample(frac=recipe_constants.REVIEW_SAMPLE_RATIO, random_state=1)
    print(review_df.describe())
    print(review_df.head())

    total_records = len(review_df)
    start_time = time.time()
    await process_reviews(review_df)


    current_time = time.time() 
    elapsed_duration = current_time - start_time
    elapsed_duration_minutes = elapsed_duration/60

    avg_review_insert_duration = np.mean(review_insert_durations)
    avg_review_insert_duration_ms = avg_review_insert_duration * 1000

    min_review_insert_duration = np.min(review_insert_durations)
    min_review_insert_duration_ms = min_review_insert_duration * 1000

    max_review_insert_duration = np.max(review_insert_durations)
    max_review_insert_duration_ms = max_review_insert_duration * 1000

    avg_reviewer_insert_duration = np.mean(reviewer_insert_durations)
    avg_reviewer_insert_duration_ms = avg_reviewer_insert_duration * 1000

    min_reviewer_insert_duration = np.min(reviewer_insert_durations)
    min_reviewer_insert_duration_ms = min_reviewer_insert_duration * 1000

    max_reviewer_insert_duration = np.max(reviewer_insert_durations)
    max_reviewer_insert_duration_ms = max_reviewer_insert_duration * 1000

    print(
        """        
        step 6 insert reviewers and reviews                                                                                                
        total elapsed {elapsed_duration}                                                                                                         
        {N1} reviewers (avg,min,max) ({avg_reviewer_insert_duration},{min_reviewer_insert_duration},{max_reviewer_insert_duration}) 
        {N2} reviews (avg,min,max) ({avg_review_insert_duration},{min_review_insert_duration},{max_review_insert_duration})                                                                                    
        """.format(
        elapsed_duration = f"{elapsed_duration_minutes:.1f} min",
        avg_reviewer_insert_duration = f"{avg_reviewer_insert_duration_ms:.3f} ms",
        min_reviewer_insert_duration = f"{min_reviewer_insert_duration_ms:.3f} ms",
        max_reviewer_insert_duration = f"{max_reviewer_insert_duration_ms:.3f} ms",
        avg_review_insert_duration = f"{avg_review_insert_duration_ms:.3f} ms",
        min_review_insert_duration = f"{min_review_insert_duration_ms:.3f} ms",
        max_review_insert_duration = f"{max_review_insert_duration_ms:.3f} ms",
        N1 = len(reviewer_ids),
        N2 = total_records
        )) 




if __name__ == "__main__":
    asyncio.run(main())


    