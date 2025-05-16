# TodoL Convert multimodal input like image to text json
# 
#Override instruct in reasoning agent

# Run with python -m agents.interface_agent.interface_agent

import ollama 
from agents.node import Node
from agents.interface_agent.util import unzip_file

class InterfaceAgent(Node):
    def __init__(self, model_name, backend, sys_msg, temperature):
        self.temperature = temperature
        # Add system prompt to message history
        self.messages = [
            {
                            'role': 'system', 
                            'content': sys_msg
            }
        ]
        super().__init__(model_name, backend, sys_msg)

    def clear (self):
        """
        Clears the agent's message history.
        """
        self.messages = [
            {
                            'role': 'system', 
                            'content': sys_msg
            }
        ]

    def instruct(self, instruction, image_path):
        """
        Instructs the agent to perform a task.
        """
        user_msg = {
                            'role': 'user', 
                            'content': instruction,
                            'images': [image_path]
                    }
        self.messages.append(user_msg)

        if self.backend == "ollama":
            response = ollama.chat(model=self.model_name, 
                    messages=self.messages, 
                    tools = self.tools, 
                    options = {'temperature': self.temperature} #EDITED
            )
                    
            response = response['message']['content']
            # Add agent message to history
            self.messages.append(
                {
                    'role': 'assistant', 
                    'content': response
                }
            )

        elif self.backend == "huggingface":
            response = self.model.run(instruction)

        return response 
    
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    print('starting')
    load_dotenv() 
    
    model = "gemma3:12b"
    sys_msg = '''
        You will be given an image of a website.
        Clearly describe each part of the website, what the components look like, a possible use for them. 
        For every component, say where they are on the page. Also describe the color and shape of each compoent. If a part
        of a page appears to be an image, state there is an image there and briefly describe it. If there is 
        any part of the page design you are not clear about, ask the user for clarification, or continue processing the image until a 
        thorough understanding is gained. Focus soley on the design. Do not ask irrelevant questions. 

        If there is text, simply state that part of the website has text saying 'dummy text'. Don't worry about the font, but state if a 
        component has text written on it or near it. 

        Format all your responses in the following format:
        <description> | <query>
        Don't include the actual phrases <description> and <query> 
        
        Every time you update the description, retain all information from your prior descriptions unless it has been
        updated with new information. 

        If the user prompts you with a question or goes off topic, still reply with your description from your
        previous response first. Update it 
        
        Once you feel you have gained a comprehensive understanding of the website, type 
        nothing but 'FINISHED' in the query section and your comprehensive description in the 
        description section.  
    '''
    temperature = 0.5

    interfaceAgent = InterfaceAgent(model, "ollama", sys_msg, temperature)

    figma_zip_path = 'agents/interface_agent/testFigma.zip'
    output_dir = unzip_file(figma_zip_path)

    website_compoents = {}

        # Iterate through each file
    for filename in os.listdir(output_dir):
        image_path = os.path.join(output_dir, filename)
        curr_page = os.path.splitext(os.path.basename(filename))[0]

        
        interfaceAgent.clear()

        prompt = f'{sys_msg}'
       # prompt = 'hello!'

        while (True):
            print(image_path)
            from PIL import Image
            Image.open(image_path).show()
            response = (interfaceAgent.instruct(prompt,image_path))
            response = f'{curr_page} | {response}'
            print(response)
            prompt = input()

            # Code can end based on agent decision or user decision?
            if 'FINISHED' in response or prompt == 'exit':
                title = response.split('|', 2)[0]
                description = response.split('|')[1]

                website_compoents[title] = description
                break

    print('FINSIHED. FINAL DESCRIPTION: ')
    print(website_compoents)


    

    



