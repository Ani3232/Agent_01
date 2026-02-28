import ollama 
import yfinance as yf
from typing import Dict, Any, Callable, List
from main import ALLOWED_ROOT
import os

def get_stock_price(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    return ticker.info.get('regularMarketPrice') or ticker.fast_info.last_price

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
    
    # Normalize both paths to resolve any inconsistencies
    normalized_file_path = os.path.normpath(file_path)
    normalized_allowed_root = os.path.normpath(ALLOWED_ROOT)
    
    # Check if the normalized path starts with the normalized allowed root
    # Also handle case-insensitivity on Windows
    if os.name == "nt":  # Windows
        if not normalized_file_path.lower().startswith(normalized_allowed_root.lower()):
            return f"Error: Access to {file_path} is denied. Allowed root is {ALLOWED_ROOT}."
    else:  # Linux/macOS (case-sensitive)
        if not normalized_file_path.startswith(normalized_allowed_root):
            return f"Error: Access to {file_path} is denied. Allowed root is {ALLOWED_ROOT}."
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(normalized_file_path), exist_ok=True)
    
    try:
        with open(normalized_file_path, "w", encoding="utf-8") as f:
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
    
    # Normalize the path to resolve any '..' or '.' components
    normalized_path = os.path.normpath(file_path)
    
    if not normalized_path.startswith(ALLOWED_ROOT):
        return f"Error: Access to {file_path} is denied. Allowed root is {ALLOWED_ROOT}."
    
    if not os.path.exists(normalized_path):
        return f"File {normalized_path} does not exist."
    
    # Extra safety: check if it's a file (not a directory)
    if os.path.isdir(normalized_path):
        return f"Error: {normalized_path} is a directory. Cannot delete directories."
    
    try:
        os.remove(normalized_path)
        return f"File {normalized_path} deleted successfully."
    except Exception as e:
        return f"Error deleting file: {e}"


