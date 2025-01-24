from surrealdb import AsyncSurrealDB

class SurqlReferenceData:
  

  # COOKING_ACTIONS = {
  #   "prepare": {
  #     "cut": [
  #       "chiffonade", "julienne", "dice", "mince", "chop", "slice", "grind", "crush", "mash", "puree"
  #     ],
  #     "combine": [
  #       "add", "mix", "fold", "blend", "stir"
  #     ],
  #     "separate": [
  #       "strain", "drain", "sift", "skim", "degrease", "filter", "separate", "divide", "split", "remove", "discard", "shell", "shuck", "deseed", "skin", "peel", "pare", "gut", "zest" 
  #     ],
  #     "apply": [
  #       "spread", "brush", "drizzle", "sprinkle", "coat", "dust", "rub", "stuff", "fill", "inject", "pack", "glaze", "baste", "pipe", "lard", "roll"
  #     ],
  #     "measure": [
  #       "measure", "weigh", "level"
  #     ],
  #     "other": [
  #       "acidulate", "brine", "marinate", "tenderize", "score", "butterfly", "spatchcock", "truss", "tie", "trim", "french", "debone" 
  #     ]
  #   },
  #   "cook": {
  #     "dry heat": [
  #       "bake", "roast", "broil", "fry", "pan fry", "sauté", "sear", "deep fry", "stir fry", "grill", "smoke", "char", "toast", "brown", "caramelize"
  #     ],
  #     "moist heat": [
  #       "blanch", "boil", "braise", "poach", "simmer", "sous vide", "steam", "stew", "pressure cook", "reduce"
  #     ],
  #     "other": [
  #       "microwave", "reheat", "defrost", "confit"
  #     ]
  #   },
  #   "finish": {
  #     "serve": [
  #       "garnish", "plate", "serve"
  #     ],
  #     "preserve": [
  #       "preserve", "can", "pickle", "cure", "freeze", "dry", "smoke", "dehydrate" 
  #     ],
  #     "other": [
  #       "test", "check", "season", "adjust", "thicken", "thin", "sweeten", "deglaze", "rest", "sanitize", "wipe", "clean" 
  #     ]
  #   }
  # }



  INSERT_COOKING_ACTION = """

  LET $parent_object = type::thing("cooking_action",$parent);
  LET $this_object = type::thing("cooking_action",$action);

  UPSERT $this_object  CONTENT {{
      name : $action
      }} RETURN NONE;

  RELATE $this_object ->is_type_of-> $parent_object CONTENT {{
    rationale: $rationale,
    confidence: <int>$confidence
  }} RETURN NONE;

  """

  INSERT_INGREDIENT_SUBSTITUTE = """
    LET $substitute_object = type::thing("ingredient",$substitute);
    LET $this_object = type::thing("ingredient",$ingredient);

    RELATE $this_object ->is_similar_to-> $substitute_object CONTENT {{
        rationale: $rationale,
        confidence: <int>$confidence
    }} RETURN NONE;
  """
  
  INSERT_INGREDIENT = """
  LET $this_object = type::thing("ingredient",$ingredient);

  UPSERT $this_object CONTENT {{
      name : $ingredient,
      flavor : $flavor
      }} RETURN NONE;
  """


  SELECT_ALL_INGREDIENTS = """
  SELECT id,name FROM ingredient;
  """


  SELECT_ALL_ACTIONS = """
    SELECT id,name FROM cooking_action;
  """


  def __init__(self,db: AsyncSurrealDB):
      self.db = db


  # @staticmethod
  # def extract_cooking_actions_with_parent(actions = None,parent = None):
  #     retVal = [] 
  #     if actions == None:
  #       actions = SurqlReferenceData.COOKING_ACTIONS
  #     for key, value in actions.items():
  #         if parent == None:
  #             retVal.append({"action":key,"parent":key}) 
  #         else:    
  #             retVal.append({"action":key, "parent":parent}) 
  #         if isinstance(value, list):
  #           for item in value:
  #               retVal.append({"action":item, "parent":key})
  #         else: 
  #             moreVals = SurqlReferenceData.extract_cooking_actions_with_parent(value,key)
  #             retVal.extend(moreVals)
  #     return retVal    
    



      
  async def insert_cooking_action(self,action,parent,rationale,confidence):
      
      params = {"action": action, "parent": parent,"rationale":rationale,"confidence":confidence }
      outcome = await self.db.query(SurqlReferenceData.INSERT_COOKING_ACTION, params)

      for item in outcome:
          if item["status"]=="ERR":
              raise SystemError("Step action error: {0}".format(item["result"])) 
      return outcome



  async def insert_ingredient_substitute(self,ingredient,substitute,rationale,confidence):
      
      params = {"ingredient": ingredient,
                "substitute": substitute,
                "rationale": rationale,
                "confidence": confidence}
      outcome = await self.db.query(SurqlReferenceData.INSERT_INGREDIENT_SUBSTITUTE, params)
         
      for item in outcome:
          if item["status"]=="ERR":
              raise SystemError("Step ingredient error: {0}".format(item["result"]))
      return outcome
  

  async def insert_ingredient(self,ingredient,flavor):
      
      params = {"ingredient": ingredient,
                "flavor": flavor}
      outcome = await self.db.query(SurqlReferenceData.INSERT_INGREDIENT, params)
         
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
