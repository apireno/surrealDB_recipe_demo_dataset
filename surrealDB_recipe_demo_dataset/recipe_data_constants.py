
import argparse
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER,ArgsLoader

DATA_FOLDER = THIS_FOLDER + "data/"

class GeminiConstants():
    def __init__(self):
        self.GOOGLE_GENAI_API_KEY_ENV_VAR = "GOOGLE_GENAI_API_KEY"
        self.GEMINI_LLM_MODEL = "gemini-1.5-flash"
        self.API_SLEEP = 4
        self.RETRY_COUNT = 10
        self.COMPLETION_DELEMITER = "#XXXXXXCOMPLETEXXXXXX" 

    
    def AddArgs(self, parser:argparse.ArgumentParser):
        parser.add_argument("-gemk","--gemini_api_key_env_var", help="The environment variable for your Gemini API key (Default: {0})".format(self.GOOGLE_GENAI_API_KEY_ENV_VAR))
        parser.add_argument("-gemm","--gemini_model", help="The Gemini model to use (Default: {0})".format(self.GEMINI_LLM_MODEL))
        parser.add_argument("-gems","--gemini_api_sleep", help="Seconds to sleep between calls to prevent lockout (Default: {0})".format(self.API_SLEEP))
        
    
    def SetArgs(self,args:argparse.Namespace):
        if args.gemini_api_key_env_var:
            self.GOOGLE_GENAI_API_KEY_ENV_VAR = args.gemini_api_key_env_var
        if args.gemini_model:
            self.GEMINI_LLM_MODEL = args.gemini_model
        if args.gemini_api_sleep:
            self.API_SLEEP = args.gemini_api_sleep

class RecipeDataConstants():

    def __init__(self):
       
        self.EXTRACTED_INGREDIENTS_FILE = DATA_FOLDER + "extracted_ingredients_list.txt"
        self.MATCHED_INGREDIENTS_FILE = DATA_FOLDER + "extracted_ingredients_match_list.txt"
        self.EXTRACTED_COOKING_ACTIONS_FILE = DATA_FOLDER + "extracted_cooking_actions_list.txt"
        self.MATCHED_COOKING_ACTIONS_FILE = DATA_FOLDER + "extracted_cooking_actions_match_list.txt"


        #https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions
        self.RECIPE_FILE = DATA_FOLDER + "RAW_recipes.csv"
        self.REVIEW_FILE = DATA_FOLDER + "RAW_interactions.csv"
        
        self.RECIPE_SAMPLE_RATIO = 0.0001
        self.REVIEW_SAMPLE_RATIO = 1.0

    def AddArgs(self, parser:argparse.ArgumentParser):
        
        parser.add_argument("-ingf","--ingredients_file", help="Your master ingredients file (Default: {0})".format(self.EXTRACTED_INGREDIENTS_FILE))
        parser.add_argument("-ingm","--ingredients_match_file", help="Your ingredient similarity matches file (Default: {0})".format(self.MATCHED_INGREDIENTS_FILE))
        parser.add_argument("-caf","--cooking_actions_file", help="Your cooking actions  (Default: {0})".format(self.EXTRACTED_COOKING_ACTIONS_FILE))
        parser.add_argument("-cam","--cooking_actions_match_file", help="Your cooking actions similarity matches file  (Default: {0})".format(self.MATCHED_COOKING_ACTIONS_FILE))
        parser.add_argument("-recf","--recipes_file", help="Your file that contains the recipes from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions (Default: {0})".format(self.RECIPE_FILE))
        parser.add_argument("-revf","--reviews_file", help="Your file that contains the recipe reviews from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions (Default: {0})".format(self.REVIEW_FILE))
        parser.add_argument("-recsr", "--recipe_sample_ratio",  help="The sampling ratio for the recipes from 0-1 (Default: {0})".format(self.RECIPE_SAMPLE_RATIO) , type=float, default=self.RECIPE_SAMPLE_RATIO)
        parser.add_argument("-revsr", "--review_sample_ratio",  help="The sampling ratio for the reviews from 0-1 (Default: {0})".format(self.REVIEW_SAMPLE_RATIO) , type=float, default=self.REVIEW_SAMPLE_RATIO)
    
    def SetArgs(self,args:argparse.Namespace):
        if args.ingredients_file:
            self.EXTRACTED_INGREDIENTS_FILE = args.ingredients_file
        if args.ingredients_match_file:
            self.MATCHED_INGREDIENTS_FILE = args.ingredients_match_file
        if args.cooking_actions_file:
            self.EXTRACTED_COOKING_ACTIONS_FILE = args.cooking_actions_file
        if args.cooking_actions_match_file:
            self.MATCHED_COOKING_ACTIONS_FILE = args.cooking_actions_match_file
        if args.recipes_file:
            self.RECIPE_FILE = args.recipes_file
        if args.reviews_file:
            self.REVIEW_FILE = args.reviews_file
        if args.recipe_sample_ratio:
            self.RECIPE_SAMPLE_RATIO = args.recipe_sample_ratio
        if args.review_sample_ratio:
            self.REVIEW_SAMPLE_RATIO = args.review_sample_ratio


