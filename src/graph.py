import os
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from src.kb_manager import get_vector_store, get_schema_summary
from src.sandbox import run_analytics_code

from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from src.kb_manager import get_vector_store, get_schema_summary
from src.sandbox import run_analytics_code

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing from .env")

llm = ChatGoogleGenerativeAI(
    model=os.getenv("DEFAULT_MODEL", "gemini-3.8-flash"),
    google_api_key=api_key,
    temperature=0
)


# Define Graph State
class AgentState(TypedDict):
    user_query: str
    retrieved_knowledge: str
    schema_summary: str
    generated_code: str
    execution_output: str
    execution_error: str
    chart_path: str
    retry_count: int
    final_answer: str

def retrieve_node(state: AgentState):
    """Step 1: Retrieve relevant business definitions from ChromaDB vector store."""
    print("--- [NODE] Retrieving Knowledge & Schema ---")
    query = state["user_query"]
    
    try:
        vector_store = get_vector_store()
        docs = vector_store.similarity_search(query, k=2)
        retrieved_text = "\n".join([d.page_content for d in docs])
    except Exception as e:
        retrieved_text = "No specific glossary rules retrieved."
        
    schema = get_schema_summary()
    
    return {
        "retrieved_knowledge": retrieved_text,
        "schema_summary": schema
    }

def code_generation_node(state: AgentState):
    """Step 2: Generate Python/Pandas code adhering to the schema and business glossary."""
    print("--- [NODE] Generating Analysis Code ---")
    
    query = state["user_query"]
    knowledge = state["retrieved_knowledge"]
    schema = state["schema_summary"]
    error = state.get("execution_error", "")
    code = state.get("generated_code", "")
    
    prompt = f"""You are an expert Python Data Analyst and Data Scientist agent.
Your goal is to write clean, executable Python code using pandas, duckdb, and matplotlib to answer the user's question.

### Database Schema & Sample Data:
{schema}

### Relevant Business Glossary & Rules (MUST OBEY):
{knowledge}

### User Question:
{query}
"""

    if error:
        prompt += f"""
---
Your previous code failed with this error:
{code}

Error Traceback:
{error}

Please fix the bug, write corrected Python code, and make sure not to repeat the error.
"""
    else:
        prompt += """
---
Instructions:
1. Use `customers` and `orders` DataFrames or query them via DuckDB.
2. Adhere strictly to the Business Glossary rules (e.g., currency conversion, excluding test accounts or uncompleted orders where required).
3. Print out the final answer clearly using `print()`.
4. If a visualization is appropriate, generate and save it using `plt.savefig('outputs/charts/latest_analysis.png')`.
5. Return ONLY executable Python code inside standard markdown code blocks (```python ... ```). Do not include conversational filler.
"""

    messages = [
        SystemMessage(content="You are a precise data analytics coding assistant. Output only Python code blocks."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Robustly handle content whether it's a string or a list of blocks
    if isinstance(content, list):
        text_content = "".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in content])
    else:
        text_content = str(content)
    
    # Extract code block
    if "```python" in text_content:
        code_str = text_content.split("```python")[1].split("```")[0].strip()
    elif "```" in text_content:
        code_str = text_content.split("```")[1].split("```")[0].strip()
    else:
        code_str = text_content.strip()
        
    return {
        "generated_code": code_str,
        "retry_count": state.get("retry_count", 0) + 1
    }

def execution_node(state: AgentState):
    """Step 3: Execute the generated code in the secure sandbox."""
    print("--- [NODE] Executing Code in Sandbox ---")
    code = state["generated_code"]
    
    result = run_analytics_code(code)
    
    return {
        "execution_output": result["output"],
        "execution_error": result["error"],
        "chart_path": result["chart_path"]
    }

def evaluation_router(state: AgentState):
    """Step 4: Check if execution succeeded or if we need to retry (self-correction)."""
    if not state["execution_error"]:
        return "success"
    if state["retry_count"] >= 3:
        return "max_retries"
    return "retry"

def synthesis_node(state: AgentState):
    """Step 5: Synthesize final executive answer."""
    print("--- [NODE] Synthesizing Final Answer ---")
    query = state["user_query"]
    output = state["execution_output"]
    error = state["execution_error"]
    
    if error and state["retry_count"] >= 3:
        final_text = f"I attempted to analyze the data, but encountered persistent errors after 3 attempts:\n\n{error}"
    else:
        prompt = f"""Based on the user question and the data analysis results below, write a clear, executive-level summary answering the question.

User Question: {query}

Analysis Results / Print Output:
{output}
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        final_text = response.content
        
    return {"final_answer": final_text}

# Build LangGraph Workflow
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", code_generation_node)
workflow.add_node("execute", execution_node)
workflow.add_node("synthesize", synthesis_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "execute")

workflow.add_conditional_edges(
    "execute",
    evaluation_router,
    {
        "success": "synthesize",
        "retry": "generate",
        "max_retries": "synthesize"
    }
)

workflow.add_edge("synthesize", END)

app_graph = workflow.compile()

if __name__ == "__main__":
    print("Testing Milestone 3 Graph with a sample question...")
    test_query = "What is the total Net Revenue for completed orders from Enterprise customers, taking into account currency conversions?"
    
    initial_state = {
        "user_query": test_query,
        "retrieved_knowledge": "",
        "schema_summary": "",
        "generated_code": "",
        "execution_output": "",
        "execution_error": "",
        "chart_path": "",
        "retry_count": 0,
        "final_answer": ""
    }
    
    result = app_graph.invoke(initial_state)
    print("\n================ FINAL ANSWER ================")
    print(result["final_answer"])
    if result["chart_path"]:
        print(f"\nGenerated Chart saved to: {result['chart_path']}")