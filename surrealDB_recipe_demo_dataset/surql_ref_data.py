from surrealDB_embedding_model.embeddings import EmbeddingModel
from surrealdb import AsyncSurrealDB

class SurqlReferenceData:
  

  COOKING_ACTIONS = {
    "prepare": {
      "cut": [
        "chiffonade", "julienne", "dice", "mince", "chop", "slice", "grind", "crush", "mash", "puree"
      ],
      "combine": [
        "add", "mix", "fold", "blend", "stir"
      ],
      "separate": [
        "strain", "drain", "sift", "skim", "degrease", "filter", "separate", "divide", "split", "remove", "discard", "shell", "shuck", "deseed", "skin", "peel", "pare", "gut", "zest" 
      ],
      "apply": [
        "spread", "brush", "drizzle", "sprinkle", "coat", "dust", "rub", "stuff", "fill", "inject", "pack", "glaze", "baste", "pipe", "lard", "roll"
      ],
      "measure": [
        "measure", "weigh", "level"
      ],
      "other": [
        "acidulate", "brine", "marinate", "tenderize", "score", "butterfly", "spatchcock", "truss", "tie", "trim", "french", "debone" 
      ]
    },
    "cook": {
      "dry heat": [
        "bake", "roast", "broil", "fry", "pan fry", "sauté", "sear", "deep fry", "stir fry", "grill", "smoke", "char", "toast", "brown", "caramelize"
      ],
      "moist heat": [
        "blanch", "boil", "braise", "poach", "simmer", "sous vide", "steam", "stew", "pressure cook", "reduce"
      ],
      "other": [
        "microwave", "reheat", "defrost", "confit"
      ]
    },
    "finish": {
      "serve": [
        "garnish", "plate", "serve"
      ],
      "preserve": [
        "preserve", "can", "pickle", "cure", "freeze", "dry", "smoke", "dehydrate" 
      ],
      "other": [
        "test", "check", "season", "adjust", "thicken", "thin", "sweeten", "deglaze", "rest", "sanitize", "wipe", "clean" 
      ]
    }
  }



  INSERT_COOKING_ACTION = """

  LET $parent_object = type::thing("cooking_action",$parent);
  LET $this_object = type::thing("cooking_action",$action);

  UPSERT $this_object  CONTENT {{
      name : $action,
      action_embedding:  $action_embedding
      }};
  RELATE $this_object ->action_is_type_of-> $parent_object;

  """
  
  INSERT_COOKING_ACTION_CALC_EMBEDDING = """

  LET $parent_object = type::thing("cooking_action",$parent);
  LET $this_object = type::thing("cooking_action",$action);
  LET $action_embedding = fn::sentence_to_vector($action);

  UPSERT $this_object  CONTENT {{
      name : $action,
      action_embedding:  $action_embedding
      }};
  RELATE $this_object ->action_is_type_of-> $parent_object;

  """

  INSERT_INGREDIENT = """
  LET $this_object = type::thing("ingredient",$ingredient);
  UPSERT $this_object CONTENT {{
      name : $ingredient,
      ingredient_embedding:  $ingredient_embedding
      }};
  """

  INSERT_INGREDIENT_CALC_EMBEDDING = """
  LET $this_object = type::thing("ingredient",$ingredient);
  LET $ingredient_embedding = fn::sentence_to_vector($ingredient);
  
  UPSERT $this_object CONTENT {{
      name : $ingredient,
      ingredient_embedding:  $ingredient_embedding
      }};
  """

  SELECT_ALL_INGREDIENTS = """
  SELECT id,name FROM ingredient;
  """


  SELECT_ALL_ACTIONS = """
    SELECT id,name FROM cooking_action;
  """


  def __init__(self,db: AsyncSurrealDB,embeddingModel: EmbeddingModel = None):
      self.db = db
      self.embeddingModel = embeddingModel


  @staticmethod
  def extract_cooking_actions_with_parent(actions = None,parent = None):
      retVal = [] 
      if actions == None:
        actions = SurqlReferenceData.COOKING_ACTIONS
      for key, value in actions.items():
          if parent == None:
              retVal.append({"action":key,"parent":key}) 
          else:    
              retVal.append({"action":key, "parent":parent}) 
          if isinstance(value, list):
            for item in value:
                retVal.append({"action":item, "parent":key})
          else: 
              moreVals = SurqlReferenceData.extract_cooking_actions_with_parent(value,key)
              retVal.extend(moreVals)
      return retVal    
      

      
  async def insert_cooking_action(self,action,parent,useDBEmbedding = True):
      if useDBEmbedding==False:
        action_embedding = self.embeddingModel.sentence_to_vec(action)
        params = {"action": action,"action_embedding": action_embedding, "parent": parent}
        outcome = await self.db.query(SurqlReferenceData.INSERT_COOKING_ACTION, params)
      else:
        params = {"action": action, "parent": parent}
        outcome = await self.db.query(SurqlReferenceData.INSERT_COOKING_ACTION_CALC_EMBEDDING, params)

      for item in outcome:
          if item["status"]=="ERR":
              raise SystemError("Step action error: {0}".format(item["result"])) 
      return outcome


  async def insert_cooking_actions(self):
    theList = SurqlReferenceData.extract_cooking_actions_with_parent()
    for item in theList:
        await self.insert_cooking_action(item["action"],item["parent"]) 
        


  async def insert_ingredient(self,ingredient,useDBEmbedding = True):
      if useDBEmbedding==False:
        ingredient_embedding = self.embeddingModel.sentence_to_vec(ingredient)
        params = {"ingredient": ingredient,"ingredient_embedding": ingredient_embedding}
        outcome = await self.db.query(SurqlReferenceData.INSERT_INGREDIENT, params)
      else:
        params = {"ingredient": ingredient}
        outcome = await self.db.query(SurqlReferenceData.INSERT_INGREDIENT_CALC_EMBEDDING, params)
         
      for item in outcome:
          if item["status"]=="ERR":
              raise SystemError("Step ingredient error: {0}".format(item["result"]))
      return outcome
  


  async def select_all_ingredients(self):
      outcome = await self.db.query(SurqlReferenceData.SELECT_ALL_INGREDIENTS)
      return outcome



  async def select_all_actions(self):
      outcome = await self.db.query(SurqlReferenceData.SELECT_ALL_ACTIONS)
      return outcome
