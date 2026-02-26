from check import get_available_models
from check import select_model_from_list
from check import stream_generate
from check import check_ollama_ready
from check import colored
from check import MODEL

ALLOWED_ROOT = r"C:\Users\Administrator\Desktop\code\swstk\workspace"

class user:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    

def main():
    models = get_available_models()
    
    selected_model = select_model_from_list(models)
    
    if not selected_model:
        print(colored("[ x ]    ", "cyan"), f"No model selected. Using default model [{MODEL}].")
        
    if not check_ollama_ready(selected_model):
        return 
    
    user_1 = user("Ani","Engineering student who is interested in mechatronics, software, mechanical simulations, real world computation models and real world interaction with technology.")
    
    while True:
        user_input = input(f"\n\n{user_1.name} : ").strip()
        if user_input.lower() in ['exit', 'quit', 'bye','close']:
            break
        
        think = True
        messages = [{"role"    : "system", "content": f"Your name is {MODEL} and you are an engineering assigtant, and the person you are talking to is {user_1.name}. And he is a  {user_1.description}. Delault language English."},
                    {"role"    : "user",   "content" : user_input}]
        
        result = stream_generate(selected_model, messages)
        
        # History handling optionsl
        # store result ["thinking"], result["content"]


if __name__ == "__main__":
    main()