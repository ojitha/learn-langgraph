from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START

# GraphState
class State(TypedDict):
    topic: str
    poem: str
    improved_poem: str
    final_poem: str

# Nodes
def generate_poem(state: State) -> State:
    # Generate a poem based on the topic
    msg = llm.invoke(f"Write a poem about {state['topic']}")
    state['poem'] = msg.content
    return state

def improve_poem(state: State) -> State:
    # Improve the poem
    msg = llm.invoke(f"Improve this poem: {state['poem']}")
    state['improved_poem'] = msg.content
    return state

def finalize_poem(state: State) -> State:
    # Finalize the poem
    msg = llm.invoke(f"Finalize this poem: {state['improved_poem']}")
    state['final_poem'] = msg.content
    return state

def check_poem(state: State) -> str:
    # Check the poem
    msg = llm.invoke(f"Is this poem is good or bad?: {state['poem']}")
    if "poem is good" in msg.content:
        return "Fail"
    else:
        return "Pass"
    

# Create LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
# Build workflow
workflow = StateGraph(State)

workflow.add_node("generate_poem", generate_poem)
workflow.add_node("improve_poem", improve_poem)
workflow.add_node("finalize_poem", finalize_poem)

workflow.add_edge(START, "generate_poem")
workflow.add_conditional_edges("generate_poem"
    , check_poem, {"Pass": "improve_poem", "Fail": END})
workflow.add_edge("improve_poem", "finalize_poem")
workflow.add_edge("finalize_poem", END)

graph = workflow.compile()    