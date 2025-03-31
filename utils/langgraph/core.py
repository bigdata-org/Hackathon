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
from utils.helper import prompt_extract_and_analyze, generate_multiple_sections

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
    report_content: Annotated[Optional[str], "The final market report"]
    error: Annotated[Optional[str], "Error message if any"]

def load_json_from_file(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON from file: {str(e)}")
        return None

def extract_and_analyze_data(json_data: Dict) -> Dict:
    """Combined extraction and analysis in one API call - works directly with results array"""
    # Prepare consolidated text from all sources in the results array
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
        return {
            "extracted_data": {
                "date": datetime.now().strftime("%B %d, %Y"),
                "market_movements": {"Error": "Invalid input data format"}
            },
            "market_analysis": {
                "sentiment": "unknown"
            }
        }
    
    # Combined extraction and analysis prompt
    prompt = prompt_extract_and_analyze(consolidated_text)
    
    response = llm(model='gemini/gemini-2.5-pro-exp-03-25', system_prompt=prompt, user_prompt='Extract and analyze for the above context')['answer']
    
    try:
        # Try to extract JSON from the response
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try other JSON extraction methods
        json_match_alt = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match_alt:
            return json.loads(json_match_alt.group(0))
            
        # If still can't parse, return basic structure
        logger.warning("Could not parse JSON from response")
        return {
            "extracted_data": {
                "date": datetime.now().strftime("%B %d, %Y"),
                "market_movements": {"Error": "Could not extract market movements"}
            },
            "market_analysis": {
                "sentiment": "unknown"
            }
        }
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        raise

async def generate_report_with_streaming(data: Dict):
    """Generate full market report with streaming output to console only"""
        
    # Define all sections
    sections = [
        "EXECUTIVE SUMMARY",
        "MARKET OVERVIEW",
        "ECONOMIC CONTEXT",
        "GEOPOLITICAL FACTORS",
        "SECTOR PERFORMANCE",
        "TOP PERFORMERS & LAGGARDS",
        "TECHNICAL ANALYSIS",
        "MARKET THEMES & CATALYSTS",
        "CORPORATE DEVELOPMENTS",
        "MARKET OUTLOOK",
        "EXPERT PERSPECTIVES",
        "APPENDIX: DATA TABLES & CHARTS"
    ]
    
    # Extract relevant market data
    extracted_data_str = json.dumps(data.get('extracted_data', {}), indent=2)
    market_analysis_str = json.dumps(data.get('market_analysis', {}), indent=2)
    
    # Create prompt for generating the full report
    prompt = generate_multiple_sections(extracted_data_str, market_analysis_str, sections)
    
    try:       
        async for chunk in allm(model="gemini/gemini-2.5-pro-exp-03-25", system_prompt=prompt, user_prompt='Generate the report as per the provided instructions'):
            logger.info('\n' in chunk)
            yield chunk  # Ensure paragraphs are correctly spaced

    except Exception as e:
        yield f"Error generating report: {str(e)}\n\n"

# Define node operations for LangGraph
def extract_data(state: AgentState) -> AgentState:
    """Extract and analyze data directly from input JSON"""
    try:
        json_data = state.get("input_data", {})
        result = extract_and_analyze_data(json_data)
        return {"extracted_data": result}
    except Exception as e:
        return {"error": f"Error extracting data: {str(e)}"}

def generate_report(state: AgentState) -> AgentState:
    """Generate the full market report with streaming to console"""
    try:
        data = state.get("extracted_data", {})
        # result = generate_report_with_streaming(data)
        return {"report_content": data}
    except Exception as e:
        return {"error": f"Error generating report: {str(e)}"}

def check_for_errors(state: AgentState) -> str:
    """Check if there are any errors and decide next step"""
    if "error" in state and state["error"]:
        logger.error(f"Error detected: {state['error']}")
        return END
    return "continue"

def router(state: AgentState) -> str:
    """Decide the next step in the process"""
    if "extracted_data" not in state or not state["extracted_data"]:
        return "extract_data"
    elif "report_content" not in state:
        return "generate_report"
    else:
        return END

# Create the LangGraph
def create_market_report_agent():
    """Create the market report agent using LangGraph"""
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("extract_data", extract_data)
    workflow.add_node("generate_report", generate_report)
    
    # Add edges
    workflow.add_conditional_edges(START, router)
    workflow.add_edge("extract_data", "generate_report")
    workflow.add_edge("generate_report", END)
    
    # Add error checking
    workflow.add_conditional_edges("extract_data", check_for_errors)
    workflow.add_conditional_edges("generate_report", check_for_errors)
    
    # Compile the graph
    return workflow.compile()

def entry_point(json_data):
    """Process a search results file using the LangGraph agent with console streaming"""
    logger.info("===== S&P 500 MARKET REPORT GENERATOR (WITH CONSOLE STREAMING) =====")
    logger.info("Starting market report generation with LangGraph agent")
    
    # Load JSON data from file
    if not json_data:
        return "Error: Could not load JSON data from file"
    
    # Create and run the agent
    agent = create_market_report_agent()
    result = agent.invoke({
        "input_data": json_data,
        "extracted_data": None,
        "report_content": None,
        "error": None
    })
    
    if "error" in result and result["error"]:
        logger.error(f"Agent error: {result['error']}")
        return f"Error: {result['error']}"
    
    logger.info("===== REPORT GENERATION COMPLETE =====")
    return result.get("report_content", None)
