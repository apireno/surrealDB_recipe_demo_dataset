from database import *
import asyncio
from surrealdb import AsyncSurrealDB
from surql_ddl import SurqlDDL
from constants import Constants

constants = Constants()
constants.LoadArgs("Process initial DDL")

async def process_DDL():
    async with AsyncSurrealDB(constants.DB_PARAMS.url) as db:
        auth_token = await db.sign_in(constants.DB_PARAMS.username,constants.DB_PARAMS.password)
        outcome = await db.query(SurqlDDL.DDL_CREATE_NS.format(ns=constants.DB_PARAMS.namespace,db=constants.DB_PARAMS.database))
        await db.use(constants.DB_PARAMS.namespace,constants.DB_PARAMS.database)
        outcome = await db.query(SurqlDDL.DDL)

    
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
    
    await process_DDL()
   


if __name__ == "__main__":
    asyncio.run(main())


    