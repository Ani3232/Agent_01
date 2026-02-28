import os
import json
import ollama
import subprocess
import shlex
import yfinance as yf
from typing import Dict, Any, Callable
from ollama import chat
from check import MODEL
from config import ALLOWED_ROOT


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

    
def write_file(file_path, content):
    """
    Write content to a file
    """
    import os

    # Enhanced debug
    print(f"🔴 DEBUG - Received content: {repr(content)}")
    print(f"🔴 DEBUG - Content length: {len(content)}")
    print(f"🔴 DEBUG - First 20 chars: {repr(content[:20])}")
    print(f"🔴 DEBUG - Last 20 chars: {repr(content[-20:]) if len(content) > 20 else 'too short'}")
    
    allowed_root = r"C:\Users\Administrator\Desktop\code\swstk\workspace"
    normalized_path = os.path.abspath(os.path.normpath(file_path))
    normalized_root = os.path.abspath(os.path.normpath(allowed_root))
    
    # Security check
    if not normalized_path.lower().startswith(normalized_root.lower()):
        return f"Error: Access denied"
    
    try:
        # Write the file
        with open(normalized_path, 'w') as f:
            f.write(content)
        
        # Verify by reading back
        with open(normalized_path, 'r') as f:
            written_content = f.read()
        
        print(f"🔴 DEBUG - Written content: {repr(written_content)}")
        print(f"🔴 DEBUG - Match? {written_content == content}")
        
        if written_content != content:
            return f"⚠️ WARNING: Written content doesn't match!\nExpected: {repr(content[:50])}...\nActual: {repr(written_content[:50])}..."
        
        return f"✅ Content written to {file_path} successfully. ({len(content)} bytes)"
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"


def read_file(file_path):
    """
    Read content from a file
    """
    import os
    
    print(f"🔵 DEBUG - Reading file: {file_path}")
    
    allowed_root = r"C:\Users\Administrator\Desktop\code\swstk\workspace"
    normalized_path = os.path.abspath(os.path.normpath(file_path))
    normalized_root = os.path.abspath(os.path.normpath(allowed_root))
    
    # Security check
    if not normalized_path.lower().startswith(normalized_root.lower()):
        return f"Error: Access denied"
    
    try:
        with open(normalized_path, 'r') as f:
            content = f.read()
        
        print(f"🔵 DEBUG - Read content: {repr(content)}")
        print(f"🔵 DEBUG - Content length: {len(content)}")
        
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
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

def run_shell_command(command, cwd=None):
    """
    Run a shell command and return the output
    """
    # Security: Only allow commands in the workspace
    allowed_root = r"C:\Users\Administrator\Desktop\code\swstk\workspace"
    
    # Set working directory to workspace if not specified
    if not cwd:
        cwd = allowed_root
    
    # Basic security: prevent dangerous commands
    dangerous_commands = ['rm -rf', 'del /f', 'format', 'diskpart']
    for dangerous in dangerous_commands:
        if dangerous in command.lower():
            return f"Error: Command '{command}' contains dangerous operations and was blocked"
    
    try:
        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        if result.returncode != 0:
            output += f"Command exited with code: {result.returncode}"
        
        return output if output else "Command executed successfully (no output)"
    
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def list_directory(dir_path):
    """
    List contents of a directory
    """
    import os
    
    # Define allowed root
    allowed_root = r"C:\Users\Administrator\Desktop\code\swstk\workspace"
    
    # Normalize paths
    normalized_path = os.path.abspath(os.path.normpath(dir_path))
    normalized_root = os.path.abspath(os.path.normpath(allowed_root))
    
    # Security check
    if not normalized_path.lower().startswith(normalized_root.lower()):
        return f"Error: Access to {dir_path} is denied. Allowed root is {allowed_root}"
    
    # Check if it's a directory
    if not os.path.isdir(normalized_path):
        return f"Error: {dir_path} is not a directory"
    
    # List contents
    try:
        items = os.listdir(normalized_path)
        files = []
        directories = []
        
        for item in items:
            full_path = os.path.join(normalized_path, item)
            if os.path.isfile(full_path):
                files.append(item)
            else:
                directories.append(item)
        
        result = f"Directory: {dir_path}\n"
        result += f"Subdirectories ({len(directories)}): {', '.join(directories) if directories else 'None'}\n"
        result += f"Files ({len(files)}): {', '.join(files) if files else 'None'}"
        
        return result
    except Exception as e:
        return f"Error listing directory: {str(e)}"


    
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
                "required": ["symbol"],  # ← Back to list format
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
                "required": ["city"],  # ← Back to list format
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
                "required": ["file_path"],  # ← Back to list format
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
                "required": ["file_path", "content"],  # ← List of strings
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
                "required": ["file_path"],  # ← Back to list format
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
                "required": ["workspace_path"],  # ← List format
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_directory',
            'description': 'List contents of a directory',
            'parameters': {
                'type': 'object',
                'properties': {
                    'dir_path': {
                        'type': 'string',
                        'description': 'Path to the directory to list'
                    }
                },
                'required': ["dir_path"]  # ← List format
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'run_shell_command',
            'description': 'Run a shell command in the workspace directory',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'description': 'The shell command to run. For venv: use "C:\\\\path\\\\to\\\\venv\\\\Scripts\\\\python.exe script.py" or combine: "cd workspace && venv\\\\Scripts\\\\activate && python script.py"'
                    }
                },
                'required': ["command"]  # ← List format (and fixed placement!)
            }
        }
    }
]


available_functions         :   Dict[str, Callable] = {
    'get_temperature'       :   get_temperature,
    'read_file'             :   read_file,
    'write_file'            :   write_file,
    'delete_file'           :   delete_file,
    'create_and_setup_venv' :   create_and_setup_venv,
    'run_shell_command'     :   run_shell_command,
    'list_directory'        :   list_directory
}


