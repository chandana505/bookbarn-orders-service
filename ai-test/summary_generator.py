import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from rag_layer import get_rag

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GENAI_API_KEY"),
    base_url="https://genailab.tcs.in/v1",
    http_client=httpx.Client(verify=False)
)

def get_forecast_summary(metrics, forecast):
    """Important metrics + trends summary."""
    rag = get_rag()
    rag_context = rag.retrieve_context("important metrics trends analysis")
    
    prompt = f"""
Analyze forecast vs metrics. Identify TOP 3 important metrics (highest growth/util), trends.

Metrics keys: {list(metrics['numeric_metrics'].keys())}
Forecast: {list(forecast['forecasts'].items())[:5]}
Risk: {forecast.get('risk_level')}

RAG: {rag_context}

1-2 para summary: key metrics driving capacity, trends, implications.
"""
    response = client.chat.completions.create(
        model="azure/genailab-maas-gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

def get_trends_summary(df, metrics):
    """3-liner all columns trends."""
    numeric_cols = list(metrics['numeric_metrics'].keys())
    trends = ', '.join([f"{col}: growth {metrics['numeric_metrics'][col]['growth_rate']:.3f}" for col in numeric_cols[:6]])
    
    prompt = f"""
3 bullet summary of ALL column trends from data.

Trends data: {trends}
Full columns: {numeric_cols}

- Metric1: trend description
- Metric2: ...
- Overall:
"""
    response = client.chat.completions.create(
        model="azure/genailab-maas-gpt-4o-mini", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def get_next_steps(metrics, forecast):
    """Max utilised + reduce/upgrade."""
    forecasts_dict = forecast.get('forecasts', {})
    if not forecasts_dict:
        return "No forecast data for next steps."
    max_util = max(forecasts_dict.items(), key=lambda x: x[1])
    
    rag = get_rag()
    rag_context = rag.retrieve_context(f"reduce usage {max_util[0]} upgrade compute")
    
    prompt = f"""
Next steps for max utilised: {max_util}

Metrics: {list(metrics['numeric_metrics'].keys())}
Forecast high: {max_util}

3 bullets:
- Reduce {max_util[0]} usage: strategies
- Computational upgrade options
- Monitoring/automation

RAG: {rag_context}
"""
    response = client.chat.completions.create(
        model="azure/genailab-maas-gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

