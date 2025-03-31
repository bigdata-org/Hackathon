import json
from dotenv import load_dotenv
from typing import Dict, List, Any, Annotated, TypedDict, Optional
from datetime import datetime
import re
import logging
import asyncio
from utils.litellm.core import allm, llm
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langgraph.graph import StateGraph, END, START
from langchain_core.tools import Tool
from utils.helper import prompt_extract_and_analyze, research_report_prompt
from utils.sandbox.core import python_sandbox
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define state structure for the agent
class AgentState(TypedDict):
    input_data: Annotated[Dict, "JSON input data with search results"]
    extracted_data: Annotated[Optional[Dict], "Consolidated extracted and analyzed data"]
    chart_data : Annotated[Optional[Dict], "Sandbox executed chart data"]
    report_context: Annotated[Optional[str], "The final market report"]
    error: Annotated[Optional[str], "Error message if any"]

def extract_and_analyze_data(json_data: Dict) -> Dict:
    """Combined extraction and analysis in one API call - works directly with results array"""
    # Prepare consolidated text from all sources in the results array
    fallback_data = {
            "extracted_data": {
                "date": datetime.now().strftime("%B %d, %Y"),
                "market_movements": {"Error": "Invalid input data format"}
            },
            "market_analysis": {
                "sentiment": "unknown"
            }
        }
    consolidated_text = ""
    
    if "results" in json_data and isinstance(json_data["results"], list):
        for i, source in enumerate(json_data["results"], 1):
            if not source:
                continue
                
            title = source.get("WEBPAGE_TITLE", "Unknown Title")
            content = source.get("WEBPAGE_CONTENT", "No content available")
            
            consolidated_text += f"Source {i} - {title}:\n{content}\n\n"
    else:
        logger.warning("Input data doesn't have expected 'results' array structure")
        return fallback_data
    
    # Combined extraction and analysis prompt
    prompt = prompt_extract_and_analyze(consolidated_text)
    
    llm_ready_data = llm(model='openai/gpt-4o-mini', system_prompt=prompt, user_prompt='Extract and analyze for the above context', is_json=True)['answer']
    try:
        logger.info("=====PREPROCESSING ENDED=====")
        return llm_ready_data
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        return fallback_data

async def generate_report_with_streaming(context):
    """Generate full market report with streaming output to console only"""    
    try: 
        logger.info("=====REPORT GENERATION STARTED =====")      
        async for chunk in allm(model="gemini/gemini-2.5-pro-exp-03-25", system_prompt=context, user_prompt='Generate the report as per the provided instructions'):
            yield chunk  
    except Exception as e:
        yield f"Error generating report: {str(e)}\n\n"

def generate_report_without_streaming(context):
    return llm(model="gemini/gemini-2.5-pro-exp-03-25", system_prompt=context, user_prompt='Generate the S&P research report as per the provided instructions')['answer']

# Define node operations for LangGraph
def extract_data(state: AgentState) -> AgentState:
    """Extract and analyze data directly from input JSON"""
    logger.info("=====PREPROCESSING STARTED=====")
    try:
        json_data = state.get("input_data", {})
        result = extract_and_analyze_data(json_data)
        return {"extracted_data": json.loads(result)}
    except Exception as e:
        return {"error": f"Error extracting data: {str(e)}"}

def consolidate_context(state: AgentState) -> AgentState:
    """Generate the full market report with streaming to console"""
    logger.info("=====CONSOLIDATING REPORT CONTEXT=====")
    try:
        data = state.get("extracted_data", {})
        logger.info(f'picking check {str(data)}')
        extracted_data_str = json.dumps(data.get('extracted_data', 'No data extracted, skip data extraction analysis'))
        market_analysis_str = json.dumps(data.get('market_analysis', 'No market analysis data found, skip market analysis'))
        chart_data_str = state.get('chart_data', 'No chart data found, skip the chart analysis')
        # Create prompt for generating the full report
        context = research_report_prompt(extracted_data_str, market_analysis_str, chart_data_str)
        return {"report_context": context}
    except Exception as e:
        return {"error": f"Error generating report: {str(e)}"}

def check_for_errors(state: AgentState) -> str:
    """Check if there are any errors and decide next step"""
    if "error" in state and state["error"]:
        logger.error(f"Error detected: {state['error']}")
        return END
    return "continue"

def generate_charts(state: AgentState):
    logger.info("=====CHART TOOL=====")
    with open('local/charts.json', 'r') as f:
        chart_metadata = json.loads(f.read())
    chart_data = python_sandbox(chart_metadata)
    if chart_data:
        return {"chart_data" : chart_data}
    return {"error": f"Error generating chart"}

# Create the LangGraph
def create_market_report_agent():
    """Create the market report agent using LangGraph"""
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("web", extract_data)
    workflow.add_node("chart", generate_charts)
    workflow.add_node("aggregator", consolidate_context)
    
    # Add edges
    workflow.add_edge(START, "web")
    workflow.add_edge(START, "chart")
    workflow.add_edge(["web", "chart"], "aggregator")
    workflow.add_edge("aggregator", END)
    
    # Add error checking
    workflow.add_conditional_edges("web", check_for_errors)
    workflow.add_conditional_edges("chart", check_for_errors)
    
    # Compile the graph
    return workflow.compile()

def entry_point(json_data):
    """Process a search results file using the LangGraph agent with console streaming"""    
    # Load JSON data from file
    logger.info("=====ENTRY POINT=====")
    if not json_data:
        logger.error("Error: Could not load JSON data from file")
        return None
    
    # Create and run the agent
    agent = create_market_report_agent()
    result = agent.invoke({
        "input_data": json_data,
        "extracted_data": None,
        "chart_data": None, 
        "report_context": None,
        "error": None
    })
    
    if "error" in result and result["error"]:
        logger.error(f"Agent error: {result['error']}")
        return None
    return result.get("report_context", None)
