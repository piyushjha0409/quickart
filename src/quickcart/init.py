from langchain.tools import tool
from dotenv import load_dotenv

from .knowledge import search_kb

# Load OPENAI_API_KEY and the LANGSMITH_* settings from the project's .env file
load_dotenv()

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

tools = [add, multiply, search_kb]
tool_by_name={tool.name: tool for tool in tools}  # tool.name = add, tool.name=multiply
