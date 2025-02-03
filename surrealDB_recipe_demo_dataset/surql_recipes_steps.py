from surrealdb import AsyncSurreal
from surrealDB_embedding_model.database import Database

class SurqlRecipesAndSteps:


    INSERT_STEP = """
    LET $this_object = type::thing("step",[$recipe_id,$step_order]);

    CREATE $this_object CONTENT {{
        step_order : $step_order,
        step_description : $step_description,
        normalized_ingredients : $ingredients,
        actions : $actions
        }}  RETURN NONE;
    """



    INSERT_RECIPE = """

    LET $stepPointers = array::map($steps, |$obj| {
        RETURN type::thing("step", [$obj.recipe_id, $obj.sort_order]);
    });


    LET $this_object = type::thing("recipe",$recipe_id);

    CREATE $this_object CONTENT {
        name : $name,
        contributor_id : $contributor_id,
        minutes : $minutes,
        tags : $tags,
        steps : $stepPointers,
        ingredients : $ingredients,
        normalized_ingredients : $normalized_ingredients,
        description : $description,
        nutrition : $nutrition,
        time :{
            submitted : <datetime>$time_submitted,
            updated : <datetime>$time_updated
        }
        } RETURN NONE;
    """


    SELECT_RECIPES_THAT_USE_INGREDIENT = """
    SELECT id FROM recipe WHERE ingredients[*] @@ $ingredient_name;
    """

    SELECT_STEPS_THAT_USE_INGREDIENT = """
    SELECT id FROM step WHERE step_description @@ $ingredient_name;
    """
    
    UPDATE_RECIPE_NORMALIZED_INGREDIENTS = """
    UPDATE type::record($recipe)
    SET normalized_ingredients = $normalized_ingredients RETURN NONE;
    """

    UPDATE_STEP_NORMALIZED_INGREDIENTS = """
    UPDATE type::record($step)
    SET normalized_ingredients = $normalized_ingredients RETURN NONE;
    """

    UPDATE_STEP_ACTIONS = """
    UPDATE type::record($step)
    SET actions = $actions RETURN NONE;
    """

    
    SELECT_ALL_RECIPE_IDS = """
    SELECT id FROM recipe;
    """
    SELECT_RECIPE_IDS_WHERE_STEP_NORMALIZED_INGREDIENTS_ARE_NONE = """
        SELECT id FROM recipe WHERE
        !array::any(steps, |$record| $record.normalized_ingredients IS NOT NONE);
    """

    SELECT_RECIPE_DETAILS = """
    SELECT * FROM {recipe};
    """

    SELECT_RECIPES_WITH_NORMALIZED_INGREDIENTS = """
    SELECT id,normalized_ingredients FROM recipe;
    """
    SELECT_STEPS_THAT_USE_ACTION = """
    RETURN fn::steps_that_use_action_text_search($action)
    """

    SELECT_STEPS_THAT_USE_ACTION_FROM_RECIPE = """
    RETURN fn::steps_that_use_action_from_recipe_text_search($recipe,$action)
    """


    SELECT_STEPS_THAT_USE_INGREDIENT_FROM_RECIPE = """
    RETURN fn::steps_that_use_ingredient_from_recipe_text_search($recipe,$ingredient)
    """


    def __init__(self,db: AsyncSurreal):
        self.db = db



    async def check_index_status(self,table_name,index_name):
        outcome = await self.db.query(f"INFO FOR INDEX {index_name} ON TABLE {table_name}")
        return outcome

    async def check_index_statuses(self,table_name):
        outcome = await SurqlRecipesAndSteps.check_table_status(self,table_name)
        index_statuses = []
        for index_name in outcome["indexes"]:
            index_status = await SurqlRecipesAndSteps.check_index_status(self,table_name,index_name)
            index_statuses.append({"index":index_name,"status":index_status})
        return index_statuses
        


    async def check_table_status(self,table_name):
        outcome = await self.db.query(f"INFO FOR TABLE {table_name}")
        return outcome
    


    async def insert_step(self,recipe_id,
                        step_order,step_description,
                        normalized_ingredients = [],actions = []):

        
        params = {"recipe_id": recipe_id,
                "step_order": step_order,
                "step_description": str(step_description),
                "normalized_ingredients": normalized_ingredients,
                "actions": actions
                }
        outcome = Database.ParseResponseForErrors(await self.db.query_raw(SurqlRecipesAndSteps.INSERT_STEP, params))
        return outcome
       





    async def insert_recipe(self,
                            recipe_id,
                            name,
                            contributor_id,
                            minutes,
                            tags,
                            steps,
                            ingredients,
                            description,
                            nutrition,
                            time_submitted,
                            time_updated,
                            normalized_ingredients = []):

       
        params = {"recipe_id": recipe_id,
            "name": str(name),
            "contributor_id": contributor_id,
            "minutes": minutes,
            "tags": tags,
            "steps": steps,
            "ingredients": ingredients,
            "normalized_ingredients": normalized_ingredients,
            "description": str(description),
            "nutrition": nutrition,
            "time_submitted": time_submitted,
            "time_updated": time_updated
            }
        outcome = Database.ParseResponseForErrors(await self.db.query_raw(SurqlRecipesAndSteps.INSERT_RECIPE, params))
        return outcome


    async def select_recipes_that_use_ingredient(self,ingredient_name):
        params = {"ingredient_name": ingredient_name
                }
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_RECIPES_THAT_USE_INGREDIENT, params)
        return outcome

    async def select_steps_that_use_ingredient(self,ingredient_name):
        params = {"ingredient_name": ingredient_name
                }
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_STEPS_THAT_USE_INGREDIENT, params)
        return outcome






    async def update_recipe_normalized_ingredients(self,
                            recipe,
                            normalized_ingredients):

        params = {"recipe": recipe,
                "normalized_ingredients": normalized_ingredients
                }
        
        outcome = Database.ParseResponseForErrors(await self.db.query_raw(SurqlRecipesAndSteps.UPDATE_RECIPE_NORMALIZED_INGREDIENTS, params))
        return outcome





    async def update_step_normalized_ingredients(self,
                            step,
                            normalized_ingredients):

        params = {"step": step,
                "normalized_ingredients": normalized_ingredients
                }
        
        outcome = Database.ParseResponseForErrors(await self.db.query_raw(SurqlRecipesAndSteps.UPDATE_STEP_NORMALIZED_INGREDIENTS, params))    
        return outcome




    async def update_step_actions(self,
                            step,
                            actions):

        params = {"step": step,
                "actions": actions
                }
        
        outcome = Database.ParseResponseForErrors(await self.db.query_raw(SurqlRecipesAndSteps.UPDATE_STEP_ACTIONS, params))
        return outcome





    async def select_all_recipe_ids(self):
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_ALL_RECIPE_IDS)
        return outcome

    async def select_recipe_ids_without_step_normalized_ingredients(self):
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_RECIPE_IDS_WHERE_STEP_NORMALIZED_INGREDIENTS_ARE_NONE)
        return outcome
    
    async def select_recipe_details(self,recipe):
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_RECIPE_DETAILS.format(recipe=recipe))
        return outcome



    async def select_recipes_with_normalized_ingredients(self):
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_RECIPES_WITH_NORMALIZED_INGREDIENTS)
        return outcome



    async def select_steps_that_use_action(self,
                            action):

        params = {
                "action": action
                }
        
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_STEPS_THAT_USE_ACTION, params)
        return outcome



    async def select_steps_that_use_action_from_recipe(self,
                            recipe,
                            action):

        params = {"recipe": recipe,
                "action": action
                }
        
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_STEPS_THAT_USE_ACTION_FROM_RECIPE, params)
        return outcome





    async def select_steps_that_use_ingredient_from_recipe(self,
                            recipe,
                            ingredient):

        params = {"recipe": recipe,
                "ingredient": ingredient
                }
        
        outcome = await self.db.query(SurqlRecipesAndSteps.SELECT_STEPS_THAT_USE_INGREDIENT_FROM_RECIPE, params)
        return outcome