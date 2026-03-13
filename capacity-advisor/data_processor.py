import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any

def detect_numeric_metrics(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Dynamically detect all numeric columns.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return {col: df[col].dropna() for col in numeric_cols if len(df[col].dropna()) > 0}

def load_and_validate_csv(file_path: str) -> pd.DataFrame:
    """
    Load CSV dynamically. Handle optional timestamp.
    """
    df = pd.read_csv(file_path)
    
    # Handle timestamp if present
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Clean ONLY numeric candidate columns
    numeric_candidates = [col for col in df.columns if col not in ['timestamp', 'server_id']]
    for col in numeric_candidates:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # NEW: Forward/backward fill contiguous nulls
    df[numeric_candidates] = df[numeric_candidates].ffill().bfill()
    
    # NEW: Anomaly detection and adjacent imputation
    imputed_counts = {}
    for col in numeric_candidates:
        series = df[col].copy()
        if series.isna().all():
            continue
        mean_val = series.mean()
        std_val = series.std()
        if pd.isna(std_val) or std_val == 0:
            continue
        
        # Flag anomalies: remaining NaN or outliers >3std
        is_anomaly = (series.isna()) | (np.abs(series - mean_val) > 3 * std_val)
        imputed_count = is_anomaly.sum()
        imputed_counts[col] = int(imputed_count)
        
        # Impute with avg adjacent non-anomalies (window 1-2)
        for idx in series[is_anomaly].index:
            neighbors = []
            for offset in [-2, -1, 1, 2]:
                n_idx = idx + offset
                if 0 <= n_idx < len(df):
                    n_val = df.at[n_idx, col]
                    if pd.notna(n_val) and np.abs(n_val - mean_val) <= 3 * std_val:
                        neighbors.append(n_val)
            if neighbors:
                df.at[idx, col] = np.mean(neighbors)
            else:
                df.at[idx, col] = mean_val  # Fallback to mean
        
        print(f"Imputed {imputed_count} anomalies in {col}")
    
    # Store imputed stats for preview/stats
    df.attrs['imputed_counts'] = imputed_counts
    
    # Drop rows where ALL numeric columns still NaN (edge case)
    numeric_cols_with_data = [col for col in numeric_candidates if df[col].notna().any()]
    if numeric_cols_with_data:
        df = df.dropna(subset=numeric_cols_with_data)
    else:
        raise ValueError("No valid numeric data found after imputation")
    
    if df.empty:
        raise ValueError("No valid numeric data after cleaning")
    
    return df

def compute_growth_rate(series: pd.Series) -> float:
    """
    Linear growth rate.
    """
    if len(series) < 2:
        return 0.0
    
    if series.index.name and 'timestamp' in series.index.name or len(series.index.unique()) < 2:
        x = np.arange(len(series))
    else:
        # Fake time if no timestamp
        x = np.arange(len(series))
    
    if len(np.unique(x)) < 2:
        return 0.0
    
    # Safe polyfit: protect division by zero (constant x/var=0)
    if np.var(x, ddof=1) == 0:
        return 0.0
    try:
        slope = np.polyfit(x, series.values, 1)[0]
    except np.linalg.LinAlgError:
        return 0.0
    return slope

def compute_metrics_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Dynamic stats/history for ALL numeric columns.
    """
    numeric_metrics = detect_numeric_metrics(df)
    
    stats = {}
    for col, series in numeric_metrics.items():
        recent_n = min(10, len(series))
        stats[col] = {
            'history': series.tail(recent_n).tolist(),
            'mean': float(series.mean() or 0.0),
            'max': float(series.max() or 0.0),
            'growth_rate': compute_growth_rate(series)
        }
    
    # Detect capacities/thresholds (cols containing keywords)
    capacities = {}
    for col in df.columns:
        if any(kw in col.lower() for kw in ['capacity', 'count', 'size']) and col in numeric_metrics:
            capacities[col] = float(df[col].iloc[-1])
    
    thresholds = {}
    for col in df.columns:
        if any(kw in col.lower() for kw in ['threshold', 'limit', 'max']) and col in numeric_metrics:
            thresholds[col] = float(df[col].iloc[-1])
    
    time_range = (df.get('timestamp', pd.Series()).min().strftime('%Y-%m-%d') + 
                  ' to ' + df.get('timestamp', pd.Series()).max().strftime('%Y-%m-%d')
                  if 'timestamp' in df.columns else f"{len(df)} data points")
    
    return {
        'numeric_metrics': stats,
        'capacities': capacities,
        'thresholds': thresholds or {k: 80.0 for k in stats.keys() if '_percent' in k.lower()},  # Default 80%
        'time_range': time_range,
'server_count': df.get('server_id', pd.Series()).nunique() if 'server_id' in df.columns else 1,
        'imputed_summary': df.attrs.get('imputed_counts', {}),
        'num_metrics': len(stats)
    }

def get_data_preview(df: pd.DataFrame, n_rows: int = 5) -> Dict:
    """Dynamic preview."""
    numeric_cols = detect_numeric_metrics(df)
    preview_df = df[list(numeric_cols.keys()) + (['timestamp'] if 'timestamp' in df.columns else [])].head(n_rows)
    return {
        'head': preview_df.to_dict('records'),
        'shape': df.shape,
        'numeric_columns': list(numeric_cols.keys()),
        'time_range': compute_metrics_stats(df)['time_range']
    }

