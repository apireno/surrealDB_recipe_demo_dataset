from setuptools import setup, find_packages


setup(
    name="surrealdb_recipe_demo_dataset",
    version="0.1.0",
    packages=find_packages(),  # Use find_packages() to automatically find packages
    install_requires=[
        "surrealdb",
        "torch",
        "surrealdb_embedding_model @ git+https://github.com/apireno/surrealDB_Embedding_Model.git"
    ]
)