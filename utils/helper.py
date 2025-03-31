sql_query_generation_prompt = """
Generate five complex SQL queries for a Snowflake database table named STOCK_DATA to create visually engaging and insightful line charts. The table has two columns: DATA_DATE (DATE) and VALUE (FLOAT), which contain S&P 500 data over the last 10 years.
 
### Requirements
 
1. **Advanced Time-Series Techniques**: Utilize techniques like Moving Averages, Lead/Lag Analysis, Year-over-Year Growth Trends, Rolling Aggregations, and Volatility Analysis (Standard Deviation over Time).
2. **Trend Analysis Graphs**: Use the above techniques to analyze trends.
3. **Title and Description**: Each query should have a short, catchy title and a description explaining the logic behind the query.
 
# Output Format
 
The output should be a JSON array with five objects, each containing the following keys:
- **Title**: A short, catchy name for the visualization.
- **SQL**: The corresponding Snowflake SQL query.
- **Description**: A small explanation of the logic behind the query.
 
# Examples
 
- **Example 1: Calculating a 30-Day Moving Average Trend**
 
  ```json
  {
    "title": "30-Day Moving Average Trend",
    "description": "Calculates the 30-day moving average of S&P 500 values to smooth out short-term fluctuations.",
    "SQL": "SELECT DATA_DATE, AVG(VALUE) OVER (ORDER BY DATA_DATE ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS MOVING_AVG FROM STOCK_DATA"
  }
  ```
 
- **Example 2: Yearly Performance Comparison**
 
  ```json
  {
    "title": "Yearly Performance Comparison",
    "description": "Compares the S&P 500 value at the same date each year to analyze growth trends.",
    "SQL": "SELECT DATA_DATE, VALUE, LAG(VALUE, 365) OVER (ORDER BY DATA_DATE) AS PREV_YEAR_VALUE, (VALUE - LAG(VALUE, 365) OVER (ORDER BY DATA_DATE)) / LAG(VALUE, 365) OVER (ORDER BY DATA_DATE) * 100 AS YOY_GROWTH FROM STOCK_DATA"
  }
  ```
 
# Notes
 
- Ensure all syntax aligns with Snowflake SQL standards.
- Consider real-life business use cases for the queries.
- Include a mixture of aggregate functions and analytical operations.
"""

python_code_generation_prompt = """
You are a code generator specializing in data visualization using Plotly. Your task is to generate Python code that reads a given DataFrame (first 5 rows will be provided) and creates an appropriate Plotly visualization. Follow these rules:

## Start with these imports:
```python
import subprocess

# Ensure Kaleido is installed
subprocess.run(["pip", "install", "kaleido"], check=True)

import plotly.express as px
import pandas as pd
import io
import base64
```

## Read Data:
Always read from `'/home/user/sandbox/data.csv'`, ensuring proper parsing of any date columns. If there are columns with date data, include them in the `parse_dates` parameter while reading the CSV.

## Detect Columns:
Identify the relevant columns based on the input sample and title.

## Choose Plot Type:
- Use `px.line()` for time series data.
- Use `px.bar()` for categorical/quarterly data.

## Title:
Use the given title in the chart.

## Multiple Series:
If multiple numeric columns exist, plot them together for comparison.

## Grouping:
If `YEAR` and `QUARTER` are present, concatenate them into a new `YEAR_QUARTER` column and use it for the x-axis.

## Ensure the following lines appear at the end of the code without modification:
```python
# NEVER CHANGE THE BELOW LINES OF CODE
img_bytes = io.BytesIO()
fig.write_image(img_bytes, format="png")  # Requires kaleido
img_base64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")
img_base64
```

## Output Format:
The generated code must be wrapped inside a JSON object under the key `"code_to_run"`:
```json
{
    "code_to_run": "<generated python code here>"
}
```
"""

#tanmay prompts

def prompt_extract_and_analyze(text) :
    return f"""
    You are a senior financial data analyst for a major investment firm. Extract key market data from the provided sources
    and perform a preliminary analysis. This will be used to generate a comprehensive market report.

    PART 1: DATA EXTRACTION
    Extract the following information:
    1. Market movements (indexes like S&P 500, Dow, Nasdaq) with percentages
    2. Top gaining stocks with percentages
    3. Top losing stocks with percentages
    4. Key events affecting the market (tariffs, economic data, etc.)
    5. Date of the information (most recent date mentioned)

    PART 2: MARKET ANALYSIS
    Based on the extracted data, provide analysis of:
    1. Overall market sentiment (bullish, bearish, or neutral)
    2. Key drivers for market movement
    3. Sector trends and performance
    4. Technical insights and outlook

    Text sources to analyze:
    {text}

    Respond with a JSON object with these two main sections:
    1. "extracted_data": Data extracted from sources
    2. "market_analysis": Your analysis of the market situation

    For ANY missing information, create realistic, plausible market data that would be appropriate for
    a professional market report. The data should be internally consistent and realistic.
    """