def create_and_setup_venv(workspace_path: str, packages=None) -> str:
    """Create a virtual environment and optionally install packages
    ARGS:
        workspace_path (str): Path where to create the venv
        packages (list or str): List of packages to install (optional)
        
    RETURNS:
        str: Status message
    """
    import os
    import subprocess
    import sys
    import ast  # Add this for safe parsing
    
    # Normalize the path
    workspace_path = os.path.normpath(workspace_path)
    venv_path = os.path.join(workspace_path, "venv")
    
    # Security check
    if not workspace_path.startswith(ALLOWED_ROOT):
        return f"Error: Access to {workspace_path} is denied. Allowed root is {ALLOWED_ROOT}."
    
    try:
        # Step 1: Create virtual environment
        print(f"Creating virtual environment at {venv_path}...")
        result = subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return f"Error creating venv: {result.stderr}"
        
        # Step 2: Determine pip path
        if os.name == "nt":  # Windows
            pip_path = os.path.join(venv_path, "Scripts", "pip")
            activate_script = os.path.join(venv_path, "Scripts", "activate")
        else:  # Linux/macOS
            pip_path = os.path.join(venv_path, "bin", "pip")
            activate_script = os.path.join(venv_path, "bin", "activate")
        
        # Step 3: Upgrade pip
        print("Upgrading pip...")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], 
                      capture_output=True, text=True)
        
        # Step 4: Parse and install packages
        if packages:
            # Handle different input types
            if isinstance(packages, str):
                # Try to parse if it's a string representation of a list
                packages_str = packages.strip()
                if packages_str.startswith('[') and packages_str.endswith(']'):
                    try:
                        # Safely evaluate the string as a Python literal
                        packages = ast.literal_eval(packages_str)
                    except (SyntaxError, ValueError):
                        # If parsing fails, split by common delimiters
                        packages = [p.strip(' "\'[]') for p in packages_str.replace('[', '').replace(']', '').split(',')]
                else:
                    # Single package
                    packages = [packages_str]
            
            # Ensure packages is a list and clean up any quotes
            if not isinstance(packages, list):
                packages = [str(packages)]
            
            # Clean up package names (remove quotes, brackets, etc.)
            clean_packages = []
            for p in packages:
                if isinstance(p, str):
                    # Remove quotes and brackets
                    p = p.strip().strip('"\'').strip('[]')
                    if p and not p.startswith('['):  # Avoid empty strings and nested lists
                        clean_packages.append(p)
            
            if clean_packages:
                print(f"Installing packages: {', '.join(clean_packages)}...")
                result = subprocess.run(
                    [pip_path, "install"] + clean_packages,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    return (f"⚠️ Venv created but error installing packages: {result.stderr}\n"
                           f"📍 Venv path: {venv_path}")
                
                return (f"✅ Virtual environment created successfully at {venv_path}\n"
                       f"✅ Packages installed: {', '.join(clean_packages)}\n"
                       f"💡 To activate: {activate_script}")
            else:
                return (f"✅ Virtual environment created successfully at {venv_path}\n"
                       f"⚠️ No valid packages to install\n"
                       f"💡 To activate: {activate_script}")
        else:
            return (f"✅ Virtual environment created successfully at {venv_path}\n"
                   f"💡 To activate: {activate_script}")
    
    except Exception as e:
        return f"Error: {str(e)}"


def run_shell(command: str) -> str:
    """Run a shell command (use with caution)"""
    import os
    import subprocess

    try:
        # Security check - only allow commands in ALLOWED_ROOT
        if os.name == "nt":  # Windows
            result = subprocess.run(
                command,
                cwd=ALLOWED_ROOT,
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
    

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price for a given ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., AAPL for Apple, MSFT for Microsoft)",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_temperature",
            "description": "Get the current temperature for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city (e.g., Paris, London, New York)",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the allowed workspace directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The full path to the file to read",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the allowed workspace directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The full path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    }
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file from the allowed workspace directory (requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The full path to the file to delete",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_and_setup_venv",
            "description": "Create a Python virtual environment and install data science packages",
            "parameters": {
                "type": "object",
                "properties": {
                    "workspace_path": {
                        "type": "string",
                        "description": "The path where to create the virtual environment",
                    },
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Python packages to install (e.g., pandas, numpy, matplotlib)",
                    }
                },
                "required": ["workspace_path"],
            },
        },
    },
]


prompt_1 ='What is the current stock price of Apple?'
prompt_2 = 'What is the current temperature of Paris?'
prompt_3 = r'What is inside the file C:\Users\Administrator\Desktop\code\swstk\workspace\test_deepseek.txt ??'
prompt_4 = r'open the file C:\Users\Administrator\Desktop\code\swstk\workspace\test_deepseek.txt and then append a md formatted text there describing Recursion in python'
prompt_5 = r'Delete the file C:\Users\Administrator\Desktop\code\swstk\workspace\test_deepseek.txt '
prompt_6 = r'Create a venv in C:\Users\Administrator\Desktop\code\swstk\workspace folder and then install the libraries needed for begineer dataanalytics engineer in that using pip and run_shell'
prompt_7 = r'Write a file at C:\Users\Administrator\Desktop\code\swstk\workspace named main.py that has a class based implementation of a neural network'

available_functions         :   Dict[str, Callable] = {
    'get_stock_price'       :   get_stock_price,
    'get_temperature'       :   get_temperature,
    'read_file'             :   read_file,
    'write_file'            :   write_file,
    'delete_file'           :   delete_file,
    'run_shell'             :   run_shell,
    'create_and_setup_venv' :   create_and_setup_venv,
}

response = ollama.chat(
    'llama3.2',
    messages=[{
        'role':'user',
        'content':prompt_7
    }],
    tools=tools,
)


if response.message.tool_calls:
    for tool in response.message.tool_calls:
        if function_to_call := available_functions.get(tool.function.name):
            print('Calling function:', tool.function.name)
            print('Arguments:', tool.function.arguments)
            print('Function Output:', function_to_call(**tool.function.arguments))
        else:
            print('Function', tool.function.name, 'not found')