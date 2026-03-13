import os
import json
import httpx
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any
from prompts import get_forecast_prompt
import rag_layer
from rag_layer import get_rag
from metrics_formatter import prepare_forecast_input

load_dotenv()

class ForecastEngine:
    def __init__(self):
        api_key = os.getenv("GENAI_API_KEY")
        if not api_key:
            raise ValueError("Set GENAI_API_KEY environment variable")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://genailab.tcs.in/v1",
            http_client=httpx.Client(verify=False)
        )
    
    def generate_forecast(self, forecast_input: Dict[str, Any], df=None, days: int = 7, enable_mock=True) -> Dict[str, Any]:
        """
        Dynamic forecast for ALL metrics with RAG + robust fallback.
        """
# Conditional RAG context
        rag_context = ""
        has_metrics, rag_msg = rag_layer.has_metrics_docs()
        print(rag_msg)
        if has_metrics:
            try:
                rag = get_rag()
                metric_keys = forecast_input['numeric_metrics_keys']
                rag_context = rag.retrieve_context(f"scaling policies for {', '.join(metric_keys[:3])} utilization trends")
                print(f"📚 RAG retrieved {len(rag_context)} chars context")
            except Exception as rag_err:
                print(f"⚠️ RAG failed: {rag_err} - no context")
        else:
            rag_context = ""
        
        # LLM call
        if not enable_mock:
            try:
                prompt = get_forecast_prompt(
                    forecast_input['metrics_summary'],
                    forecast_input['numeric_metrics_keys'],
                    forecast_input['capacities'],
                    forecast_input['thresholds'],
                    days=days,
                    rag_context=rag_context
                )
                response = self.client.chat.completions.create(
                    model="azure_ai/genailab-maas-DeepSeek-V3-0324",  # or DeepSeek-R1 if available
                    messages=[
                        {"role": "system", "content": "Precise forecasting AI. Respond ONLY with requested JSON format. Match ALL metric names."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                raw_content = response.choices[0].message.content or ""
                if raw_content.strip():
                    forecast = json.loads(raw_content)
                    if 'forecasts' in forecast and forecast_input['numeric_metrics_keys']:
                        missing = set(forecast_input['numeric_metrics_keys']) - set(forecast['forecasts'].keys())
                        if missing:
                            print(f"⚠️ Missing forecasts for: {missing}")
                    print(f"✅ API forecast: {list(forecast.keys())}")
                    return forecast
                    
            except Exception as api_err:
                print(f"❌ API failed: {api_err}")
        
        # Dynamic mock/trend fallback
        print(f"📊 Using dynamic trend forecast + RAG summary for {days} days")
        return self._create_dynamic_mock(forecast_input, df, days)
    
    def _create_dynamic_mock(self, forecast_input: Dict, df, days: int = 7) -> Dict:
        """Dynamic mock based on real trends."""
        numeric_stats = forecast_input.get('numeric_metrics', {})
        forecasts = {}
        
        upward_trends = 0
        for col, data in numeric_stats.items():
            base = float(data['mean'] or 0)
            growth_rate = data['growth_rate']
            
            # Improved: detect exponential if accelerating
            recent_growth = growth_rate * 1.5 if growth_rate > 0.05 else growth_rate  # Boost if fast growth
            if growth_rate > 0.1:  # Exponential for high growth
                forecast_val = max(0, base * (1 + recent_growth) ** days)
            else:
                forecast_val = max(0, base + growth_rate * days)
            
            noise = np.random.normal(0, base*0.03)
            forecast_val += noise
            forecasts[col] = round(max(0, forecast_val), 2)
            
            if forecast_val > base * 1.05:
                upward_trends += 1
        
        # Enhanced risk logic
        high_risk_cols = [col for col, f in forecasts.items() if ('_percent' in col.lower() and f > 75) or ('rate' in col.lower() and f > 500)]
        risk_level = "HIGH" if len(high_risk_cols) >= 2 or (len(forecasts) > 0 and upward_trends / len(forecasts) > 0.5) else "MEDIUM" if high_risk_cols or upward_trends > 0 else "LOW"
        
        num_metrics = len(forecasts)
        trend_pct = (upward_trends / num_metrics * 100) if num_metrics > 0 else 0
        trend_summary = f"Enhanced {days}-day forecast: Exponential for high growth. {risk_level} risk."
        
        return {
            "forecasts": forecasts,
            "risk_level": risk_level,
            "trend_summary": trend_summary
        }

