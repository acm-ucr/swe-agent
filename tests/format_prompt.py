# this script prints out the prompt as a single line string for the json

import json 

prompt = """Task: {task}
                        File: {file_path}

                        START_CODE
                        [complete file content here - NO explanations, NO markdown, JUST the raw code/content]
                        END_CODE

                        You must put ONLY the raw file content between START_CODE and END_CODE. Do not include any explanations, descriptions, or markdown formatting.
                        """

print(json.dumps(prompt))