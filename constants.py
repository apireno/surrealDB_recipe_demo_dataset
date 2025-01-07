
import argparse
import os
from database import Database

class Constants():
    THIS_FOLDER = "./"

    def __init__(self):
       

        #export SURREAL_CLOUD_TEST_USER=xxx
        #export SURREAL_CLOUD_TEST_PASS=xxx

        self.DB_USER_ENV_VAR = "SURREAL_CLOUD_TEST_USER"
        self.DB_PASS_ENV_VAR = "SURREAL_CLOUD_TEST_PASS"
        
        
        #The path to your SurrealDB instance
        #The the SurrealDB namespace and database to upload the model to
        self.DB_PARAMS = Database(
            #"wss://test-med-069pe77i4lv4j3mhm6bc7t5u9g.aws-use1.surreal.cloud",
            #"wss://test-4xl-069pe79vptv4jcpim0vdloso0o.aws-use1.surreal.cloud",
            "ws://0.0.0.0:8080",
            os.getenv(self.DB_USER_ENV_VAR),
            os.getenv(self.DB_PASS_ENV_VAR),
            "embedding_example",
            "embedding_example")
                    
        


        #For use in authenticating your database in database.py
        #These are just the pointers to the environment variables
        #Don't put the actual passwords here




        
        #You must download a model in the format of:
        # word v1 v2 v3 ... vN
        #here is an example
        #https://www.kaggle.com/datasets/watts2/glove6b50dtxt
        self.MODEL_PATH = Constants.THIS_FOLDER + "/glove.6B.50d.txt"
        self.PREV_EXTRACTED_INGREDIENTS_FILE = Constants.THIS_FOLDER + "/extracted_ingredients_list.txt"



        #https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions
        self.RECIPE_FILE = Constants.THIS_FOLDER + "/RAW_recipes.csv"
        self.REVIEW_FILE = Constants.THIS_FOLDER + "/RAW_interactions.csv"
        
        self.RECIPE_SAMPLE_RATIO = 0.001
        self.REVIEW_SAMPLE_RATIO = 1.0

    def LoadArgs(self,description):

        parser = argparse.ArgumentParser(description=description)
        parser.add_argument("-url","--url", help="Path to your SurrealDB instance (Default: {0})".format(self.DB_PARAMS.url))
        parser.add_argument("-ns","--namespace", help="SurrealDB namespace to create and install the model (Default: {0})".format(self.DB_PARAMS.namespace))
        parser.add_argument("-db","--database", help="SurrealDB database to create and install the model (Default: {0})".format(self.DB_PARAMS.database))
        parser.add_argument("-mp","--model_path", help="Your model file (Default: {0})".format(self.MODEL_PATH))
        parser.add_argument("-ingf","--ingredients_file", help="Your master ingredients file (Default: {0})".format(self.PREV_EXTRACTED_INGREDIENTS_FILE))
        parser.add_argument("-recf","--recipes_file", help="Your file that contains the recipes from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions (Default: {0})".format(self.RECIPE_FILE))
        parser.add_argument("-revf","--reviews_file", help="Your file that contains the recipe reviews from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions (Default: {0})".format(self.REVIEW_FILE))
        parser.add_argument("-uenv","--user_env", help="Your environment variable for db username (Default: {0})".format(self.DB_USER_ENV_VAR))
        parser.add_argument("-penv","--pass_env", help="Your environment variable for db password (Default: {0})".format(self.DB_PASS_ENV_VAR))
        parser.add_argument("-recsr", "--recipe_sample_ratio",  help="The sampling ratio for the recipes from 0-1 (Default: {0})".format(self.RECIPE_SAMPLE_RATIO) , type=float, default=self.RECIPE_SAMPLE_RATIO)
        parser.add_argument("-revsr", "--review_sample_ratio",  help="The sampling ratio for the reviews from 0-1 (Default: {0})".format(self.REVIEW_SAMPLE_RATIO) , type=float, default=self.REVIEW_SAMPLE_RATIO)


        
        args = parser.parse_args()

        if args.url:
            self.DB_PARAMS.url = args.url
        if args.namespace:
            self.DB_PARAMS.namespace = args.namespace
        if args.database:
            self.DB_PARAMS.database = args.database
        if args.model_path:
            self.MODEL_PATH = args.model_path
        if args.user_env:
            self.DB_USER_ENV_VAR = args.user_env
            self.DB_PARAMS.username = os.getenv(self.DB_USER_ENV_VAR)
        if args.pass_env:
            self.DB_PASS_ENV_VAR = args.pass_env
            self.DB_PARAMS.password = os.getenv(self.DB_PASS_ENV_VAR)
        if args.ingredients_file:
            self.PREV_EXTRACTED_INGREDIENTS_FILE = args.ingredients_file
        if args.recipes_file:
            self.RECIPE_FILE = args.recipes_file
        if args.reviews_file:
            self.REVIEW_FILE = args.reviews_file
        if args.recipe_sample_ratio:
            self.RECIPE_SAMPLE_RATIO = args.recipe_sample_ratio
        if args.review_sample_ratio:
            self.REVIEW_SAMPLE_RATIO = args.review_sample_ratio

        

    



