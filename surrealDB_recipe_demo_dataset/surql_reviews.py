from surrealDB_embedding_model.embeddings import EmbeddingModel
from surrealdb import AsyncSurrealDB

class SurqlReviewsAndReviewers:



    INSERT_REVIEWER =  """
    LET $this_object = type::thing("reviewer",$reviewer_id);
    UPSERT $this_object CONTENT {{
        name : $name
        }} RETRUN NONE;
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
        review_text : $review_text,
        review_text_embedding : $review_text_embedding
        }} RETURN NONE;
    """



    INSERT_REVIEW_CALC_EMBEDDING = """
    LET $reviewer_object = type::thing("reviewer",$reviewer_id);
    LET $recipe_object = type::thing("recipe",$recipe_id);
    LET $review_text_embedding = fn::sentence_to_vector($review_text);


    RELATE $reviewer_object -> review -> $recipe_object
    CONTENT {{
        time :{{
            submitted : <datetime>$time_submitted,
            updated : <datetime>$time_updated
        }},
        rating : $rating,
        review_text : $review_text,
        review_text_embedding : $review_text_embedding
        }} RETURN NONE;
    """



    def __init__(self,db: AsyncSurrealDB,embeddingModel: EmbeddingModel = None):
        self.db = db
        self.embeddingModel = embeddingModel

    async def insert_reviewer(self,reviewer_id,name):
        
        params = {"reviewer_id": reviewer_id,
                "name": str(name)
                }
        outcome = await self.db.query(SurqlReviewsAndReviewers.INSERT_REVIEWER, params)
        return outcome
        



    async def insert_review(self,reviewer_id,recipe_id,
                            time_submitted,time_updated,
                            rating,review_text,useDBEmbedding = True):
        

        if useDBEmbedding==False:
            review_text_embedding = self.embeddingModel.sentence_to_vec(review_text)
            params = {"reviewer_id": reviewer_id,
                "recipe_id": recipe_id,
                "time_submitted": time_submitted,
                "time_updated": time_updated,
                "rating": rating,
                "review_text": str(review_text),
                "review_text_embedding":review_text_embedding
                }
            outcome = await self.db.query(SurqlReviewsAndReviewers.INSERT_REVIEW, params)
        else:
            params = {"reviewer_id": reviewer_id,
                "recipe_id": recipe_id,
                "time_submitted": time_submitted,
                "time_updated": time_updated,
                "rating": rating,
                "review_text": str(review_text)
                }
            outcome = await self.db.query(SurqlReviewsAndReviewers.INSERT_REVIEW_CALC_EMBEDDING, params)
            
        for item in outcome:
            if item["status"]=="ERR":
                raise SystemError("Review error: {0}".format(item["result"]))
        return outcome
  
    
    


