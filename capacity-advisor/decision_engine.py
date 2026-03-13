"""
LLM-powered dynamic capacity decisions - NO hardcodes.
"""
import os
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List
import statistics
from prompts import get_decision_prompt
from rag_layer import get_rag

load_dotenv()

def make_capacity_decision(forecast: Dict, thresholds: Dict, metrics_stats: Dict = None, days: int = 7, numeric_keys: List[str] = None) -> Dict:
    """
    LLM-driven decisions from forecast data + stats + RAG. Dynamic fallback.
    """
    forecasts = forecast.get('forecasts', {})
    if not forecasts:
        return {
            "recommended_action": "📊 Data analysis ready - forecasts generated",
            "reason": "Metrics processed. Run forecast for recommendations.",
            "urgency": "LOW",
            "num_actions": 0
        }
    
    # Compute stats for LLM
    stats_dict = {'current_values': {}, 'deltas': {}, 'growth_rates': {}}
    if metrics_stats and 'numeric_metrics' in metrics_stats:
        for col in forecasts:
            stats = metrics_stats['numeric_metrics'].get(col, {})
            history = stats.get('history', [])
            current = history[-1] if history else forecasts[col]
            delta_pct = ((forecasts[col] - current) / current * 100) if current > 0 else 0
            
            stats_dict['current_values'][col] = current
            stats_dict['deltas'][col] = delta_pct
            stats_dict['growth_rates'][col] = stats.get('growth_rate', 0)
    
    # RAG context
    rag_context = ""
    try:
        rag = get_rag()
        rag_context = rag.retrieve_context(f"capacity actions for {list(forecasts.keys())} forecast trends")
    except:
        rag_context = "RAG unavailable"
    
    # LLM decision
    api_key = os.getenv("GENAI_API_KEY")
    if api_key:
        client = OpenAI(
            api_key=api_key,
            base_url="https://genailab.tcs.in/v1",
            http_client=httpx.Client(verify=False)
        )
        
        prompt = get_decision_prompt(forecast, stats_dict, thresholds, days, rag_context)
        
        try:
            response = client.chat.completions.create(
                model="azure/genailab-maas-gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Capacity planning expert. Precise JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            llm_response = json.loads(response.choices[0].message.content or '{}')
            if llm_response.get('recommended_action'):
                llm_response['forecast_risk'] = forecast.get('risk_level', 'UNKNOWN')
                print("✅ LLM decision used")
                return llm_response
        except Exception as llm_err:
            print(f"LLM decision failed: {llm_err}")
    
    # Generic dynamic fallback
    top_metric = max(forecasts.items(), key=lambda x: x[1])[0] if forecasts else "metrics"
    avg_delta = statistics.mean(list(stats_dict['deltas'].values())) if stats_dict['deltas'] else 0
    buffer_pct = max(25, int(abs(avg_delta) + 20))
    
    recommended_action = f"✅ Capacity stable across {len(forecasts)} metrics - monitor {top_metric} | {buffer_pct}% buffer"
    reason = f"Forecast risk: {forecast.get('risk_level', 'LOW')}. Trends: {forecast.get('trend_summary', 'stable')[:80]}... | Avg change {avg_delta:.1f}%"
    urgency = "LOW" if abs(avg_delta) < 10 else "MEDIUM" if abs(avg_delta) < 25 else "HIGH"
    
    return {
        "recommended_action": recommended_action,
        "reason": reason,
        "urgency": urgency,
        "num_actions": 1,
        "actions": [f"Maintain {buffer_pct}% buffer on {top_metric}"],
        "forecast_risk": forecast.get('risk_level', 'UNKNOWN')
    }

