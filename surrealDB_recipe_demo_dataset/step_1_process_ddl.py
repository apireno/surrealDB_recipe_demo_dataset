import asyncio
from surrealdb import AsyncSurreal
from surrealDB_embedding_model.embedding_model_constants import DatabaseConstants
from recipe_data_constants import RecipeDataConstants, ArgsLoader
from recipe_data_surql_ddl import RecipeDataSurqlDDL
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel
from surrealDB_embedding_model.database import Database

db_constants = DatabaseConstants()
recipe_constants = RecipeDataConstants()

async def process_DDL():
    async with AsyncSurreal(db_constants.DB_PARAMS.url) as db:
        auth_token = await db.signin({"username":db_constants.DB_PARAMS.username,"password":db_constants.DB_PARAMS.password})
        outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL_CREATE_NS.format(ns=db_constants.DB_PARAMS.namespace,db=db_constants.DB_PARAMS.database)))
        await db.use(db_constants.DB_PARAMS.namespace,db_constants.DB_PARAMS.database)
        
        
        embedDataProcessor = SurqlEmbeddingModel(db)
        embed_dimensions = await embedDataProcessor.get_model_dimensions()
        # print(embed_dimensions)
        # print(RecipeDataSurqlDDL.DDL.format(embed_dimensions=embed_dimensions))
        

        outcome = Database.ParseResponseForErrors(await db.query_raw(RecipeDataSurqlDDL.DDL.format(embed_dimensions=embed_dimensions)))

    
    print(
        """ 
        Step 1 -- DDL    
        Complete 
        """)
    


async def main():
    args_loader = ArgsLoader("Step 1 - Process initial DDL",db_constants,recipe_constants)
    args_loader.LoadArgs()
    args_loader.print()

    await process_DDL()
   


if __name__ == "__main__":
    asyncio.run(main())


    