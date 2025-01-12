import asyncio
from surrealdb import AsyncSurrealDB
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader
from recipe_data_surql_ddl import RecipeDataSurqlDDL
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel

db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
args_loader = RecipeArgsLoader("Process initial DDL",db_constants,embed_constants,recipe_constants)
args_loader.LoadArgs()



async def process_DDL():
    async with AsyncSurrealDB(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(db_constants.DB_PARAMS.username,db_constants.DB_PARAMS.password)
        outcome = await db.query(RecipeDataSurqlDDL.DDL_CREATE_NS.format(ns=db_constants.DB_PARAMS.namespace,db=db_constants.DB_PARAMS.database))
        await db.use(db_constants.DB_PARAMS.namespace,db_constants.DB_PARAMS.database)
        
        
        embedDataProcessor = SurqlEmbeddingModel(db)
        embed_dimensions = await embedDataProcessor.get_model_dimensions()
        # print(embed_dimensions)
        # print(RecipeDataSurqlDDL.DDL.format(embed_dimensions=embed_dimensions))
        

        outcome = await db.query(RecipeDataSurqlDDL.DDL.format(embed_dimensions=embed_dimensions))

    
    print(
        """ 
        Step 1 -- DDL    
        Complete 
        """)
    


async def main():
    
    print("""
          


          STEP 1 DDL
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

    await process_DDL()
   


if __name__ == "__main__":
    asyncio.run(main())


    