from surrealDB_embedding_model.embeddings import EmbeddingModel
from surrealdb import AsyncSurreal
from surrealDB_embedding_model.database import Database

class SurqlReviewsAndReviewers:



    INSERT_REVIEWER =  """
    LET $this_object = type::thing("reviewer",$reviewer_id);
    UPSERT $this_object CONTENT {{
        name : $name
        }} RETURN NONE;
    """

    INSERT_REVIEW = """
    LET $reviewer_object = type::thing("reviewer",$reviewer_id);
    LET $recipe_object = type::thing("recipe",$recipe_id);


    RELATE $reviewer_object -> review -> $recipe_object
    CONTENT {{
        time :{{
            submitted : <datetime>$time_submitted,
            updated : <datetime>$time_updated
        }},
        rating : $rating,
        review_text : $review_text
        }} RETURN NONE;
    """





    def __init__(self,db: AsyncSurreal,embeddingModel: EmbeddingModel = None):
        self.db = db
        self.embeddingModel = embeddingModel

    async def insert_reviewer(self,reviewer_id,name):
        
        params = {"reviewer_id": reviewer_id,
                "name": str(name)
                }
        outcome = Database.ParseResponseForErrors(await self.db.query_raw(SurqlReviewsAndReviewers.INSERT_REVIEWER, params))
        return outcome
        



    async def insert_review(self,reviewer_id,recipe_id,
                            time_submitted,time_updated,
                            rating,review_text):
        

        params = {"reviewer_id": reviewer_id,
            "recipe_id": recipe_id,
            "time_submitted": time_submitted,
            "time_updated": time_updated,
            "rating": rating,
            "review_text": str(review_text)
            }
        outcome = Database.ParseResponseForErrors(await self.db.query_raw(SurqlReviewsAndReviewers.INSERT_REVIEW, params))
        return outcome
  
    
    


