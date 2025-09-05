from typing import TypedDict, Literal, Annotated, Sequence
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage | SystemMessage], operator.add]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    weather_data = {
        "london": "Cloudy with light rain, 15°C",
        "paris": "Sunny and warm, 22°C", 
        "new york": "Partly cloudy, 18°C",
        "tokyo": "Clear skies, 25°C"
    }
    location_lower = location.lower()
    if location_lower in weather_data:
        return f"The weather in {location} is {weather_data[location_lower]}"
    else:
        return f"The weather in {location} is sunny with 20°C (mock data)"

def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Search results for '{query}': Here are some relevant articles and information about {query}. This is mock data - in a real implementation, this would connect to a search API."

def calculate_math(expression: str) -> str:
    """Calculate mathematical expressions safely."""
    try:
        allowed_chars = set('0123456789+-*/().,= ')
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"The result of {expression} is {result}"
        else:
            return "Invalid mathematical expression. Only basic arithmetic operations are allowed."
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"

tools = [get_weather, search_web, calculate_math]
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    """The main agent reasoning node."""
    messages = state["messages"]
    
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        system_msg = SystemMessage(content="""You are a helpful AI assistant with access to several tools:

1. get_weather(location): Get weather information for any location
2. search_web(query): Search the web for information 
3. calculate_math(expression): Perform mathematical calculations

Use these tools when appropriate to help answer user questions. Always be helpful and provide detailed, accurate responses.""")
        messages = [system_msg] + list(messages)
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def tool_node(state: AgentState):
    """Execute tools when the agent calls them."""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_results = []
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name == "get_weather":
                result = get_weather(**tool_args)
            elif tool_name == "search_web":
                result = search_web(**tool_args)
            elif tool_name == "calculate_math":
                result = calculate_math(**tool_args)
            else:
                result = f"Unknown tool: {tool_name}"
            
            tool_message = ToolMessage(
                content=result,
                tool_call_id=tool_call["id"]
            )
            tool_results.append(tool_message)
    
    return {"messages": tool_results}

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return "end"

# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)
workflow.add_edge("tools", "agent")

# Compile the graph
graph = workflow.compile()