# =====================================================
#          AGENT SETUP TRIAL - FIXED
# =====================================================
import json
import os
import ollama
import re
import uuid
import sys
import threading
import time
from datetime import datetime
from termcolor import colored 
from typing import List, Dict, Any, Optional
from tools import tools
from tools import read_file
from tools import write_file
from tools import delete_file
from tools import run_shell_command
from tools import list_directory
from tools import create_and_setup_venv
from tools import available_functions


class Spinner:
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.spinner_thread = None
    
    def spin(self):
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"  # Braille spinner characters
        i = 0
        while self.running:
            sys.stdout.write(f'\r{self.message} {chars[i % len(chars)]}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
    
    def start(self):
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop(self):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.5)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 2) + '\r')  # Clear line
        sys.stdout.flush()
        




class TrainingDataLogger:
    def __init__(self, workspace: str, format: str = "openai"):
        """
        format: "openai" or "sharegpt"
        """
        self.workspace = workspace
        self.format = format
        self.current_session = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.pending_tool_calls = {}  # Store tool calls waiting for results
        
        # Create training data file
        self.training_file = os.path.join(workspace, f"training_data_{format}.jsonl")
        
    def start_session(self, system_prompt: str):
        """Start a new conversation session"""
        self.current_session = []
        self.pending_tool_calls = {}
        
        if self.format == "openai":
            self.current_session.append({
                "role": "system",
                "content": system_prompt
            })
        # ShareGPT doesn't typically include system prompts
    
    def log_user_message(self, content: str):
        """Log user message"""
        if self.format == "openai":
            self.current_session.append({
                "role": "user",
                "content": content
            })
        else:  # sharegpt
            self.current_session.append({
                "from": "human",
                "value": content
            })
    
    def log_assistant_message(self, content: str, tool_calls: Optional[List[Dict]] = None):
        """
        Log assistant message with optional tool calls
        
        Args:
            content: The assistant's text response
            tool_calls: List of tool calls in the format:
                [{
                    "name": "tool_name",
                    "arguments": {"arg1": "value1", ...}
                }]
        """
        if self.format == "openai":
            message = {
                "role": "assistant",
                "content": content
            }
            
            if tool_calls:
                # Format tool calls according to OpenAI spec
                formatted_calls = []
                for i, tc in enumerate(tool_calls):
                    call_id = f"call_{uuid.uuid4().hex[:8]}"
                    
                    # Store for matching with results
                    self.pending_tool_calls[call_id] = {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                    
                    formatted_calls.append({
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"], ensure_ascii=False)
                        }
                    })
                
                message["tool_calls"] = formatted_calls
            
            self.current_session.append(message)
            
        else:  # sharegpt
            # ShareGPT doesn't have native tool support, so we'll add as text
            if tool_calls:
                tool_text = "\n\n[Tool Calls: " + ", ".join([
                    f"{tc['name']}({json.dumps(tc['arguments'])[:50]}...)" 
                    for tc in tool_calls
                ]) + "]"
                content += tool_text
            
            self.current_session.append({
                "from": "gpt",
                "value": content
            })
    
    def log_tool_result(self, content: str, tool_call_id: Optional[str] = None, tool_name: Optional[str] = None):
        """
        Log tool result message
        
        Args:
            content: The result from tool execution
            tool_call_id: ID of the tool call this result responds to (OpenAI format)
            tool_name: Name of the tool (used if tool_call_id not available)
        """
        if self.format == "openai":
            # If we don't have a call ID but have name, try to find matching pending call
            if not tool_call_id and tool_name:
                for cid, call in self.pending_tool_calls.items():
                    if call["name"] == tool_name:
                        tool_call_id = cid
                        break
            
            # If still no ID, generate one (fallback)
            if not tool_call_id:
                tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
            
            message = {
                "role": "tool",
                "content": content,
                "tool_call_id": tool_call_id
            }
            
            self.current_session.append(message)
            
            # Clean up pending call if we used it
            if tool_call_id in self.pending_tool_calls:
                del self.pending_tool_calls[tool_call_id]
                
        else:  # sharegpt
            # For ShareGPT, we'll format tool results as part of the conversation
            self.current_session.append({
                "from": "system",
                "value": f"[Tool Result: {content[:200]}...]"
            })
    
    def log_error(self, error_msg: str, tool_name: Optional[str] = None):
        """Log error message (helpful for training on error recovery)"""
        if self.format == "openai":
            self.current_session.append({
                "role": "tool",
                "content": f"ERROR: {error_msg}",
                "tool_call_id": f"error_{uuid.uuid4().hex[:8]}"
            })
        else:
            self.current_session.append({
                "from": "system",
                "value": f"[ERROR: {error_msg}]"
            })
    
    def end_session(self):
        """End current session and save to file"""
        # Check if there are any pending tool calls (shouldn't happen in good data)
        if self.pending_tool_calls and self.format == "openai":
            print(f"⚠️ Warning: {len(self.pending_tool_calls)} tool calls pending at session end")
            
            # Add placeholder results for incomplete calls
            for call_id, call in self.pending_tool_calls.items():
                self.current_session.append({
                    "role": "tool",
                    "content": f"[Tool {call['name']} was called but session ended before result]",
                    "tool_call_id": call_id
                })
        
        # Save session if it has at least one exchange
        if len(self.current_session) > 1:  # More than just system prompt
            if self.format == "openai":
                training_example = {"messages": self.current_session}
            else:  # sharegpt
                training_example = {"conversations": self.current_session}
            
            # Append to JSONL file
            with open(self.training_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
            
            print(f"✅ Session saved to {self.training_file}")
            return True
        
        return False
    
    def export_all_sessions(self, output_file: Optional[str] = None):
        """Export all logged sessions to a single file"""
        if not output_file:
            output_file = os.path.join(self.workspace, f"training_data_{self.format}.json")
        
        sessions = []
        try:
            with open(self.training_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sessions.append(json.loads(line))
        except FileNotFoundError:
            print(f"No training data found at {self.training_file}")
            return None
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(sessions)} sessions to {output_file}")
        return output_file
    
    def validate_session(self, session: List[Dict]) -> List[str]:
        """Validate a session for OpenAI format compliance"""
        issues = []
        
        if self.format != "openai":
            return issues
        
        for i, msg in enumerate(session):
            # Check tool calls have required fields
            if "tool_calls" in msg:
                for j, tc in enumerate(msg["tool_calls"]):
                    if "id" not in tc:
                        issues.append(f"Message {i}, tool call {j}: Missing 'id'")
                    if "type" not in tc or tc["type"] != "function":
                        issues.append(f"Message {i}, tool call {j}: 'type' must be 'function'")
                    if "function" not in tc:
                        issues.append(f"Message {i}, tool call {j}: Missing 'function'")
                    else:
                        if "name" not in tc["function"]:
                            issues.append(f"Message {i}, tool call {j}: Missing function.name")
                        if "arguments" not in tc["function"]:
                            issues.append(f"Message {i}, tool call {j}: Missing function.arguments")
            
            # Check tool results have matching call IDs
            if msg.get("role") == "tool":
                if "tool_call_id" not in msg:
                    issues.append(f"Message {i}: Tool result missing 'tool_call_id'")
        
        return issues 
    

class Agent:
    def __init__(self, model="qwen2.5:7b", workspace=r"C:\Users\Administrator\Desktop\code\swstk\workspace"):
        self.model = model
        self.workspace = workspace
        self.conversation = []
        self.plan_file = os.path.join(workspace, "agent_plan.json")
        self.max_steps = 10
        self.verification_steps = 2
        
        
        # Initialize datalogger
        self.training_logger = TrainingDataLogger(workspace,format="openai") # or sharegpt
        
        # Add system prompt on initialization
        self.add_system_prompt()
        
             
    def read_prompt(self, prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def add_system_prompt(self):
        """Add System prompt that defines system behaviour"""
        system_content = self.read_prompt(prompt_path=r"C:/Users/Administrator/Desktop/code/swstk/Architecture/agent.md")
        if system_content:
            system_prompt = {
                'role': 'system',
                'content': system_content
            }
            self.conversation.append(system_prompt)
            print("✅ System prompt added")
        else:
            # Fallback system prompt
            self.conversation.append({
                'role': 'system',
                'content': '''You are an autonomous AI agent. You can have normal conversations AND execute complex tasks.
                When given a task, break it down into steps and use available tools.
                After each tool execution, analyze the result and decide next steps.'''
            })
        
    def save_plan(self, plan):
        """Save plan to file for persistence"""
        with open(self.plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"📋 Plan saved to {self.plan_file}")
        
    def create_plan(self, task):
        """Ask the model to create a detailed plan"""
        plan_prompt = self.read_prompt(prompt_path=r"C:/Users/Administrator/Desktop/code/swstk/Architecture/plan.md")
        
        # If plan.md doesn't exist, use a default prompt
        if not plan_prompt:
            plan_prompt = f"""Create a detailed step-by-step plan for this task: {task}
            Return the plan as JSON with this structure:
            {{
                "task": "description",
                "steps": [
                    {{
                        "step": 1,
                        "description": "what to do",
                        "tool": "tool_name",
                        "arguments": {{"arg": "value"}},
                        "expected_outcome": "what should happen"
                    }}
                ],
                "verification": {{
                    "final_check": "how to verify",
                    "test_command": "command to test"
                }}
            }}
            """
        
        response = ollama.chat(
            model=self.model,
            messages=self.conversation + [{'role': 'user', 'content': plan_prompt}],
            tools=tools
        )
        
        # Extract plan from response
        try:
            # look for json in response
            json_match = re.search(r'\{.*\}', response.message.content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                self.save_plan(plan)
                return plan 
        except Exception as e:
            print(f"Error parsing plan: {e}")
            # Fallback - create a simple plan
            return {
                "task": task,
                "steps": [{
                    "step": 1,
                    "description": "Complete the task",
                    "tool": None,
                    "arguments": {},
                    "expected_outcome": "Task completed"
                }],
                "verification": {"final_check": "User confirms completion"}
            }
        
    def load_plan(self):
        """Load existing plan"""
        if os.path.exists(self.plan_file):
            with open(self.plan_file, 'r') as f:
                return json.load(f)
        return None
    
    def execute_step(self, step):
        """Execute Single step"""
        print(f"\n [x] Executing step {step['step']}: {step.get('description','')}")
        print(f"    Tool: {step['tool']}")
        print(f"    Arguments: {step.get('arguments', {})}")
        
        # Check if this step needs a tool
        if not step.get('tool'):
            return {
                'success': True,
                'result': "No tool needed for this step",
                'verification': {'verified': True, 'explanation': 'No verification needed'}
            }
        
        # call the appropriate tool
        if function_to_call := available_functions.get(step['tool']):
            try:
                result = function_to_call(**step['arguments'])
                result_str = str(result)
                
                # Add to conversation
                self.conversation.append({
                    'role': 'tool',
                    'name': step['tool'],
                    'content': result_str
                })
                
                # verify the step
                verification = self.verify_step(step, result_str)
                
                return {
                    'success': True,
                    'result': result_str,
                    'verification': verification
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            return {
                'success': False,
                'error': f"Tool {step['tool']} not found."
            }
            
    def verify_step(self, step, result):
        """verify if steps executed properly"""
        verification_prompt = f"""
        Step: {step.get('description', 'Unknown step')}
        Expected outcome: {step.get('expected_outcome', 'Not specified')}
        Actual result: {result}
        
        Did this step execute correctly? Answer YES or NO and explain why.
        """
        
        response = ollama.chat(
            model=self.model,
            messages=self.conversation + [{'role': 'user', 'content': verification_prompt}]
        )
        
        return {
            'verified': 'YES' in response.message.content.upper(),
            'explanation': response.message.content
        }
        
    def verify_final_result(self, plan):
        """Verify entire task"""
        if 'verification' not in plan:
            return {
                'verified': True,
                'explanation': 'No verification specified.'
            }
        verification = plan['verification']
        
        if 'test_command' in verification:
            # Run test command
            test_result = run_shell_command(verification['test_command'])
            
            verification_prompt = f"""
            Final verification: {verification.get('final_check', 'Check if task completed')}
            Test command: {verification['test_command']}
            Test result: {test_result}

            Did the task complete successfully? Answer YES or NO and explain.
            """
            
            response = ollama.chat(
                model=self.model,
                messages=self.conversation + [{'role': 'user', 'content': verification_prompt}]
            )
            
            return {
                'verified': 'YES' in response.message.content.upper(),
                'explanation': response.message.content,
                'test_result': test_result
            }
        
        return {'verified': True, 'explanation': 'Verification passed'}
    
    def update_plan(self, failed_step, error):
        """Update plan based on failure"""
        current_plan = self.load_plan()
        if not current_plan:
            return None
            
        update_prompt = f"""
        Step {failed_step['step']} failed with error: {error}

        Current plan: {json.dumps(current_plan, indent=2)}

        How should we update the plan to handle this failure?
        Options:
        1. Retry same step with different arguments
        2. Skip this step (if optional)
        3. Abort the task
        4. Try a different approach

        Provide updated plan JSON.
        """
        response = ollama.chat(
            model=self.model,
            messages=self.conversation + [{'role': 'user', 'content': update_prompt}]
        )
        
        # Extract and save updated plan
        try:
            json_match = re.search(r'\{.*\}', response.message.content, re.DOTALL)
            if json_match:
                updated_plan = json.loads(json_match.group())
                self.save_plan(updated_plan)
                return updated_plan
        except Exception as e:
            print(f"Error updating plan: {e}")
            return None
        
    def run_task(self, task):
        """Main agent loop"""
        print(f"\n🚀 Starting task: {task}")
        
        # Add task to conversation
        self.conversation.append({'role': 'user', 'content': task})
        
        # PHASE 1: PLANNING
        print("\n📝 PHASE 1: Creating plan...")
        plan = self.create_plan(task)
        if not plan:
            print("❌ Failed to create plan")
            return
        
        print(f"✅ Plan created with {len(plan.get('steps', []))} steps")
        
        # PHASE 2 & 3: EXECUTION & VERIFICATION
        print("\n⚙️ PHASE 2: Executing plan...")
        
        steps = plan.get('steps', [])
        current_step = 0
        
        while current_step < len(steps):
            step = steps[current_step]
            
            # Execute step
            result = self.execute_step(step)
            
            if result['success']:
                print(f"✅ Step {step['step']} completed")
                print(f"   Verification: {result['verification']['explanation']}")
                
                if result['verification']['verified']:
                    # Move to next step
                    steps[current_step]['status'] = 'completed'
                    current_step += 1
                else:
                    # Step executed but verification failed
                    print(f"⚠️ Step {step['step']} executed but verification failed")
                    # Ask model what to do
                    steps = self.handle_verification_failure(step, result, steps, current_step)
            else:
                # Step failed
                print(f"❌ Step {step['step']} failed: {result['error']}")
                # Update plan based on failure
                new_plan = self.update_plan(step, result['error'])
                if new_plan:
                    steps = new_plan.get('steps', [])
                    # Reset to appropriate step
                    current_step = max(0, current_step - 1)  # Go back one step
                else:
                    print("❌ Cannot recover from failure")
                    break
            
            # Save progress
            self.save_plan(plan)
        
        # PHASE 4: FINAL VERIFICATION
        print("\n🔍 PHASE 4: Verifying final result...")
        final_verification = self.verify_final_result(plan)
        
        if final_verification['verified']:
            print("\n🎉 TASK COMPLETED SUCCESSFULLY!")
            print(f"   {final_verification['explanation']}")
            
            # Add completion to conversation
            self.conversation.append({
                'role': 'assistant',
                'content': f"Task completed: {final_verification['explanation']}"
            })
        else:
            print("\n⚠️ TASK COMPLETED BUT VERIFICATION FAILED")
            print(f"   {final_verification['explanation']}")
            
            # Ask if user wants to iterate
            response = input("\n🔄 Try to fix? (y/n): ")
            if response.lower() == 'y':
                # Start over with new plan based on failure
                new_task = f"Fix the issues with previous attempt: {task}\nPrevious attempt failed because: {final_verification['explanation']}"
                self.run_task(new_task)
        
        return plan
    
    def handle_verification_failure(self, step, result, steps, current_step):
        """Handle case where step executed but verification failed"""
        prompt = f"""
        Step {step['step']} was executed but verification failed:
        Step: {step.get('description', 'Unknown')}
        Result: {result['result']}
        Verification: {result['verification']['explanation']}

        What should we do?
        1. Mark as complete anyway (if verification was too strict)
        2. Retry with different arguments
        3. Add an extra step to fix the issue
        4. Abort

        Provide updated steps array.
        """
        response = ollama.chat(
            model=self.model,
            messages=self.conversation + [{'role': 'user', 'content': prompt}]
        )
        
        # Parse response and return updated steps
        try:
            json_match = re.search(r'\[.*\]', response.message.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing verification failure response: {e}")
        
        # Default: continue but mark as completed
        steps[current_step]['status'] = 'completed_with_issues'
        return steps

    def process_message(self, user_input):
        """Process a message with automatic tool use - no intent detection needed"""
        
        
        # Add user message to conversation
        self.conversation.append({'role': 'user', 'content': user_input})
        
        iteration = 0
        max_iterations = 10
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get LLM response with tools always available
            response = ollama.chat(
                model=self.model,
                messages=self.conversation,
                tools=tools
            )
            
            # If no tool calls, we're done
            if not response.message.tool_calls:
                final_response = response.message.content
                # Add assistant response to conversation
                self.conversation.append({'role': 'assistant', 'content': final_response})
                return final_response
            
            # Handle tool calls - ONE AT A TIME to ensure proper format
            # Take ONLY the first tool call (enforce sequential execution)
            first_tool = response.message.tool_calls[0]
            
            # Log warning if multiple tools were requested
            if len(response.message.tool_calls) > 1:
                print(f"[x]    Model requested {len(response.message.tool_calls)} tools - processing sequentially")
            
            print(f"\n🔧 Using tool: {first_tool.function.name}")
            print(f"   Arguments: {first_tool.function.arguments}")
            
            # Add assistant message with tool call to conversation
            self.conversation.append({
                'role': 'assistant',
                'content': response.message.content,
                'tool_calls': [{
                    "id": f"call_{iteration}",
                    "type": "function",
                    "function": {
                        "name": first_tool.function.name,
                        "arguments": first_tool.function.arguments  # Stringify!
                    }
                }]
            })
            
            # Execute the tool
            if function_to_call := available_functions.get(first_tool.function.name):
                try:
                    result = function_to_call(**first_tool.function.arguments)
                    result_str = str(result)
                    
                    # Add tool result to conversation
                    self.conversation.append({
                        'role': 'tool',
                        'name': first_tool.function.name,
                        'content': result_str,
                        'tool_call_id':f"call_{iteration}"
                    })
                    
                    for n in result_str:
                        if n == "\n":
                            print("\n")
                        else:
                            print("n")
                    
                except Exception as e:
                    error_msg = f"Error executing tool: {str(e)}"
                    
                    # Add error to conversation
                    self.conversation.append({
                        'role': 'tool',
                        'name': first_tool.function.name,
                        'content': f"ERROR: {error_msg}",
                        'tool_call_id': f"call_{iteration}"
                    })
                    
                    print(f"   [x]   ERROR: {error_msg}")
            else:
                error_msg = f"Tool {first_tool.function.name} not found"
                
                # Log error for training
                self.training_logger.log_error(error_msg, first_tool.function.name)
                
                # Add error to conversation
                self.conversation.append({
                    'role': 'tool',
                    'name': first_tool.function.name,
                    'content': f"ERROR: {error_msg}",
                    'tool_call_id': f"call_{iteration}"
                })
                
                print(f"   [x] {error_msg}")
            
            # Loop continues with tool result added to conversation
            # The model will see the result and decide next action
        
        # If we hit max iterations
        timeout_msg = f"⚠️ Maximum iterations ({max_iterations}) reached without completing task"
        self.conversation.append({'role': 'assistant', 'content': timeout_msg})
        return timeout_msg
    
    def run(self):
        # =====================================================================
        #       Necessary Information Print Section
        # =====================================================================
        print(colored("\n\n","green"))
        """Main interactive loop"""
        """Print a nice header for the agent"""
        print("╔════════════════════════════════════╗")
        print("║     Agent Initialized              ║")
        print(f"║     Model: {self.model:<22}  ║")  # <22 left-aligns with 22 spaces
        print("╚════════════════════════════════════╝")
        print(colored("\n\n","green"))
        
        # Track if we're in an active session
        in_session = False
        
        try:
            while True:
                user_input = input(colored("┌─You       : ","green"))
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    # End current session before exiting
                    if in_session:
                        self.training_logger.end_session()
                    print("👋 Goodbye!")
                    break
                
                if not user_input.strip():
                    continue
                
                spinner = Spinner(colored("└─Assistant : ","green"))
                spinner.start()
                # Process the message
                response = self.process_message(user_input)
                spinner.stop()
                print( colored("└─Assistant : ","green")+f"{response}")
                
                # Optional: End session after each complete task?
                # You could add logic here to detect when a task is complete
        
        except KeyboardInterrupt:
            if in_session:
                self.training_logger.end_session()
            print(colored("Goodbye...","green"))

