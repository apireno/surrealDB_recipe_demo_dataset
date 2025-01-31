import time
import asyncio
from surrealDB_embedding_model.embedding_model_ddl import EmbeddingModelDDL
from surrealDB_embedding_model.surql_embedding_model import SurqlEmbeddingModel
from surrealDB_embedding_model.embedding_model_constants import DatabaseConstants,THIS_FOLDER
from recipe_data_constants import RecipeDataConstants, ArgsLoader

out_folder = THIS_FOLDER + "/embeddings_{0}".format(time.strftime("%Y%m%d-%H%M%S"))
db_constants = DatabaseConstants()
recipe_constants = RecipeDataConstants()
args_loader = ArgsLoader("Input Embeddings Model",db_constants,recipe_constants)
args_loader.LoadArgs()

async def main():
    args_loader.print()
    
if __name__ == "__main__":
    asyncio.run(main())
