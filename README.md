# SWE Agent
This is the first iteration of a local, distributed SWE agent system. The goal of this first iteration is to automate the creation of the frontend and backend of a basic website when given a user prompt and the figma assets. 


## Enviorment Setup
Make sure to clone the repo with submodules
```
    git clone --recurse-submodules https://github.com/acm-ucr/swe-agent.git
```


Create a conda enviorment with python 3.10
```
    conda create -n myenv python=3.10 
```


Install the requirements
```
    pip install -r requirements.txt
```

## Running Single Device
In order to run the agent on a single device run the following
```
    python run_agent.py \
        --instruction_path /SWE-Agent/instructions/instruction.json \
        --log_type test \
        --main_device 1
```

## Running Distributed
In order to run the agent on the distributed setting run the following on the main device with your parameters
```
    python run_agent.py \
        --instruction_path /SWE-Agent/instructions/instruction.json \
        --log_type run_name \
        --main_device 1
```

Run the following on each coding agent device with your parameters
```
    python run_agent.py \
        --instruction_path /SWE-Agent/instructions/instruction.json \
        --device_config /SWE-Agent/instructions/device_config.json
        --distributed_config /SWE-Agent/instructions/distributed_config.json
        --log_type run_name \
        --main_device 0
```
