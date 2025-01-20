import time
import asyncio
from surrealDB_embedding_model.embedding_model_ddl import EmbeddingModelDDL
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER,ArgsLoader
from surrealDB_embedding_model.embeddings import EmbeddingModel
from recipe_data_constants import RecipeDataConstants, RecipeArgsLoader

out_folder = THIS_FOLDER + "/embeddings_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
embed_constants = EmbeddingModelConstants()
recipe_constants = RecipeDataConstants()
args_loader = RecipeArgsLoader("Input Embeddings Model",db_constants,embed_constants,recipe_constants)
args_loader.LoadArgs()

async def main():
    
    print("""
          STEP 0
          DB_PARAMS {URL} N: {NS} DB: {DB} USER: {DB_USER}

          DB_USER_ENV_VAR {DB_USER_ENV_VAR}
          DB_PASS_ENV_VAR {DB_PASS_ENV_VAR}

          MODEL_PATH {MODEL_PATH}

          RECIPE_FILE {RECIPE_FILE}
          REVIEW_FILE {REVIEW_FILE}

          EXTRACTED_INGREDIENTS_FILE {EXTRACTED_INGREDIENTS_FILE}

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
              EXTRACTED_INGREDIENTS_FILE = recipe_constants.EXTRACTED_INGREDIENTS_FILE,
              RECIPE_SAMPLE_RATIO = recipe_constants.RECIPE_SAMPLE_RATIO,
              REVIEW_SAMPLE_RATIO = recipe_constants.REVIEW_SAMPLE_RATIO

          )
          )
    
if __name__ == "__main__":
    asyncio.run(main())
