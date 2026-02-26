

import requests
import json
import sys
import time
from termcolor import colored

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = "deepseek-r1:8b"

def check_ollama_ready():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            print(colored("[ x ]", "red"), "Ollama server not responding")
            return False
        
        models = response.json().get('models', [])
        model_exists = any(m['name'].startswith(MODEL.split(':')[0]) for m in models)
        
        if not model_exists:
            print(colored("[ x ]", "red"), f"Model {MODEL} not found. Pulling it now...")
            import subprocess
            subprocess.run(["ollama", "pull", MODEL])
            print(colored("[ x ]", "green"), "Model pulled successfully")
        
        return True

    except requests.exceptions.ConnectionError:
        print(colored("[ x ]", "red"), "Cannot connect to Ollama. Run 'ollama serve'")
        return False


def stream_generate(conversation):
    
    # This is the Payloads construction. These are the specifics needed for this ollama (OpenAI API) to work
    # "model"   :   selects the model from the list of models
    # "messages":   conversations sets it to conversation mode
    # "stream"  :   Sets token streaming toggle on
    # "options" :   Model operation settings 
    payload = {
        "model": MODEL,
        "messages": conversation,
        "stream": True,
        "options": {
            "temperature": 0.8,
            "top_p" : 0.9,
            "repeat_penalty": 1.2,
            "num_ctx" : 8192,
            "num_predict": 500
        }
    }

    # Stores the complete assistant reply while tokens are streamed
    full_response = ""

    # State Variable
    
    in_code_block = False
    
    
    # try except setup if in case fails
    try:
        # Sending the requests
        # Sends POST request
        # stream=True --> Do not wait for full response stream what is currently available
        # Opens a streaming HTTP connection
        # timeout=60 abort if it takes more than 60 sec
        
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60) as r:
            
            # raises ERROR is the HTTP ststus != 200
            r.raise_for_status()

            # Token Streaming loop:
            print(colored("SWSTK  :  ","green"), flush=True)
            for line in r.iter_lines():
                
                # If no line is found then go for the next line this one is a line gap
                if not line:
                    continue
                
                # Cleaning the line and using proper Encoding.
                line = line.decode("utf-8")

                
                # This removes the prefixes for printing
                if line.startswith("data: "):
                    line = line[6:]

                # When the server ends the response it sends this keyword [DONE]
                # So this lines ends the response and gets ready to get the users text.
                if line.strip() == "[DONE]":
                    break
                
                # This line tryies to get lines from the user, one line at a time no line breaking 
                # or line gaps are allowed in this setup
                try:
                    
                    # Here each line input is taken as data
                    # Then delta(the streaming response is made)
                    # {
                    #    "choices" : {
                    #           "delta": {
                    #               "content":"Hello"    
                    #            }   
                    #    }
                    # }
                    # So token = delta["content"]
                    # Then each token is appended
                    # full_response += token
                    # And printed live 
                    # print(token, end="", flush=True)
                    
                    data = json.loads(line)
                    delta = data["choices"][0]["delta"]
                    if "content" in delta:
                        token = delta["content"]
                        full_response += token
                        if "```" in token:
                            in_code_block = not in_code_block
                            print(colored(token, "blue"), end="\n", flush=True)
                            
                        else:
                            if in_code_block:
                                print(colored(token, "blue"), end="", flush=True)
                            else:
                                print(token, end="", flush=True)

                except json.JSONDecodeError:
                    continue

            print("")
            
        # This is the final response returned as the full answer for context/conversation history
        return full_response

    except Exception as e:
        print(colored("[ x ]", "red"), f"Error: {e}")
        return ""


# This is the model behvbioral setup
# And guides the response structure of the model
# And injected at the start of every conversation starting
def load_mode(path="Architecture/chat.md"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(colored("[ x ]    ","red"), "SOUL.md not found.")
        return ""
    
    


def main():
    if not check_ollama_ready():
        return

    # ==================================================================
    #                  MODE SELECTION
    # ==================================================================
   
    
    time.sleep(1)

    print(colored("Interactive Chat Started (type 'exit 0' to quit)\n", "cyan"))

    soul = load_mode()
    conversation = []
    if soul:
        conversation.append({
            "role":"system", "content":soul})
    
    
    while True:
        user_input = input(colored("ANI    :  \n","green"))

        if user_input.strip().lower() == "exit 0":
            print("Exiting...")
            break

        conversation.append({"role": "user", 
                             "content": f"{user_input}\n\n[Follow the system constitution strictly.]"
                             })

        response = stream_generate(conversation)

        conversation.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()