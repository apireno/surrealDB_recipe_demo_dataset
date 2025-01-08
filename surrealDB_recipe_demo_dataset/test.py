import asyncio
from surrealdb_embedding_model.embedding_model_constants import DatabaseConstants,EmbeddingModelConstants,THIS_FOLDER


async def main():
    print(THIS_FOLDER)
if __name__ == "__main__":
    asyncio.run(main())