def prompt_extract_and_analyze(consolidated_text):
    """
    Returns the prompt for extracting and analyzing market data
    
    Args:
        consolidated_text (str): The consolidated text from all sources
        
    Returns:
        str: The formatted prompt
    """
    return f"""
    You are a senior financial data analyst for a major investment firm. Extract key market data from the provided sources
    and perform a preliminary analysis. This will be used to generate a comprehensive market report.

    PART 1: DATA EXTRACTION
    Extract the following information:
    1. Market movements (indexes like S&P 500, Dow, Nasdaq) with percentages
    2. Top gaining stocks with percentages
    3. Top losing stocks with percentages
    4. Key events affecting the market (tariffs, economic data, etc.)
    5. Date of the information (most recent date mentioned)
    6. Sector performances and trends
    7. Technical indicators mentioned

    PART 2: MARKET ANALYSIS
    Based on the extracted data, provide analysis of:
    1. Overall market sentiment (bullish, bearish, or neutral) with justification
    2. Key drivers for market movement and their significance
    3. Sector trends and detailed sector performance
    4. Technical insights and support/resistance levels
    5. Impact analysis of key events
    6. Short and medium-term outlook

    Text sources to analyze:
    {consolidated_text}

    Respond with a detailed JSON object with these two main sections:
    1. "extracted_data": Data extracted from sources
    2. "market_analysis": Your analysis of the market situation

    For ANY missing information, create realistic, plausible market data that would be appropriate for
    a professional market report. The data should be internally consistent and realistic.
    
    Format your response as valid JSON within ```json ``` code blocks.
    """

def generate_multiple_sections(extracted_data_str, market_analysis_str, target_sections):
    """
    Returns the prompt for generating multiple report sections
    
    Args:
        extracted_data_str (str): JSON string of extracted data
        market_analysis_str (str): JSON string of market analysis
        target_sections (list): List of section names
        
    Returns:
        str: The formatted prompt
    """
    return f"""
    You are a senior financial analyst writing a comprehensive market report for research purposes (A research report).
    
    Based on this market data:
    
    Extracted Data:
    {extracted_data_str}
    
    Market Analysis:
    {market_analysis_str}
    
    Generate the following report sections:
    {', '.join(target_sections)}
    
    Each section should be extremely detailed and thorough (at least 800-1000 words per section). 
    Include realistic market data, analysis, and commentary throughout. 

    **IMPORTANT GUIDELINES:**

    1. **Markdown Formatting**: Use **proper Markdown formatting**:
       - Use `##` for section headers (e.g., `## EXECUTIVE SUMMARY`).
       - Use `-` for bullet points, and `**bold**` or `_italic_` for emphasis.
       - Separate paragraphs with **two line breaks (`\n\n`)**.
       - Use subheadings with `###` for more detailed subsections.
    
    2. **Content Quality**:
       - For any missing information, invent **realistic, plausible market details**.
       - Include **specific numbers, percentages, price points**, and **analyst quotes** where relevant.
       - Focus on creating **professional, insightful analysis** that would be suitable for **professional investors**.
       - Avoid generic or boilerplate language—make sure the report reads like it was written by an **experienced financial analyst**.

    3. **Specific Sections**:
       - **SECTOR PERFORMANCE**: Analyze **all 11 S&P 500 sectors** in detail.
       - **TECHNICAL ANALYSIS**: Include specific **support/resistance levels**, **moving averages**, and **indicators**.
       - **TOP PERFORMERS & LAGGARDS**: Analyze at least **10 companies** (5 top performers, 5 laggards) with detailed context.
       - **EXPERT PERSPECTIVES**: Provide **realistic quotes** from **fictional analysts** with company affiliations.
       
    The content must be **extremely detailed** and **comprehensive**, suitable for a **15-16 page printed report**. Focus on **quality analysis** over generic statements.

    Be sure to structure the content logically with **clear headings**, **subheadings**, and **breaks between sections** for readability.
    """

def format_section_content(section_name, content):
    """
    Formats section content with proper heading
    
    Args:
        section_name (str): The name of the section
        content (str): The content for the section
        
    Returns:
        str: Formatted section content
    """
    if not content.strip().startswith(f"## {section_name}"):
        return f"## {section_name}\n\n{content}"
    return content