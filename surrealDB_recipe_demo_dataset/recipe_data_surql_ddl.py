
class RecipeDataSurqlDDL:

    
    DDL_CREATE_NS = """
        DEFINE NAMESPACE IF NOT EXISTS {ns};
        USE NAMESPACE {ns};
        DEFINE DATABASE IF NOT EXISTS {db};
        USE DATABASE {db};
    """
    DDL_OVERWRITE_NS = """
        DEFINE NAMESPACE OVERWRITE {ns};
        USE NAMESPACE {ns};
        DEFINE DATABASE OVERWRITE {db};
        USE DATABASE {db};
    """
    DDL_ANALYZER = """
        REMOVE ANALYZER IF EXISTS snowball_analyzer;
        DEFINE ANALYZER snowball_analyzer
            TOKENIZERS class
            FILTERS lowercase, snowball(english);
    """



    DDL_REVIEW = """

        REMOVE TABLE IF EXISTS review;
        DEFINE TABLE review TYPE RELATION IN reviewer OUT recipe SCHEMAFULL;
        DEFINE FIELD time ON review TYPE object;
        DEFINE FIELD time.submitted ON review TYPE datetime DEFAULT time::now();
        DEFINE FIELD time.updated ON review TYPE datetime VALUE time::now();
        DEFINE FIELD rating ON review TYPE number;
        DEFINE FIELD review_text ON review TYPE string;
        DEFINE FIELD review_text_embedding ON review TYPE option<array<float>> DEFAULT fn::sentence_to_vector(review_text);

    """

    DDL_REVIEW_INDEX_REMOVE = """


        REMOVE INDEX IF EXISTS review_text_index ON TABLE review;
        
        REMOVE INDEX IF EXISTS vector_index_review_text ON TABLE review;
        

    """
    DDL_REVIEW_INDEX_DEFINE = """
        DEFINE INDEX review_text_index ON TABLE review
            FIELDS review_text SEARCH ANALYZER snowball_analyzer BM25;
        DEFINE INDEX vector_index_review_text ON TABLE review FIELDS review_text_embedding 
            HNSW DIMENSION {embed_dimensions} M 32 EFC 300;

    """
    DDL_REVIEW_INDEX_DEFINE_CONCURRENTLY = """
        DEFINE INDEX review_text_index ON TABLE review
            FIELDS review_text SEARCH ANALYZER snowball_analyzer BM25 CONCURRENTLY;
        DEFINE INDEX vector_index_review_text ON TABLE review FIELDS review_text_embedding 
            HNSW DIMENSION {embed_dimensions} M 32 EFC 300 CONCURRENTLY;

    """

    DDL_REVIEWER = """
       
    REMOVE TABLE IF EXISTS reviewer;
    DEFINE TABLE reviewer TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD name ON reviewer TYPE string;


    """

    DDL_SEARCH_FUNCTIONS = """

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_ingredient_from_recipe_text_search($recipe: record<recipe>, 
    $ingredient: record<ingredient>) {{
        LET $full_text_results = (
            SELECT id, step_description, search::score(1) AS relevance
            FROM step            
            WHERE id[0]==record::id($recipe)
            AND step_description @1@ $ingredient.name
            ORDER BY relevance DESC
        ); 
        RETURN $full_text_results;
    }};

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_ingredient_from_recipe_vector_search($recipe: record<recipe>, 
    $ingredient: record<ingredient>) {{
        LET $semantic_results = (
            SELECT id, vector::distance::knn() as distance
            FROM step
            WHERE id[0]==record::id($recipe)
            AND step_description_embedding <|10,{embed_dimensions}|> $ingredient.ingredient_vector
            ORDER BY distance
        );
        RETURN $semantic_results;
    }};


    DEFINE FUNCTION OVERWRITE fn::steps_that_use_ingredient_from_recipe($recipe: record<recipe>, 
    $ingredient: record<ingredient>,$full_text_weight: float, $rrf_k: int) {{
        LET $match_count = 100;
        LET $semantic_weight = 1 - $full_text_weight;
        LET $full_text_results = fn::steps_that_use_ingredient_from_recipe_text_search(
            $recipe,
            $ingredient
        );
        LET $semantic_results = fn::steps_that_use_ingredient_from_recipe_vector_search(
            $recipe,
            $ingredient
        );



        RETURN (
            SELECT 
                id,
                step_description,
                (($full_text_weight * (1.0 / ($rrf_k + ((array::find_index($full_text_results.id, id) ?? $match_count * 2) + 1)))) + 
                ($semantic_weight * (1.0 / ($rrf_k + ((array::find_index($semantic_results.id, id) ?? $match_count * 2) + 1))))) 
                AS combined_score
            FROM step
            WHERE id IN $full_text_results.id OR id IN $semantic_results.id
            ORDER BY combined_score DESC
            LIMIT $match_count
        );
        
    }};

    

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_text_search(
    $action: record<cooking_action>) {{
        LET $full_text_results = (
            SELECT id, search::score(1) AS relevance
            FROM step            
            WHERE step_description @1@ $action.name
            ORDER BY relevance DESC
        ); 
        RETURN $full_text_results;
    }};

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_from_recipe_text_search( 
    $recipe: record<recipe>,
    $action: record<cooking_action>) {{
        LET $full_text_results = (
            SELECT id, step_description, search::score(1) AS relevance
            FROM step            
            WHERE id[0]==record::id($recipe) 
            AND  step_description @1@ $action.name
            ORDER BY relevance DESC
        ); 
        RETURN $full_text_results;
    }};


    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_from_recipe_vector_search( 
    $recipe: record<recipe>,
    $action: record<cooking_action>) {{
        LET $semantic_results = (
            SELECT id, vector::distance::knn() as distance
            FROM step
            WHERE id[0]==record::id($recipe) 
            AND step_description_embedding <|10,{embed_dimensions}|> $action.action_vector
            ORDER BY distance
        );
        RETURN $semantic_results;
    }};


    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_from_recipe( 
    $recipe: record<recipe>,
    $action: record<cooking_action>,$full_text_weight: float, $rrf_k: int) {{
        LET $match_count = 100;
        LET $semantic_weight = 1 - $full_text_weight;
        LET $full_text_results = fn::steps_that_use_action_from_recipe_text_search(
            $recipe,$action
        );
        LET $semantic_results = fn::steps_that_use_action_from_recipe_vector_search(
            $recipe,$action
        );



        RETURN (
            SELECT 
                id,
                step_description,
                (($full_text_weight * (1.0 / ($rrf_k + ((array::find_index($full_text_results.id, id) ?? $match_count * 2) + 1)))) + 
                ($semantic_weight * (1.0 / ($rrf_k + ((array::find_index($semantic_results.id, id) ?? $match_count * 2) + 1))))) 
                AS combined_score
            FROM step
            WHERE id IN $full_text_results.id OR id IN $semantic_results.id
            ORDER BY combined_score DESC
            LIMIT $match_count
        );
        
    }};

    """

    DDL_INGREDIENT = """

    REMOVE TABLE IF EXISTS ingredient;
    DEFINE TABLE ingredient TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD name ON ingredient TYPE string;
    DEFINE FIELD flavor ON ingredient TYPE string;
    DEFINE FIELD ingredient_embedding ON ingredient TYPE option<array<float>>  
        DEFAULT fn::sentence_to_vector(name);
    DEFINE FIELD flavor_embedding ON ingredient TYPE option<array<float>>  
        DEFAULT fn::sentence_to_vector(flavor);

    REMOVE INDEX IF EXISTS vector_index_ingredient_flavor_description_embedding ON TABLE ingredient;
    DEFINE INDEX vector_index_ingredient_flavor_description_embedding ON TABLE ingredient FIELDS flavor_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300;
    
    REMOVE INDEX IF EXISTS vector_index_ingredient_embedding ON TABLE ingredient;
    DEFINE INDEX vector_index_ingredient_embedding ON TABLE ingredient FIELDS ingredient_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300;
    

    REMOVE TABLE IF EXISTS is_similar_to;
    DEFINE TABLE is_similar_to SCHEMAFULL TYPE RELATION FROM ingredient TO ingredient;
    DEFINE FIELD rationale ON TABLE is_similar_to TYPE string;
    DEFINE FIELD confidence ON TABLE is_similar_to TYPE int;
    DEFINE FIELD rationale_embedding ON TABLE is_similar_to TYPE option<array<float>> 
        DEFAULT fn::sentence_to_vector(rationale);

    REMOVE INDEX IF EXISTS vector_index_is_similar_to_rationale_embedding ON TABLE is_similar_to;
    DEFINE INDEX vector_index_is_similar_to_rationale_embedding ON TABLE is_similar_to FIELDS rationale_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300;
    """

    DDL_ACTION = """

    REMOVE TABLE IF EXISTS cooking_action;
    DEFINE TABLE cooking_action TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD name ON cooking_action TYPE string;
    DEFINE FIELD cooking_action_embedding ON cooking_action TYPE option<array<float>>
     DEFAULT fn::sentence_to_vector(name);

    REMOVE TABLE IF EXISTS is_type_of;
    DEFINE TABLE is_type_of TYPE RELATION IN cooking_action OUT cooking_action SCHEMAFULL;
    DEFINE FIELD rationale ON TABLE is_type_of TYPE string;
    DEFINE FIELD confidence ON TABLE is_type_of TYPE int;

    DEFINE FIELD rationale_embedding ON TABLE is_type_of TYPE option<array<float>> 
        DEFAULT fn::sentence_to_vector(rationale);

    REMOVE INDEX IF EXISTS vector_index_is_type_of_rationale_embedding ON TABLE is_type_of;
    DEFINE INDEX vector_index_is_type_of_rationale_embedding ON TABLE is_type_of FIELDS rationale_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300;

    """
   
    DDL_STEP = """
    REMOVE TABLE IF EXISTS step;
    DEFINE TABLE step TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD id ON step TYPE array<number>;
    DEFINE FIELD step_order ON step TYPE number;
    DEFINE FIELD step_description ON step TYPE option<string>;
    DEFINE FIELD step_description_embedding ON step TYPE option<array<float>> 
     DEFAULT fn::sentence_to_vector(step_description);
    DEFINE FIELD normalized_ingredients ON step TYPE option<array<record<ingredient>>>;
    DEFINE FIELD actions ON step TYPE option<array<record<cooking_action>>>;
    """

    DDL_STEP_INDEX_REMOVE = """
    REMOVE INDEX IF EXISTS text_index_step_desccription ON TABLE step;
    REMOVE INDEX IF EXISTS text_index_step_ingredient ON TABLE step;
    REMOVE INDEX IF EXISTS vector_index_step_description ON TABLE step;
    """
    DDL_STEP_INDEX_DEFINE = """
    DEFINE INDEX text_index_step_desccription ON TABLE step
        FIELDS step_description SEARCH ANALYZER snowball_analyzer BM25;
        
    DEFINE INDEX text_index_step_ingredient ON TABLE step
    FIELDS normalized_ingredients[*].name SEARCH ANALYZER snowball_analyzer BM25;
    
    DEFINE INDEX vector_index_step_description ON TABLE step FIELDS step_description_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300;
    """
    

    DDL_STEP_INDEX_DEFINE_CONCURRENTLY = """
    DEFINE INDEX text_index_step_desccription ON TABLE step
        FIELDS step_description SEARCH ANALYZER snowball_analyzer BM25 CONCURRENTLY;
        
    DEFINE INDEX text_index_step_ingredient ON TABLE step
    FIELDS normalized_ingredients[*].name SEARCH ANALYZER snowball_analyzer BM25 CONCURRENTLY;
    
    DEFINE INDEX vector_index_step_description ON TABLE step FIELDS step_description_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300 CONCURRENTLY;
    """
    
    STEP_INDEX_NAMES = ["text_index_step_desccription","text_index_step_ingredient","vector_index_step_description"]

    DDL_RECIPE = """
    REMOVE TABLE IF EXISTS recipe;
    DEFINE TABLE recipe TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD name ON recipe TYPE string;
    DEFINE FIELD id ON recipe TYPE number;
    DEFINE FIELD contributor_id ON recipe TYPE option<number>;
    DEFINE FIELD minutes ON recipe TYPE option<number>;
    DEFINE FIELD tags ON recipe TYPE option<array<string>>;
    DEFINE FIELD steps ON recipe TYPE option<array<record<step>>>;
    DEFINE FIELD normalized_ingredients ON recipe TYPE option<array<record<ingredient>>>;
    DEFINE FIELD ingredients ON recipe TYPE option<array<string>>;
    DEFINE FIELD description ON recipe TYPE option<string>;
    DEFINE FIELD description_embedding ON TABLE recipe TYPE option<array<float>> 
    DEFAULT fn::sentence_to_vector(description);
    DEFINE FIELD nutrition ON recipe TYPE option<array<number>>;
    DEFINE FIELD time ON recipe TYPE object;
    DEFINE FIELD time.submitted ON recipe TYPE datetime DEFAULT time::now();
    DEFINE FIELD time.updated ON recipe TYPE datetime VALUE time::now();
    """

    DDL_RECIPE_INDEX_REMOVE = """
    REMOVE INDEX IF EXISTS text_index_recipe_description ON TABLE recipe;
    REMOVE INDEX IF EXISTS text_index_recipe_ingredient ON TABLE recipe;
    REMOVE INDEX IF EXISTS text_index_recipe_unnormalized_ingredient ON TABLE recipe;
    REMOVE INDEX IF EXISTS vector_index_step_description ON TABLE recipe;
    """

    DDL_RECIPE_INDEX_DEFINE = """
    DEFINE INDEX text_index_recipe_description ON TABLE recipe
        FIELDS description SEARCH ANALYZER snowball_analyzer BM25;
    
    DEFINE INDEX text_index_recipe_ingredient ON TABLE recipe
    FIELDS normalized_ingredients[*].name SEARCH ANALYZER snowball_analyzer BM25;

    DEFINE INDEX text_index_recipe_unnormalized_ingredient ON TABLE recipe
    FIELDS ingredients[*] SEARCH ANALYZER snowball_analyzer BM25;

    DEFINE INDEX vector_index_recipe_description ON TABLE recipe FIELDS description_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300;
    """
   

    DDL_RECIPE_INDEX_DEFINE_CONCURRENTLY = """
    DEFINE INDEX text_index_recipe_description ON TABLE recipe
        FIELDS description SEARCH ANALYZER snowball_analyzer BM25 CONCURRENTLY;
    
    DEFINE INDEX text_index_recipe_ingredient ON TABLE recipe
    FIELDS normalized_ingredients[*].name SEARCH ANALYZER snowball_analyzer BM25 CONCURRENTLY;

    DEFINE INDEX text_index_recipe_unnormalized_ingredient ON TABLE recipe
    FIELDS ingredients[*] SEARCH ANALYZER snowball_analyzer BM25 CONCURRENTLY;

    DEFINE INDEX vector_index_recipe_description ON TABLE recipe FIELDS description_embedding HNSW DIMENSION {embed_dimensions} M 32 EFC 300 CONCURRENTLY;
    """
   
    RECIPE_INDEX_NAMES = ["text_index_recipe_description","text_index_recipe_ingredient","text_index_recipe_unnormalized_ingredient","vector_index_recipe_description"]

    DDL = (DDL_ANALYZER + DDL_ACTION + 
                        DDL_INGREDIENT + 
                        DDL_STEP + DDL_STEP_INDEX_REMOVE + DDL_STEP_INDEX_DEFINE +
                        DDL_RECIPE + DDL_RECIPE_INDEX_REMOVE + DDL_RECIPE_INDEX_DEFINE +
                        DDL_REVIEWER +
                        DDL_REVIEW + DDL_REVIEW_INDEX_REMOVE + DDL_REVIEW_INDEX_DEFINE +
                        DDL_SEARCH_FUNCTIONS)
    

