"""
Format processed metrics into LLM-friendly strings dynamically.
"""
from typing import Dict, Any

def format_metric_details(col: str, metric_data: Dict[str, Any]) -> str:
    """Format single metric."""
    hist_str = ', '.join(f"{v:.1f}" for v in metric_data['history'][:5])  # First 5
    if len(metric_data['history']) > 5:
        hist_str += f" ... ({len(metric_data['history'])} points)"
    return f"{col}: [{hist_str}] | mean={metric_data['mean']:.1f}, max={metric_data['max']:.1f}, growth/day={metric_data['growth_rate']:.3f}"

def format_metrics_summary(metrics: Dict[str, Any]) -> str:
    """
    Dynamic prompt-friendly metrics history summary for ALL numeric columns.
    """
    numeric_stats = metrics['numeric_metrics']
    imputed = metrics.get('imputed_summary', {})
    total_imp = sum(imputed.values())
    
    summary = f"""Time range: {metrics['time_range']}
Server count: {metrics['server_count']}
Detected metrics: {metrics['num_metrics']}
Data cleaning: {total_imp} anomalies imputed

RECENT HISTORY & STATS (last 10 points each):\n"""
    
    for col, data in numeric_stats.items():
        imp_note = f" *imputed:{imputed.get(col,0)}*" if col in imputed and imputed[col]>0 else ""
        summary += f"- {format_metric_details(col, data)}{imp_note}\n"
    
    capacities_str = "\nCapacities: " + ', '.join(f"{k}: {v}" for k,v in metrics['capacities'].items()) if metrics['capacities'] else "\nCapacities: N/A"
    thresholds_str = "\nThresholds: " + ', '.join(f"{k}: {v}%" for k,v in metrics['thresholds'].items()) if metrics['thresholds'] else "\nThresholds: Defaults (80%)"
    
    summary += f"{capacities_str}{thresholds_str}"
    
    return summary

def prepare_forecast_input(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare all inputs for forecast LLM."""
    return {
        'metrics_summary': format_metrics_summary(metrics),
        'numeric_metrics_keys': list(metrics['numeric_metrics'].keys()),
        'capacities': metrics['capacities'],
        'thresholds': metrics['thresholds']
    }
