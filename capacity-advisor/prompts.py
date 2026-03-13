"""
LLM prompt templates for AI Infrastructure Capacity Planning Advisor.
"""

FORECAST_PROMPT = """
You are an infrastructure capacity planning expert. Analyze these DYNAMIC metrics and forecast for next {days} days.

METRICS SUMMARY (detected columns):
{metrics_summary}

CURRENT CAPACITY:
{capacities_str}

THRESHOLDS:
{thresholds_str}

METRICS TO FORECAST: {metric_keys}

Forecast ALL numeric metrics for next {days} days using appropriate trend modeling (linear/exponential/seasonal).
Provide point forecast per metric. Consider acceleration, volatility, RAG patterns.

RAG CONTEXT (scaling policies/reports): {rag_context}

Respond ONLY with valid JSON:
{{
  "forecasts": {{
    "{example_key1}": <number>,
    "{example_key2}": <number>,
    // Include ALL metrics from METRICS TO FORECAST with realistic {days}-day projections
  }},
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "trend_summary": "<1-2 sentences on key trends/risks over {days} days>"
}}

IMPORTANT: forecasts dict must match ALL input metric names exactly. Use history growth rates.
"""

REPORT_PROMPT = """
Generate executive capacity planning report.

FORECAST SUMMARY:
Risk: {risk_level}
Trends: {trend_summary}
Forecasts: {forecast_summary}

RECOMMENDATION: {recommended_action} (Urgency: {urgency})

RAG CONTEXT: {rag_context}

Write 3-5 sentences: trends, rationale, risks if ignored, next steps. Professional tone.
"""

DECISION_PROMPT = """
You are expert cloud capacity planner. Analyze forecast and generate PRIORITIZED capacity actions.

{ days }-DAY FORECAST:
- Forecasts: {forecasts_str}
- Risk: {risk_level}
- Trends: {trend_summary}

STATS:
- Current: {current_str}
- Δ%: {deltas_str}
- Growth/day: {growth_str}
- Thresholds: {thresholds_str}

RAG policies: {rag_context}

Generate data-driven decisions. Consider growth acceleration, correlations, costs.

ONLY JSON:
{{
  "recommended_action": "Executive action (1 sentence)",
  "reason": "Analysis (2-3 sentences with metrics)",
  "urgency": "HIGH|MEDIUM|LOW", 
  "num_actions": 0-10,
  "actions": ["Specific action 1", "Action 2", ...]
}}
"""

def get_forecast_prompt(metrics_summary: str, metric_keys: list, capacities: dict, thresholds: dict, days: int = 7, rag_context: str = "") -> str:
    capacities_str = ', '.join(f"{k}: {v}" for k,v in capacities.items()) if capacities else "N/A"
    thresholds_str = ', '.join(f"{k}: {v}" for k,v in thresholds.items()) if thresholds else "Defaults"
    example_keys = metric_keys[:2] if metric_keys else ["metric1", "metric2"]
    
    return FORECAST_PROMPT.format(
        metrics_summary=metrics_summary,
        capacities_str=capacities_str,
        thresholds_str=thresholds_str,
        metric_keys=', '.join(metric_keys),
        days=days,
        example_key1=example_keys[0],
        example_key2=example_keys[1] if len(example_keys)>1 else example_keys[0],
        rag_context=rag_context
    )

def get_report_prompt(forecast: dict, decision: dict, rag_context: str = "") -> str:
    forecast_summary = ', '.join([f"{k}: {v}" for k,v in list(forecast.get('forecasts', {}).items())[:5]])
    if len(forecast.get('forecasts', {})) > 5:
        forecast_summary += "..."
    
    return REPORT_PROMPT.format(
        risk_level=forecast.get('risk_level', 'UNKNOWN'),
        trend_summary=forecast.get('trend_summary', ''),
        forecast_summary=forecast_summary,
        recommended_action=decision['recommended_action'],
        urgency=decision['urgency'],
        rag_context=rag_context
    )

def get_decision_prompt(forecast: dict, stats_dict: dict, thresholds: dict, days: int, rag_context: str = "") -> str:
    forecasts = forecast.get('forecasts', {})
    forecasts_str = ', '.join(f"{k}: {v:.1f}" for k,v in list(forecasts.items())[:10])
    
    risk_level = forecast.get('risk_level', 'UNKNOWN')
    trend_summary = forecast.get('trend_summary', '')
    
    current_str = ', '.join(f"{k}: {v:.1f}" for k,v in stats_dict.get('current_values', {}).items())
    deltas_str = ', '.join(f"{k}: {v:.0f}%" for k,v in stats_dict.get('deltas', {}).items())
    growth_str = ', '.join(f"{k}: {v:.3f}" for k,v in stats_dict.get('growth_rates', {}).items())
    
    thresholds_str = ', '.join(f"{k}: {v}" for k,v in thresholds.items())
    
    return DECISION_PROMPT.format(
        days=days,
        forecasts_str=forecasts_str,
        risk_level=risk_level,
        trend_summary=trend_summary,
        current_str=current_str,
        deltas_str=deltas_str,
        growth_str=growth_str,
        thresholds_str=thresholds_str,
        rag_context=rag_context
    )

