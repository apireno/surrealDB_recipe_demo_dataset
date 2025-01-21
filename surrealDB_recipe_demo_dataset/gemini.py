from recipe_data_constants import GeminiConstants
import google.generativeai as genai
import time
import os
import ast


class GeminiHelper():

    def __init__(self,gemini_constants: GeminiConstants,debug_file = None):
        self.gemini_constants = gemini_constants
        # Set your API key (I've stored mine in an env variable)
        genai.configure(api_key=os.getenv(gemini_constants.GOOGLE_GENAI_API_KEY_ENV_VAR))
        self.model = genai.GenerativeModel(gemini_constants.GEMINI_LLM_MODEL)
        self.debug_file = debug_file

    def fix_json_quotes(input_string):

        try:
            return ast.literal_eval(input_string)
        except:
            pattern = r"(?<!\\)'(.*?)(?<!\\)'"  
            ret_val = input_string.replace("\"", '|')
            ret_val = re.sub(pattern, r'"\1"', ret_val)
            try:
                return json.loads(ret_val.replace("|","'"))
            except:
                return ["ERR"]
            
    def log_debug_message(self,message):
        if self.debug_file:
            with open(self.debug_file, "a") as f:
                f.write(message)

    def attach_file(self,file_name):
        the_file = genai.upload_file(file_name)
        
        while the_file.state.name == "PROCESSING":
            #sleep to stop google from throttling
            time.sleep(self.gemini_constants.API_SLEEP)
            the_attached_file = genai.get_file(the_attached_file.name)   
        return the_file



    def generate_content(self,the_messages,attached_file):



        odd_text = ["```","```text","json"]
            
        #sleep to stop google from throttling
        time.sleep(self.gemini_constants.API_SLEEP)

        print("calling API ", end =".")
        if attached_file == None:
            response = self.model.generate_content([str(the_messages)])
        else:
            response = self.model.generate_content([attached_file,str(the_messages)])
        
        ai_response_text = response.text.strip()
        if ai_response_text.endswith(odd_text[0]) or ai_response_text.startswith(odd_text[0]):
            ai_response_text = ai_response_text.replace(odd_text[2],"")
            ai_response_text = ai_response_text.replace(odd_text[1],"")
            ai_response_text = ai_response_text.replace(odd_text[0],"")
            ai_response_text = ai_response_text.strip()
    
        
    
        self.log_debug_message(
    """
        ----------------------------------------------------
{5}
        ----------------------------------------------------
{0}
        ----------------------------------------------------
                    Ends with [{1}]? {2} 
                    Finish reason {3}
                    Usage data {4}
        ----------------------------------------------------
        """.format(response.text,
                self.gemini_constants.COMPLETION_DELEMITER,
                ai_response_text.endswith(self.gemini_constants.COMPLETION_DELEMITER), 
                response.candidates[0].finish_reason,
                response.usage_metadata,
                the_messages
                )
        )

        return ai_response_text


    def generate_content_until_complete_with_post_process_function(self, post_function,the_messages,attached_file,retry_count = 0, *args, **kwargs):
        """
        Inherits from parent_func, handles potential exceptions,
        and executes the passed function. Calls itself recursively
        on exception, respecting max_loop.

        Args:
          func: The function to be executed.
          *args: Positional arguments to pass to the function.
          **kwargs: Keyword arguments to pass to the function.
          loop_counter: Counter for recursive calls.
        """

        if retry_count > self.gemini_constants.RETRY_COUNT:
            raise Exception("Too many retries {0}".format(retry_count))
        
        try:
            print(retry_count, end ="+")
            ai_response_text = self.generate_content_until_complete(the_messages,attached_file)
            return post_function(ai_response_text, *args, **kwargs)
        except Exception as e:
            print(f"Parse error: {e}")
            retry_count += 1
            return self.generate_content_until_complete_with_post_process_function(
                 post_function,the_messages,attached_file,retry_count, *args, **kwargs)



    # this function will recursively call a prompt until
    # the prompt ends with the COMPLETION_DELIMINATER 
    # or exceeds the max number of tries
    def generate_content_until_complete(self,the_messages,attached_file,retry_count = 0):

        ai_response_text = self.generate_content(the_messages,attached_file)

        #confirm the response ends with the correct delemiter
        if ai_response_text.endswith(self.gemini_constants.COMPLETION_DELEMITER):
            return ai_response_text.replace(self.gemini_constants.COMPLETION_DELEMITER,"")
        else:            
            retry_count += 1
            print(retry_count, end =".")
            if retry_count > self.gemini_constants.RETRY_COUNT:
                raise Exception("Too many retries {0}".format(retry_count))
            else:
                #try again!
                return self.generate_content_until_complete(the_messages,attached_file,retry_count)
        