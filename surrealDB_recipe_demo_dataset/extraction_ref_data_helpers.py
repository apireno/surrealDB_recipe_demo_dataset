
import ast

class RefDataHelper:



    @staticmethod 
    def validate_lists_matchon_key(list1, list2, key):

        list1 = sorted(list1, key=lambda x: x[key])
        list2 = sorted(list2, key=lambda x: x[key])
        return RefDataHelper.validate_sorted_lists_matchon_key(list1,list2,key)
    
    @staticmethod 
    def validate_sorted_lists_match_on_key(list1, list2, key):
        """
        Validates that two lists of dictionaries have the same unique "key" values.

        Args:
            list1: The first list of dictionaries.
            list2: The second list of dictionaries.
        Returns:
            True if the lists have matching "ingredient" values, False otherwise.
        """
        if len(list1) != len(list2):
            return False  # Lists must have the same length

        for d1, d2 in zip(list1, list2):
            if d1[key].lower() != d2[key].lower():
                print(d1[key].lower())
                print(d2[key].lower())
                return False  # Mismatch found

        return True  # All ingredients match
    


    @staticmethod  
    def merge_dicts_over_two_keys(list1, list2, key1, key2):
        """
        Merges two lists of dictionaries based on "entity" and "sub" properties.

        Args:
            list1: The first list of dictionaries.
            list2: The second list of dictionaries.
        """
        merged_list = list1.copy()  # Create a copy of list1
  
        # Create a set of (entity, sub) tuples from list1 for efficient lookup
        existing_pairs = {(d[key1], d[key2]) for d in merged_list}

        for dict2 in list2:
            key = (dict2[key1], dict2[key2])
            if key not in existing_pairs:
                merged_list.append(dict2)  # Add if not present
            else:
                # Find and replace if present
                for i, dict1 in enumerate(merged_list):
                    if (dict1[key1], dict1[key2]) == key:
                        merged_list[i] = dict2
                    break
        
        merged_list = sorted(merged_list, key=lambda x: (x[key1], x[key2]))

        return merged_list  # Return the new merged list

    @staticmethod   
    def rsq(s):
        #remove single quotes
        return s.replace("'", "")



    @staticmethod
    def write_enriched_ingredients_to_file(ingredient_list,ingredient_file,file_mode="w"):
        with open(ingredient_file, file_mode) as f:
            f.write("[\n")
            for item in ingredient_list:
                f.write(f"{{'ingredient':'{item["ingredient"].replace("'"," ")}','flavor':'{item["flavor"].replace("'"," ")}'}},\n")
            f.write("]")

   
    @staticmethod
    def write_matched_ingredients_to_file(ingredient_match_list,ingredient_file,file_mode="w"):
        with open(ingredient_file, file_mode) as f:
            f.write("[\n")
            for item in ingredient_match_list:           
                f.write(f"{{'entity':'{RefDataHelper.rsq(item["entity"])}','sub':'{RefDataHelper.rsq(item["sub"])}','rationale':'{RefDataHelper.rsq(item["rationale"])}','confidence':'{item["confidence"]}'}},\n")
            f.write("]")

    
    @staticmethod
    def find_unmatched_items(list1, list2, key1, key2):
        """
        Generates a list of dictionaries from list1 where the key1
        property does not match any key2 property in list2.

        Args:
            list1: The first list of dictionaries with the key1 property.
            list2: The second list of dictionaries with the key2 property.

        Returns:
            A new list of dictionaries from list1 with unmatched ingredients.
        """
        # Create a set of entities from list2 for efficient lookup
        list2_items = {d[key2].lower() for d in list2}

        unmatched_list1_items = []
        for dict1 in list1:
            val1 = dict1[key1].lower()
            if val1 not in list2_items:
                unmatched_list1_items.append(dict1)

        return unmatched_list1_items


    @staticmethod
    def write_ingredients_and_matches_to_file(ingredient_list,ingredient_match_list,ingredient_unmatched_list,
                                              no_match_list_delimiter,full_list_delimiter,already_matched_delimeter,
                                              ingredient_file):
        
        

        #write unmatched first
        with open(ingredient_file, "w") as f:
            f.write(f"<{no_match_list_delimiter}>\n") 
        RefDataHelper.write_enriched_ingredients_to_file(
            ingredient_unmatched_list,ingredient_file, file_mode="a")
        with open(ingredient_file, "a") as f:
            f.write(f"</{no_match_list_delimiter}>\n") 


        #write full list
        with open(ingredient_file, "a") as f:
            f.write(f"<{full_list_delimiter}>\n") 
        RefDataHelper.write_enriched_ingredients_to_file(ingredient_list,ingredient_file, file_mode="a")
        with open(ingredient_file, "a") as f:
            f.write(f"</{full_list_delimiter}>\n") 



        #write matches last
        with open(ingredient_file, "a") as f:
            f.write(f"<{already_matched_delimeter}>\n") 
        RefDataHelper.write_matched_ingredients_to_file(ingredient_match_list,ingredient_file, file_mode="a")
        with open(ingredient_file, "a") as f:
            f.write(f"</{already_matched_delimeter}>\n") 

    @staticmethod
    def write_action_steps_for_attach_to_file(
            action_list,step_list, existing_actions_delimiter,new_text_delimiter,output_file
    ):
        
        with open(output_file, "w") as f:
            f.write(existing_actions_delimiter)

        RefDataHelper.write_list_as_blurb_to_file(action_list,output_file,"a")

        with open(output_file, "a") as f:
            f.write(new_text_delimiter)

        RefDataHelper.write_list_to_file(step_list,output_file,"a")
        
        




    @staticmethod
    def convert_simple_array_text_to_unique_sorted_list(text):

        sorted_list = []
        item_list =  ast.literal_eval(text)
        for item in item_list:
            item_lower = item.strip().lower()
            if item_lower not in sorted_list:
                sorted_list.append(item_lower)
     
        sorted_list.sort()
        return sorted_list

    @staticmethod
    def write_list_to_file(list,file_name,file_mode="w"):
        with open(file_name, file_mode) as f:
            f.write("[\n")
            for item in list:           
                f.write(f"'{item}',\n")
            f.write("]")


    @staticmethod
    def write_list_as_blurb_to_file(list,file_name,file_mode="w"):
        with open(file_name, file_mode) as f:
            for item in list:           
                f.write(f"{item},\n")

    @staticmethod
    def convert_enriched_ingredient_file_to_list(file_name):
        with open(file_name, 'r') as f:
                return RefDataHelper.convert_enriched_ingredient_file_text_to_list(f.read())

    @staticmethod
    def convert_enriched_ingredient_file_text_to_list(text):
        item_list =  ast.literal_eval(text)
        for item in item_list:
            item['ingredient'] = item['ingredient'].strip()
            item['flavor'] = item['flavor'].strip()
        return item_list


    @staticmethod
    def convert_ingredient_match_file_to_list(file_name):
        with open(file_name, 'r') as f:
                return RefDataHelper.convert_ingredient_match_file_text_to_list(f.read())






    @staticmethod
    def extend_action_to_action_match_list(action_list):
        action_match_list = []
        for item in action_list:
            action_match_list.append(
                {
                    "entity":f"{item}","parent":"", "rationale":"", "confidence":0
                }
            )
        return action_match_list


    @staticmethod
    def write_actions_as_matched_actions_to_file(action_list,action_file,file_mode="w"):
        action_match_list = RefDataHelper.extend_action_to_action_match_list(action_list)
        RefDataHelper.write_matched_actions_to_file(action_match_list,action_file,file_mode = file_mode)



    @staticmethod
    def write_matched_actions_to_file(action_match_list,action_file,file_mode="w"):
        with open(action_file, file_mode) as f:
            f.write("[\n")
            for item in action_match_list:           
                f.write(f"{{'entity':'{RefDataHelper.rsq(item["entity"])}','parent':'{RefDataHelper.rsq(item["parent"])}','rationale':'{RefDataHelper.rsq(item["rationale"])}','confidence':{item["confidence"]}}},\n")
            f.write("]")

    @staticmethod
    def write_actions_and_matched_actions_to_file(action_list,action_match_list,action_file,exisiting_relations_delimiter,file_mode="w"):
        RefDataHelper.write_list_to_file(action_list,action_file)
        with open(action_file, "a") as f:
            f.write(f"{exisiting_relations_delimiter}\n") 
        RefDataHelper.write_matched_actions_to_file(action_match_list,action_file,"a")












    # @staticmethod
    # def convert_ingredient_match_file_text_to_list(text):
    #     item_list =  ast.literal_eval(text)
    #     for item in item_list:
    #         item['ingredient'] = item['ingredient'].strip()
    #         item['flavor'] = item['flavor'].strip()
    #     return item_list
