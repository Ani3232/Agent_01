from ollama import chat
from check import MODEL
from main import ALLOWED_ROOT





def get_temperature(city: str) -> str:
    """Get the current temperaure for a city
    ARGS:
        city (str): The name of the city
        
    RETURNS:
        str: The current temperature for the city
        
    """
    temperature = {
        "New York": "15°C",
        "London": "10°C",
        "Paris": "12°C",
        "Tokyo": "20°C",
        "Sydney": "25°C"
    }
    return temperature.get(city, "City not found")

def read_file(file_path: str) -> str:
    """Read the content of a file
    ARGS:
        file_path (str): The path to the file
        
    RETURNS:
        str: The content of the file
    """
    
    if not file_path.startswith(ALLOWED_ROOT):
        return f"Error: Access to {file_path} is denied. Allowed root is {ALLOWED_ROOT}."
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"
    
def write_file(file_path: str, content: str) -> str:
    """Write content to a file
    ARGS:
        file_path (str): The path to the file
        content (str): The content to write to the file
        
    RETURNS:
        str: Confirmation message
    """
    
    if not file_path.startswith(ALLOWED_ROOT):
        return f"Error: Access to {file_path} is denied. Allowed root is {ALLOWED_ROOT}."
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Content written to {file_path} successfully."
    except Exception as e:
        return f"Error writing to file: {e}"
    
def delete_file(file_path: str) -> str:
    """Delete a file
    ARGS:
        file_path (str): The path to the file
        
    RETURNS:
        str: Confirmation message
    """
    ALLOWED_ROOT = r"C:\Users\Administrator\Desktop\code\swstk\workspace"
    if not file_path.startswith(ALLOWED_ROOT):
        return f"Error: Access to {file_path} is denied. Allowed root is {ALLOWED_ROOT}."
    
    import os
    if not os.path.exists(file_path):
        return f"File {file_path} does not exist."
    try:
        os.remove(file_path)
        return f"File {file_path} deleted successfully."
    except Exception as e:
        return f"Error deleting file: {e}"
    
def run_shell(command: str) -> str:
    import os
    import subprocess

    try:
        if os.name == "nt":  # Windows
            result = subprocess.run(
                command,
                cwd=ALLOWED_ROOT,          # restrict working directory
                shell=True,
                capture_output=True,
                text=True
            )
        else:  # Linux/macOS
            result = subprocess.run(
                command,
                cwd=ALLOWED_ROOT,
                shell=True,
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            return result.stdout
        return f"Error running command: {result.stderr}"

    except Exception as e:
        return f"Error running command: {e}"
    
    
GET_TEMPERATURE_SCHEMA = {
    "name": "get_temperature",
    "description": "Get the current temperature for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Name of the city"}
        },
        "required": ["city"]
    }
}

READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": "Read the content of a file.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"}
        },
        "required": ["file_path"]
    }
}

WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": "Write content to a file.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "content": {"type": "string", "description": "Content to write into the file"}
        },
        "required": ["file_path", "content"]
    }
}

DELETE_FILE_SCHEMA = {
    "name": "delete_file",
    "description": "Delete a file.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path of the file to delete"}
        },
        "required": ["file_path"]
    }
}

RUN_SHELL_SCHEMA = {
    "name": "run_shell",
    "description": "Run a shell command.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"}
        },
        "required": ["command"]
    }
}

TOOLS = {
    "get_temperature": {
        "function": get_temperature,
        "schema": GET_TEMPERATURE_SCHEMA
    },
    "read_file": {
        "function": read_file,
        "schema": READ_FILE_SCHEMA
    },
    "write_file": {
        "function": write_file,
        "schema": WRITE_FILE_SCHEMA
    },
    "delete_file": {
        "function": delete_file,
        "schema": DELETE_FILE_SCHEMA
    },
    "run_shell": {
        "function": run_shell,
        "schema": RUN_SHELL_SCHEMA
    }
}
