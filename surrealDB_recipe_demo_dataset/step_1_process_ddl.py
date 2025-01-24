import asyncio
from surrealdb import AsyncSurrealDB
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader
from recipe_data_surql_ddl import RecipeDataSurqlDDL
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel

db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
args_loader = RecipeArgsLoader("Step 1 - Process initial DDL",db_constants,embed_constants,recipe_constants)
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
    args_loader.print()

    await process_DDL()
   


if __name__ == "__main__":
    asyncio.run(main())


    