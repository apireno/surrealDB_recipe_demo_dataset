# surrealDB_recipe_demo_dataset

This repository contains a series of scripts to upload a demo dataset scraped from food.com into a SurrealDB database. The purpose of these scripts is to facilitate the exploration of various database concepts in SurrealDB, such as **graph relationships**, **vector embeddings**, and **full-text search capabilities**. This project builds on the foundations of the `surrealDB_Embedding_Model` repository, utilizing similar code for data processing and database interaction.

## Overview

This project provides a way to load recipe and review data, pre-processed and ready to be used in SurrealDB. This setup is ideal for testing the many features of SurrealDB, like:

*   **Graph Queries:** Explore relationships between recipes, ingredients, and reviews.
*   **Vector Search:** Use pre-computed embeddings for similarity searches between recipes or ingredients.
*   **Full-Text Search:** Search the recipe text and reviews.

## Getting Started

Follow these steps to load the data into your SurrealDB instance:

### Prerequisites

1.  **Python 3.6+**: Ensure you have Python 3.6 or higher installed.
2.  **SurrealDB**: You need a SurrealDB instance, either running locally or on the cloud. See the official documentation for installation instructions or use the cloud option:
    *   Local Install: [https://surrealdb.com/docs/surrealdb/introduction/start](https://surrealdb.com/docs/surrealdb/introduction/start)
    *   Surreal Cloud: [https://surrealdb.com/cloud](https://surrealdb.com/cloud)

### Steps

1.  **Download an embedding model**:
    *   Download a pre-trained embedding model, such as the **GloVe model**, from:
        *   [https://nlp.stanford.edu/projects/glove/](https://nlp.stanford.edu/projects/glove/)
        *  Or download the specific version from [https://www.kaggle.com/datasets/watts2/glove6b50dtxt](https://www.kaggle.com/datasets/watts2/glove6b50dtxt) which is the `glove.6B.50d.txt` file.
    *   The scripts use this model to generate vector embeddings for ingredients and other text data in the dataset. This step is similar to how the `surrealDB_Embedding_Model` repo uses it.
2.  **Download the recipe data**: Download the dataset from [https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions). The scripts expect this data to be in the data directory.
3.  **Set up your SurrealDB database**: Either install a local instance of SurrealDB or use Surreal Cloud.
4.  **Environment Variables**: Ensure your SurrealDB credentials are set as environment variables.
5.  **Ensure the embedding module depedency is installed**: 
    * execute `bash setup.sh` in the root of where you downloaded this repo which will set up your venv and execute `pip install -r reqirements.txt` 
    * you can run `test_dependencies.py` to confirm all dependencies were properly installed
    * remeber to activate your venv before running scripts
5.  **CLI args and constants file `surrealDB_recipe_demo_dataset/recipe_data_constants.py`**:
    * CLI options:
      * -h, --help            show this help message and exit
      * -url URL, --url URL   Path to your SurrealDB instance (Default: ws://0.0.0.0:8000)
      * -ns NAMESPACE, --namespace NAMESPACE
                        SurrealDB namespace to create and install the data (Default: embedding_example)
      * -db DATABASE, --database DATABASE
                        SurrealDB database to create and install the data (Default: embedding_example)
      * -mp MODEL_PATH, --model_path MODEL_PATH
                        Your embeddings model file (Default: .//glove.6B.50d.txt)
      * -ingf INGREDIENTS_FILE, --ingredients_file INGREDIENTS_FILE
                        Your master ingredients file (Default: .//extracted_ingredients_list.txt)
      * -recf RECIPES_FILE, --recipes_file RECIPES_FILE
                        Your file that contains the recipes from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-
                        interactions (Default: .//RAW_recipes.csv)
      * -revf REVIEWS_FILE, --reviews_file REVIEWS_FILE
                        Your file that contains the recipe reviews from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-
                        user-interactions (Default: .//RAW_interactions.csv)
      * -uenv USER_ENV, --user_env USER_ENV
                        Your environment variable for db username (Default: SURREAL_CLOUD_TEST_USER)
      * -penv PASS_ENV, --pass_env PASS_ENV
                        Your environment variable for db password (Default: SURREAL_CLOUD_TEST_PASS)
      * -recsr RECIPE_SAMPLE_RATIO, --recipe_sample_ratio RECIPE_SAMPLE_RATIO
                        The sampling ratio for the recipes from 0-1 (Default: 0.001)
      * -revsr REVIEW_SAMPLE_RATIO, --review_sample_ratio REVIEW_SAMPLE_RATIO
                        The sampling ratio for the reviews from 0-1 (Default: 1.0)
    *   If you are running from an IDE, edit the `recipe_data_constants.py` file to alter any settings there if more convenient.
6.  **Run the embedding script**: If your target database doesn't have the embedding model loaded already run `src/surrealdb-embedding-model/upload_model.py`
7.  **Optional**: The enriched relationships between ingredients and cooking actions are already provided in the data folder. If you want to re-generate them using Gemini execute the Python scripts sequentially, from step 0_1 through 0_4
8.  **Run the scripts in order**: Execute the Python scripts sequentially, from step 1 through 6
    *   `step_1_process_ddl.py`: Creates all the database schema definitions for all the data to be ingested.
    *   `step_2_process_input_ingredients_and_actions.py`: Ingests the ingredient data into SurrealDB.
    *   `step_3_process_input_recipes.py`: Ingests the recipe data into SurrealDB.
    *   `step_4_process_recipe_ingredient_normalization.py`: Creates an array of ingredients for the recipes that are records of type ingredient loaded in step 2 using text-search.
    *   `step_5a_process_step_ingredient_normalization.py`: Creates an array of ingredients for the steps that are records of type ingredient loaded in step 2 using text-search.
    *   `step_5b_process_step_action_extraction.py`: Creates an array of cooking actions that are records of type cooking_action loaded in step 2 using text-search.
    *   `step_6_process_input_reviews.py`: Ingests the reviewers and review data into SurrealDB.
    * Each of these is implemented as a python script which can be run separately.


## Dataset and Research Citation

The recipe and review data is sourced from the Food.com dataset on Kaggle:

*   **Dataset:** [https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions)

This dataset was created for the following research:

*   **Citation:** Shuyang Li, Chris Callison-Burch, and Benjamin Van Durme. 2019. [From Recipes to Actions: Generating Procedural Text from Web Data](https://aclanthology.org/D19-1613/). In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, pages 6083–6093, Hong Kong, China. Association for Computational Linguistics.

## Code Similarities
This repository reuses a lot of the code from the `surrealDB_Embedding_Model` repository. Specifically the following modules:
    * constants.py
    * database.py
    * embeddings.py
    * helpers.py
    * surql_ddl.py
    * surql_embedding_model.py
