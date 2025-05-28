# Run with python -m agents.interface_agent.interface_agent

import ollama
import re
from agents.node import Node
from agents.interface_agent.util import unzip_file
from agents.interface_agent.util import convert_to_base64
from shared.file_tools import extract_json

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

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """

        def get_image_path(text: str) -> list[str]:
            """
             Check if the instruction contains an image path
            """
            matches= re.findall(r'\\image\s*"([^"]*)"', text)
            return matches

        image_paths = get_image_path(instruction)
        print(image_paths)

        def images_to_base64(image_paths: list[str])-> list[str]:
            images = [convert_to_base64(path) for path in image_paths]
            return images
        
        image_data = images_to_base64(image_paths)

        user_msg = {
                            'role': 'user',
                            'content': instruction,
                            'images': image_data
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

    sys_msg=""

    with open('agents/interface_agent/system_prompt.txt', 'r', encoding='utf-8') as file:
        sys_msg = file.read()

    model = "gemma3:4b"
    temperature = 0.5
    interfaceAgent = InterfaceAgent(model, "ollama", sys_msg, temperature)
    interfaceAgent.clear()

    while (True):
        prompt = input(">>> ")
        response = interfaceAgent.instruct(prompt)
        print(response)
        
        tasks = extract_json(response)
        if tasks is not None:
            break

    print(tasks)







