
class RecipeDataSurqlDDL:

    
    DDL_CREATE_NS = """
        DEFINE NAMESPACE IF NOT EXISTS {ns};
        DEFINE DATABASE IF NOT EXISTS {db};
        
        USE NAMESPACE {ns};
        USE DATABASE {db};
    """
    DDL_OVERWRITE_NS = """
        DEFINE NAMESPACE OVERWRITE {ns};
        DEFINE DATABASE OVERWRITE {db};

        USE NAMESPACE {ns};
        USE DATABASE {db};
    """
    DDL_ANALYZER = """
        REMOVE ANALYZER IF EXISTS snowball_analyzer;
        DEFINE ANALYZER snowball_analyzer
            TOKENIZERS class
            FILTERS lowercase, snowball(english);
    """



    DDL_REVIEW_WO_EMBEDDING_EVENTS = """

        REMOVE TABLE IF EXISTS review;
        DEFINE TABLE review TYPE RELATION IN reviewer OUT recipe SCHEMAFULL;
        DEFINE FIELD time ON review TYPE object;
        DEFINE FIELD time.submitted ON review TYPE datetime DEFAULT time::now();
        DEFINE FIELD time.updated ON review TYPE datetime VALUE time::now();
        DEFINE FIELD rating ON review TYPE number;
        DEFINE FIELD review_text ON review TYPE string;
        DEFINE FIELD review_text_embedding ON review TYPE option<array<float>>;



        REMOVE INDEX IF EXISTS review_text_index ON TABLE review;
        DEFINE INDEX review_text_index ON TABLE review
        FIELDS review_text SEARCH ANALYZER snowball_analyzer BM25;

        REMOVE INDEX IF EXISTS idx_review_text ON TABLE review;
        DEFINE INDEX idx_review_text ON TABLE review FIELDS review_text_embedding HNSW DIMENSION 50 M 32 EFC 300;

    """

    DDL_REVIEW = DDL_REVIEW_WO_EMBEDDING_EVENTS #+ DDL_REVIEW_EMBEDDING_EVENT

    DDL_REVIEWER = """
       
    REMOVE TABLE IF EXISTS reviewer;
    DEFINE TABLE reviewer TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD name ON reviewer TYPE string;


    """

    DDL_SEARCH_FUNCTIONS = """

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_ingredient_from_recipe_text_search($recipe: record<recipe>, 
    $ingredient: record<ingredient>) {
        LET $full_text_results = (
            SELECT id, step_description, search::score(1) AS relevance
            FROM step            
            WHERE id[0]==record::id($recipe)
            AND step_description @1@ $ingredient.name
            ORDER BY relevance DESC
        ); 
        RETURN $full_text_results;
    };

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_ingredient_from_recipe_vector_search($recipe: record<recipe>, 
    $ingredient: record<ingredient>) {
        LET $semantic_results = (
            SELECT id, vector::distance::knn() as distance
            FROM step
            WHERE id[0]==record::id($recipe)
            AND step_description_embedding <|10,50|> $ingredient.ingredient_vector
            ORDER BY distance
        );
        RETURN $semantic_results;
    };


    DEFINE FUNCTION OVERWRITE fn::steps_that_use_ingredient_from_recipe($recipe: record<recipe>, 
    $ingredient: record<ingredient>,$full_text_weight: float, $rrf_k: int) {
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
        
    };

    

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_text_search(
    $action: record<cooking_action>) {
        LET $full_text_results = (
            SELECT id, search::score(1) AS relevance
            FROM step            
            WHERE step_description @1@ $action.name
            ORDER BY relevance DESC
        ); 
        RETURN $full_text_results;
    };

    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_from_recipe_text_search( 
    $recipe: record<recipe>,
    $action: record<cooking_action>) {
        LET $full_text_results = (
            SELECT id, step_description, search::score(1) AS relevance
            FROM step            
            WHERE id[0]==record::id($recipe) 
            AND  step_description @1@ $action.name
            ORDER BY relevance DESC
        ); 
        RETURN $full_text_results;
    };


    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_from_recipe_vector_search( 
    $recipe: record<recipe>,
    $action: record<cooking_action>) {
        LET $semantic_results = (
            SELECT id, vector::distance::knn() as distance
            FROM step
            WHERE id[0]==record::id($recipe) 
            AND step_description_embedding <|10,50|> $action.action_vector
            ORDER BY distance
        );
        RETURN $semantic_results;
    };


    DEFINE FUNCTION OVERWRITE fn::steps_that_use_action_from_recipe( 
    $recipe: record<recipe>,
    $action: record<cooking_action>,$full_text_weight: float, $rrf_k: int) {
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
        
    };

    """

    # DDL_STEP_EMBEDDING_EVENT = """
    #     DEFINE EVENT OVERWRITE update_step_description_embedding ON TABLE step WHEN 
    #         $before.step_description != $after.step_description THEN {
    #         UPDATE 
    #             $this    
    #         SET step_description_embedding = fn::sentence_to_vector($after.step_description);
    #     };
    #     """
    # DDL_RECIPE_EMBEDDING_EVENT = """

    #     DEFINE EVENT OVERWRITE update_recipe_description_embedding ON TABLE recipe WHEN 
    #         $before.description != $after.description THEN {
    #         UPDATE 
    #             $this    
    #         SET description_embedding = fn::sentence_to_vector($after.description);
    #     };
    #     """

    # DDL_REVIEW_EMBEDDING_EVENT = """
    #     DEFINE EVENT OVERWRITE update_review_text_embedding ON TABLE review WHEN 
    #         $before.review_text != $after.review_text THEN {
    #         UPDATE 
    #             $this    
    #         SET review_text_embedding = fn::sentence_to_vector($after.review_text);
    #     };
    #     """
    

    # DDL_ACTION_EMBEDDING_EVENT = """
      
    #     DEFINE EVENT OVERWRITE update_action_embedding ON TABLE cooking_action WHEN 
    #         $before.name != $after.name THEN {
    #         UPDATE 
    #             $this    
    #         SET action_embedding = fn::sentence_to_vector($after.name);
    #     };
    #     """
    
    # DDL_INGREDIENT_EMBEDDING_EVENT = """
      
    #     DEFINE EVENT OVERWRITE update_ingredient_embedding ON TABLE ingredient WHEN 
    #         $before.name != $after.name THEN {
    #         UPDATE 
    #             $this    
    #         SET ingredient_embedding = fn::sentence_to_vector($after.name);
    #     };
    #     """

    # DDL_EMBEDDING_EVENTS = DDL_STEP_EMBEDDING_EVENT + DDL_RECIPE_EMBEDDING_EVENT + DDL_REVIEW_EMBEDDING_EVENT + DDL_ACTION_EMBEDDING_EVENT + DDL_INGREDIENT_EMBEDDING_EVENT

    DDL_EMBEDDING_MODEL = """


        REMOVE TABLE IF EXISTS embedding_model;
        DEFINE TABLE embedding_model TYPE NORMAL SCHEMAFULL;
        DEFINE FIELD word ON embedding_model TYPE string;
        DEFINE FIELD embedding ON embedding_model TYPE array<float>;

        DEFINE FUNCTION OVERWRITE fn::sentence_to_vector($sentence: string) {
            LET $vector_size = (SELECT VALUE array::len(embedding) FROM embedding_model LIMIT 1)[0];
            
            LET $words = string::lowercase($sentence).split(" ");
            LET $words = array::filter($words, |$word| $word != "");
            LET $vectors = array::map($words, |$word| {
                RETURN (SELECT VALUE embedding FROM type::thing("embedding_model",$word))[0];
            });

            
            LET $vectors = array::filter($vectors, |$v| { RETURN $v != NONE; });
            LET $transposed = array::transpose($vectors);
            LET $sum_vector = $transposed.map(|$sub_array| math::sum($sub_array));
            
            
            LET $mean_vector = vector::scale($sum_vector, 1.0f / array::len($vectors));

            RETURN 
                IF array::len($mean_vector) == $vector_size {$mean_vector}
                ELSE {array::repeat(0,$vector_size)}
                ;
        };

    """

    DDL_INGREDIENT_WO_EMBEDDING_EVENTS = """

    REMOVE TABLE IF EXISTS ingredient;
    DEFINE TABLE ingredient TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD name ON ingredient TYPE string;
    DEFINE FIELD ingredient_embedding ON ingredient TYPE option<array<float>>;


    """

    DDL_INGREDIENT = DDL_INGREDIENT_WO_EMBEDDING_EVENTS #+ DDL_INGREDIENT_EMBEDDING_EVENT



    DDL_ACTION_WO_EMBEDDING_EVENTS = """

    REMOVE TABLE IF EXISTS cooking_action;
    DEFINE TABLE cooking_action TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD name ON cooking_action TYPE string;
    DEFINE FIELD action_embedding ON cooking_action TYPE option<array<float>>;

    REMOVE TABLE IF EXISTS action_is_type_of;
    DEFINE TABLE action_is_type_of TYPE RELATION IN cooking_action OUT cooking_action SCHEMAFULL;

    """
    DDL_ACTION = DDL_ACTION_WO_EMBEDDING_EVENTS #+ DDL_ACTION_EMBEDDING_EVENT

    DDL_STEP_WO_EMBEDDING_EVENTS = """
    REMOVE TABLE IF EXISTS step;
    DEFINE TABLE step TYPE NORMAL SCHEMAFULL;
    DEFINE FIELD id ON step TYPE array<number>;
    DEFINE FIELD step_order ON step TYPE number;
    DEFINE FIELD step_description ON step TYPE option<string>;
    DEFINE FIELD step_description_embedding ON step TYPE option<array<float>>;
    DEFINE FIELD normalized_ingredients ON step TYPE option<array<record<ingredient>>>;
    DEFINE FIELD actions ON step TYPE option<array<record<cooking_action>>>;



    REMOVE INDEX IF EXISTS step_desc_index ON TABLE step;
    DEFINE INDEX step_desc_index ON TABLE step
        FIELDS step_description SEARCH ANALYZER snowball_analyzer BM25;
        
    REMOVE INDEX IF EXISTS step_ingredient_index ON TABLE step;
    DEFINE INDEX step_ingredient_index ON TABLE step
    FIELDS normalized_ingredients[*].name SEARCH ANALYZER snowball_analyzer BM25;

    REMOVE INDEX IF EXISTS unnormalized_step_ingredient_index ON TABLE step;
    DEFINE INDEX unnormalized_step_ingredient_index ON TABLE step
    FIELDS ingredients[*] SEARCH ANALYZER snowball_analyzer BM25;
    
    
    REMOVE INDEX IF EXISTS idx_step_description ON TABLE step;
    DEFINE INDEX idx_step_description ON TABLE step FIELDS step_description_embedding HNSW DIMENSION 50 M 32 EFC 300;
    """
    DDL_STEP = DDL_STEP_WO_EMBEDDING_EVENTS #+ DDL_STEP_EMBEDDING_EVENT


    DDL_RECIPE_WO_EMBEDDING_EVENTS = """
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
    DEFINE FIELD description_embedding ON TABLE recipe TYPE option<array<float>>;
    DEFINE FIELD nutrition ON recipe TYPE option<array<number>>;
    DEFINE FIELD time ON recipe TYPE object;
    DEFINE FIELD time.submitted ON recipe TYPE datetime DEFAULT time::now();
    DEFINE FIELD time.updated ON recipe TYPE datetime VALUE time::now();




    REMOVE INDEX IF EXISTS recipe_desc_index ON TABLE recipe;
    DEFINE INDEX recipe_desc_index ON TABLE recipe
    FIELDS description SEARCH ANALYZER snowball_analyzer BM25;
    
    REMOVE INDEX IF EXISTS recipe_ingredient_index ON TABLE recipe;
    DEFINE INDEX recipe_ingredient_index ON TABLE recipe
    FIELDS normalized_ingredients[*].name SEARCH ANALYZER snowball_analyzer BM25;


    REMOVE INDEX IF EXISTS unnormalized_recipe_ingredient_index ON TABLE recipe;
    DEFINE INDEX unnormalized_recipe_ingredient_index ON TABLE recipe
    FIELDS ingredients[*] SEARCH ANALYZER snowball_analyzer BM25;


    REMOVE INDEX IF EXISTS idx_step_description ON TABLE recipe;
    DEFINE INDEX idx_recipe_description ON TABLE recipe FIELDS description_embedding HNSW DIMENSION 50 M 32 EFC 300;



    """
    DDL_RECIPE = DDL_RECIPE_WO_EMBEDDING_EVENTS #+ DDL_RECIPE_EMBEDDING_EVENT



    DDL_WO_EMBEDDING_EVENTS = (DDL_ANALYZER + DDL_ACTION_WO_EMBEDDING_EVENTS + 
                        DDL_INGREDIENT_WO_EMBEDDING_EVENTS + 
                        DDL_STEP_WO_EMBEDDING_EVENTS + 
                        DDL_RECIPE_WO_EMBEDDING_EVENTS + 
                        DDL_REVIEWER +
                        DDL_REVIEW_WO_EMBEDDING_EVENTS +
                        DDL_SEARCH_FUNCTIONS)
    
    DDL = DDL_WO_EMBEDDING_EVENTS #+ DDL_EMBEDDING_EVENTS

