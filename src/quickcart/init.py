from langchain.tools import tool
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

# Load OPENAI_API_KEY and the LANGSMITH_* settings from the project's .env file
load_dotenv()

model = init_chat_model(
    "gpt-5-nano",
     temperature=0
)

# Define the basic tools
@tool
def add(a: int, b: int):
   """Add a and b."""
   return a+b

@tool
def multiply(a:int, b:int):
   """Multiply a and b."""
   return a*b


#making an array for all the tools

tools = [add, multiply]
tool_by_name={tool.name: tool for tool in tools}  # tool.name = add, tool.name=multiply
model_with_tools = model.bind_tools(tools)
