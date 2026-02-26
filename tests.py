import requests
import json
import sys
import os 
import subprocess
import time 
from ollama import chat
from termcolor import colored
from ollama import chat
from check import MODEL
from check import get_available_models
from check import select_model_from_list
from check import stream_generate
from check import check_ollama_ready
from tools import get_temperature
from tools import read_file 
from tools import write_file
from tools import delete_file
from tools import run_shell  
from tools import TOOLS
from termcolor import colored




from tools import TOOLS

# message to write a file
write_message = {
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "function": {
                "name": "write_file",
                "arguments": {
                    "file_path": r"C:\Users\Administrator\Desktop\code\swstk\workspace\test.txt",
                    "content": "Hello from tool test"
                }
            }
        }
    ]
}

# execute write
tool_messages = []
if "tool_calls" in write_message and write_message["tool_calls"]:
    for call in write_message["tool_calls"]:
        name = call["function"]["name"]
        args = call["function"]["arguments"]
        result = TOOLS[name]["function"](**args)
        tool_messages.append({"role": "tool", "name": name, "content": str(result)})

"""print("WRITE RESULT:")
for m in tool_messages:
    print(m["content"])"""
    
if tool_messages and "successfully" in tool_messages[-1]["content"].lower():
    print(colored("[ x ] Write test passed!", "green"))

# read file
read_message = {
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "function": {
                "name": "read_file",
                "arguments": {
                    "file_path": r"C:\Users\Administrator\Desktop\code\swstk\workspace\test.txt"
                }
            }
        }
    ]
}

tool_messages = []
if "tool_calls" in read_message and read_message["tool_calls"]:
    for call in read_message["tool_calls"]:
        name = call["function"]["name"]
        args = call["function"]["arguments"]
        result = TOOLS[name]["function"](**args)
        tool_messages.append({"role": "tool", "name": name, "content": str(result)})

"""print("\nREAD RESULT:")
for m in tool_messages:
    print(m["content"])"""

if tool_messages and tool_messages[-1]["content"] == "Hello from tool test":
    print(colored("[ x ] Read test passed!", "green"))

# delete file
delete_message = {
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "function": {
                "name": "delete_file",
                "arguments": {
                    "file_path": r"C:\Users\Administrator\Desktop\code\swstk\workspace\test.txt"
                }
            }
        }
    ]
}

tool_messages = []
if "tool_calls" in delete_message and delete_message["tool_calls"]:
    for call in delete_message["tool_calls"]:
        name = call["function"]["name"]
        args = call["function"]["arguments"]
        result = TOOLS[name]["function"](**args)
        tool_messages.append({"role": "tool", "name": name, "content": str(result)})

"""print("\nDELETE RESULT:")
for m in tool_messages:
    print(m["content"])"""

if tool_messages and "deleted successfully" in tool_messages[-1]["content"].lower():
    print(colored("[ x ] Delete test passed!", "green"))

# dir check
dir_message = {
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "function": {
                "name": "run_shell",
                "arguments": {"command": "dir"}
            }
        }
    ]
}

tool_messages = []
if "tool_calls" in dir_message and dir_message["tool_calls"]:
    for call in dir_message["tool_calls"]:
        name = call["function"]["name"]
        args = call["function"]["arguments"]
        result = TOOLS[name]["function"](**args)
        tool_messages.append({"role": "tool", "name": name, "content": str(result)})

"""print("\nDIR RESULT:")
for m in tool_messages:
    print(m["content"])"""