class RecipeArgsLoader(ArgsLoader):
        
    def __init__(self,description,
            db_constants: DatabaseConstants,
            embed_constants: EmbeddingModelConstants,
            recipe_data_constants: RecipeDataConstants,
            gemini_data_constants: GeminiConstants = None):
        
        super().__init__(description,db_constants,embed_constants)
        self.recipe_data_constants = recipe_data_constants
        self.recipe_data_constants.AddArgs(self.parser)
        self.gemini_data_constants = gemini_data_constants
        if self.gemini_data_constants != None:
            self.gemini_data_constants.AddArgs(self.parser)


    def LoadArgs(self):
        
        super().LoadArgs()

        self.recipe_data_constants.SetArgs(self.args)
        if self.gemini_data_constants != None:
            self.gemini_data_constants.SetArgs(self.args)

        
        #for developing edit the settings here to avoid using CLI
        self.db_constants.DB_PARAMS.url = "ws://0.0.0.0:8080"
        self.db_constants.DB_PARAMS.namespace = "embedding_example"
        self.db_constants.DB_PARAMS.database = "embedding_example"
        self.recipe_data_constants.RECIPE_SAMPLE_RATIO = 0.001




    def print(self):
        # self.gemini_data_constants.GOOGLE_GENAI_API_KEY_ENV_VAR = "GOOGLE_GENAI_API_KEY"
        # self.gemini_data_constants.GEMINI_LLM_MODEL = "gemini-1.5-flash"
        # self.gemini_data_constants.API_SLEEP = 4
        # self.gemini_data_constants.RETRY_COUNT = 10
        # self.gemini_data_constants.COMPLETION_DELEMITER = "#XXXXXXCOMPLETEXXXXXX" 


        print("""
          {description}
          ---------------
          DB_PARAMS {URL} N: {NS} DB: {DB} USER: {DB_USER}

          DB_USER_ENV_VAR {DB_USER_ENV_VAR}
          DB_PASS_ENV_VAR {DB_PASS_ENV_VAR}

          MODEL_PATH {MODEL_PATH}

          RECIPE_FILE {RECIPE_FILE}
          REVIEW_FILE {REVIEW_FILE}

          EXTRACTED_INGREDIENTS_FILE {EXTRACTED_INGREDIENTS_FILE}
          MATCHED_INGREDIENTS_FILE {MATCHED_INGREDIENTS_FILE}
          EXTRACTED_COOKING_ACTIONS_FILE {EXTRACTED_COOKING_ACTIONS_FILE}
          MATCHED_COOKING_ACTIONS_FILE {MATCHED_COOKING_ACTIONS_FILE}

          RECIPE_SAMPLE_RATIO {RECIPE_SAMPLE_RATIO}
          REVIEW_SAMPLE_RATIO {REVIEW_SAMPLE_RATIO}

          """.format(
              description = self.parser.description,
              URL = self.db_constants.DB_PARAMS.url,
              DB_USER = self.db_constants.DB_PARAMS.username,
              NS = self.db_constants.DB_PARAMS.namespace,
              DB = self.db_constants.DB_PARAMS.database,
              DB_USER_ENV_VAR = self.db_constants.DB_USER_ENV_VAR,
              DB_PASS_ENV_VAR = self.db_constants.DB_PASS_ENV_VAR,
              MODEL_PATH = self.embed_constants.MODEL_PATH,
              RECIPE_FILE = self.recipe_data_constants.RECIPE_FILE,
              REVIEW_FILE = self.recipe_data_constants.REVIEW_FILE,
              EXTRACTED_INGREDIENTS_FILE = self.recipe_data_constants.EXTRACTED_INGREDIENTS_FILE,
              MATCHED_INGREDIENTS_FILE = self.recipe_data_constants.MATCHED_INGREDIENTS_FILE,
              EXTRACTED_COOKING_ACTIONS_FILE =  self.recipe_data_constants.EXTRACTED_COOKING_ACTIONS_FILE,
              MATCHED_COOKING_ACTIONS_FILE = self.recipe_data_constants.MATCHED_COOKING_ACTIONS_FILE,
              RECIPE_SAMPLE_RATIO = self.recipe_data_constants.RECIPE_SAMPLE_RATIO,
              REVIEW_SAMPLE_RATIO = self.recipe_data_constants.REVIEW_SAMPLE_RATIO

            )
          )


    



