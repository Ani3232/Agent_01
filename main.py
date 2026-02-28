import os
from agent import Agent
from agent import TrainingDataLogger




# =====================================================
#          MAIN EXECUTION
# =====================================================

if __name__ == "__main__":
    # Create an instance of the Agent
    agent = Agent(
        model='qwen2.5:7b',  # or whatever model you want to use
        workspace=r"C:\Users\Administrator\Desktop\code\swstk\workspace"
    )
    
    # Run the agent (this starts the interactive loop)
    agent.run()
    
    