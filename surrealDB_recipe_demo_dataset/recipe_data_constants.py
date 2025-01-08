
import argparse
import os
from surrealDB_embedding_model.database import Database
from surrealDB_embedding_model.embedding_model_constants import EmbeddingModelConstants,DatabaseConstants,THIS_FOLDER,ArgsLoader

class RecipeDataConstants():
    THIS_FOLDER = "./"

    def __init__(self):
       
        self.PREV_EXTRACTED_INGREDIENTS_FILE = THIS_FOLDER + "data/extracted_ingredients_list.txt"


        #https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions
        self.RECIPE_FILE = THIS_FOLDER + "data/RAW_recipes.csv"
        self.REVIEW_FILE = THIS_FOLDER + "data/RAW_interactions.csv"
        
        self.RECIPE_SAMPLE_RATIO = 0.0001
        self.REVIEW_SAMPLE_RATIO = 1.0

    def AddArgs(self, parser:argparse.ArgumentParser):
        
        parser.add_argument("-ingf","--ingredients_file", help="Your master ingredients file (Default: {0})".format(self.PREV_EXTRACTED_INGREDIENTS_FILE))
        parser.add_argument("-recf","--recipes_file", help="Your file that contains the recipes from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions (Default: {0})".format(self.RECIPE_FILE))
        parser.add_argument("-revf","--reviews_file", help="Your file that contains the recipe reviews from https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions (Default: {0})".format(self.REVIEW_FILE))
        parser.add_argument("-recsr", "--recipe_sample_ratio",  help="The sampling ratio for the recipes from 0-1 (Default: {0})".format(self.RECIPE_SAMPLE_RATIO) , type=float, default=self.RECIPE_SAMPLE_RATIO)
        parser.add_argument("-revsr", "--review_sample_ratio",  help="The sampling ratio for the reviews from 0-1 (Default: {0})".format(self.REVIEW_SAMPLE_RATIO) , type=float, default=self.REVIEW_SAMPLE_RATIO)
    
    def SetArgs(self,args:argparse.Namespace):
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


class RecipeArgsLoader(ArgsLoader):
        
    def __init__(self,description,
            db_constants: DatabaseConstants,
            embed_constants: EmbeddingModelConstants,
            recipe_data_constants: RecipeDataConstants):
        
        super().__init__(description,db_constants,embed_constants)
        self.recipe_data_constants = recipe_data_constants
        self.recipe_data_constants.AddArgs(self.parser)
        #for developing edit the settings here to avoid using CLI
        #self.db_constants.DB_PARAMS.url = "ws://0.0.0.0:8080"
        #self.db_constants.DB_PARAMS.database = "test2"

    def LoadArgs(self):
        
        super().LoadArgs()

        self.recipe_data_constants.SetArgs(self.args)


    



