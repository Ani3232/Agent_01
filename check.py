import requests
import json
import sys
import os 
import subprocess
import time 
from ollama import chat
from termcolor import colored

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_URL  = f"{OLLAMA_BASE_URL}/v1/chat/completions"
MODEL           = "deepseek-r1:8b" # default model to use for the agent. You can change this to any model you have available in Ollama, or pull new models as needed.

# Getting model names for reference of the current installation of ollama.
def get_available_models():
    # Running "Ollama list" command in terminal and capturing the output to see what mdeols are there
    try:
        models_list = subprocess.run(["ollama","list"], capture_output=True, text=True)
        if models_list.returncode == 0:
            print(colored("[ x ]    ","green"), "Available models in Ollama:")
            print(models_list.stdout)
            lines = models_list.stdout.strip().split("\n")
            models = []
            for line in lines[1:]:
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            # print(colored("[ x ]    ","green"), f"Parsed models: {models}")
            return models   
        elif models_list.returncode != 0:
            print(colored("[ x ]    ","red"), f"Error running 'ollama list': {models_list.stderr}")
            return []
        
        # Parse the output to extract model names
        lines = models_list.strip().split("\n")
        models = []
        # Skip header line (first line) and process the rest
        for line in lines[1:]:
            if line.strip(): # Skip empty lines
                # Split by whitespaces and get the first column as mdoel name
                model_name = line.split()[0]
                models.append(model_name)
        return 
    except FileNotFoundError:
        print(colored("[ x ]    ","red"), "Ollama command not found. Please Ensure Ollama is installaed")
    except Exception as e:
        print(colored("[ x ]    ","red"), f"Error getting models list from Ollama: {e}")
        return []

# This function returns the model that has been selected from the list
def select_model_from_list(models):
    """ Displyy a list of models and prompt the user to select one."""
    if not models:
        print(colored("[ x ]    ","red"), "No models available to select from.")
        return MODEL
    print(colored("[ x ]    ","green"), "Available models:")
    print(colored("="*60, "yellow"))
    # Dispaly the models with numbers for selection
    for idx, model in enumerate(models, 1):
        print(colored(f"  {idx}.    |    ", "green") + f"{model}")
    print(colored("="*60, "yellow"))
    
    while True:
        try:
            selection = input(colored("[ ? ]     ","yellow") + "Enter model number to use or 0 to exit:  ")
            if selection.strip() == "0":
                print(colored("[ x ]    ","yellow"), "Exiting the selection..")
                return MODEL
            model_num = int(selection)
            if 1 <= model_num <= len(models):
                selected_model = models[model_num - 1]
                print(colored("[ x ]    ","green"), f"Selected model: [{selected_model}]")
                return selected_model
            else:
                print(colored("[ x ]    ","red"), f"Invalid selection. Please enter a number between 1 and {len(models)}, or 0 to exit.")
        except ValueError:
            print(colored("[ x ]    ","red"), "Invalid input. Please enter a valid number.")          

# FUnction to check what models are available and if i
def check_ollama_ready(selected_model="deepseek-r1:8b"):
    """Check if Ollama is running and the required mdoel is available."""
    try:
        # Check server health
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=60)
        r.raise_for_status()
        models = r.json().get("models",[])
        model_names = [m.get("name","") for m in models]
        model_exists = selected_model in model_names or any(
            name.startswith(selected_model.split(":")[0]) for name in model_names
        )
        if not model_exists:
            print(colored("[ x ]    ","red"),f"Model '{selected_model}' not found in Ollama. Available models: {model_names}")
            pull_model = input(colored("[ x ]    ","green"), f"Pull {selected_model}??: (y/N) ").strip().lower()
            if pull_model in ["y","yes", "Y"]:
                try:
                    print(colored("[ x ]    ","green"),f"Pulling model {selected_model} from Ollama...This may take some time.")
                    pull = subprocess.run(["ollama", "pull", selected_model], capture_output=True, text=True)
                    if pull.returncode == 0:
                        print(colored("[ x ]    ","green"),f"Model {selected_model} pulled successfully.")
                        return True
                    else:
                        print(colored("[ x ]    ","red"),f"Failed to pull model {selected_model}. Error: {pull.stderr}")
                        return False
                except FileNotFoundError:
                    print(colored("[ x ]    ","red"),f"Ollama command not found. Please ensure Ollama is installed and in your PATH.")
                    return False
                except Exception as e:
                    print(colored("[ x ]    ","red"), f"Error pulling model {selected_model}: {e}")
                    return False
            if pull_model in ["n","no", "N", "No", "NO"]:
                return False
        else:
            print(colored("[ x ]    ","green"), f"Model '{selected_model}' is set to run for this session.")
            return True
    except requests.exceptions.ConnectionError:
        print(colored("[ x ]    ","red"),"Ollama server is not running. Please start the Ollama server and try again.")
        return False
    except requests.exceptions.Timeout:
        print(colored("[ x ]    ","red"), "Ollama connection timed out. Please try again.")
        return False
    except requests.exceptions.HTTPError as err:
        print(colored("[ x ]    ","red"), f"Ollama HTTP error: {err}")
        return False
    except Exception as e:
        print(colored("[ x ]    ","red"), f"An error occurred while checking Ollama: {e}")
        return False
    
# Tracks the conversation and handles the streaming response from Ollama.
def stream_generate(model, messages,tools, think=False, stream=True, num_predict=1024, num_ctx=1024, temperature=0.7, top_p=0.9):
    """
    Streams responses from Ollama and handles:
    - thinking tokens
    - content tokens
    - history accumulation
    """

    stream = chat(
        model=model,
        messages=messages,
        tools=tools,
        think=think,
        stream=stream,
        options={
            "num_predict":num_predict,
            "num_ctx":num_ctx,
            "temperature":temperature,
            "top_p":top_p,
        }
    )

    tool_calls_detected = False
    in_thinking = False
    content = ""
    thinking = ""

    for chunk in stream:
        # Handle thinking tokens
        if getattr(chunk.message, "thinking", None):
            if not in_thinking:
                in_thinking = True
                print("Thinking...\n", flush=True)

            print(chunk.message.thinking, end="", flush=True)
            thinking += chunk.message.thinking

        # Handle regular tokens
        elif getattr(chunk.message, "content", None):
            if in_thinking:
                in_thinking = False
                print("\n\nAgent:\n", flush=True)
        

            print(chunk.message.content, end="", flush=True)
            content += chunk.message.content
                
    return {
        "thinking": thinking,
        "content": content,
        "tool_calls":tool_calls_detected
    }   
