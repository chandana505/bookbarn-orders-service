import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import tempfile
import os

# Local imports - dynamic
from data_processor import load_and_validate_csv, compute_metrics_stats, get_data_preview
from metrics_formatter import prepare_forecast_input
from forecast_engine import ForecastEngine
from decision_engine import make_capacity_decision
from report_generator import ReportGenerator
import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from metrics_formatter import format_metrics_summary

load_dotenv()

def get_qa_answer(question: str, metrics: dict, df: pd.DataFrame) -> str:
    """LLM Q&A about uploaded data."""
    api_key = os.getenv("GENAI_API_KEY")
    if not api_key:
        return "❌ GENAI_API_KEY missing"
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://genailab.tcs.in/v1",
        http_client=httpx.Client(verify=False)
    )
    
    context = f"""
Data Summary:
- Time: {metrics['time_range']}
- Metrics: {len(metrics['numeric_metrics'])} detected
- Recent stats: {format_metrics_summary(metrics)}

Question: {question}
    
Answer based only on this data. Be precise and actionable.
"""
    
    try:
        response = client.chat.completions.create(
            model="azure/genailab-maas-gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Data analyst expert. Answer questions precisely using provided metrics/data summary."},
                {"role": "user", "content": context}
            ],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Q&A error: {str(e)}"

st.set_page_config(page_title="AI Capacity Planning Advisor", layout="wide")

st.title(" AI Infrastructure Capacity Planning Advisor")
st.markdown("Upload **any CSV with numeric infrastructure metrics** to get AI-powered dynamic analysis with RAG.")

@st.cache_data
def process_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            df = load_and_validate_csv(tmp_path)
            metrics = compute_metrics_stats(df)
            preview = get_data_preview(df)
            forecast_input = prepare_forecast_input(metrics)
            return df, metrics, preview, forecast_input
        finally:
            os.unlink(tmp_path)
    return None, None, None, None

@st.cache_resource
def init_rag():
    """Lazy RAG init with fallback."""
    try:
        from rag_layer import get_rag
        return get_rag()
    except Exception as e:
        print(f"RAG init failed: {e} - using mock")
        class MockRAG:
            def retrieve_context(self, query, k=2):
                return "RAG temporarily unavailable. Using local rules."
        return MockRAG()

# Main app
uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file is not None:
    df, metrics, preview, forecast_input = process_uploaded_file(uploaded_file)
    
    if df is not None and metrics['num_metrics'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Preview")
            st.dataframe(preview['head'])
            st.metric("Rows", preview['shape'][0])
            st.metric("Metrics Detected", metrics['num_metrics'])
            imputed = metrics.get('imputed_summary', {})
            total_imputed = sum(imputed.values()) if imputed else 0
            if total_imputed > 0:
                st.metric("Anomalies Imputed", total_imputed)
            st.caption(f"{preview['time_range']} | Data robustified")
        
        with col2:
            st.subheader("📈 Trends (Top 4 Metrics)")
            fig = go.Figure()
            import numpy as np
            numeric_cols = [col for col in preview['numeric_columns'][:4] if col]  # Filter empty
            x_values = df['timestamp'].values if 'timestamp' in df.columns else np.arange(len(df))
            if numeric_cols:
                for col in numeric_cols:
                    fig.add_trace(go.Scatter(x=x_values, y=df[col], name=col, mode='lines'))
            fig.update_layout(title="Dynamic Resource Trends", xaxis_title="Time/Index", yaxis_title="Value", height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # RAG status notification
        import rag_layer
        has_metrics, rag_msg = rag_layer.has_metrics_docs()
        st.info(rag_msg)
        
        # Q&A section
        col_qa, col_metrics = st.columns([2,1])
        with col_qa:
            qa_question = st.text_area(
                "💬 Ask about your data:", 
                placeholder="E.g., CPU growth trend? Top risks? Forecast highlights?",
                key="qa_input"
            )
            if st.button("Submmit", key="qa_btn") and qa_question.strip():
                with st.spinner("🤔 Analyzing..."):
                    qa_answer = get_qa_answer(qa_question, metrics, df)
                    st.success(f"**{qa_question}**")
                    st.markdown(qa_answer)
        
        with col_metrics:
            st.subheader("🔍 Detected Metrics")
            st.caption(', '.join(metrics['numeric_metrics'].keys()))
        
# Custom forecast date
        col_date, col_days = st.columns(2)
        with col_date:
            last_date = df['timestamp'].max().date() if 'timestamp' in df and not df['timestamp'].isna().all() else pd.Timestamp.now().date()
            target_date = st.date_input("Target forecast date", value=last_date + pd.Timedelta(days=30), min_value=last_date)
        with col_days:
            forecast_days = max(1, (pd.Timestamp(target_date) - pd.Timestamp(last_date)).days)
            st.metric("Days ahead", forecast_days)
        forecast_days = int(forecast_days)
        
        # Analysis button
        if st.button("🚀 Generate Capacity Advice", type="primary"):
            init_rag()  # Warm up RAG
            init_rag()  # Warm up RAG
            with st.spinner("🔮 Forecasting with DeepSeek-R1 + RAG analysis..."):
                try:
                    forecaster = ForecastEngine()
                    forecast = forecaster.generate_forecast(forecast_input, df=df, days=forecast_days)
                    
                    st.session_state.debug_forecast = forecast
                    
                    # Dynamic decision with metrics_stats
                    decision = make_capacity_decision(
                        forecast, 
                        forecast_input['thresholds'],
                        metrics,
                        days=forecast_days  # Pass forecast period for context
                    )
                    
                    # Report
                    try:
                        reporter = ReportGenerator()
                        report = reporter.generate_report(forecast, decision)
                    except Exception as report_err:
                        st.warning(f"Report failed: {report_err} - using summary")
                        report = f"**Summary:** {decision['reason']}\\nTrends: {forecast.get('trend_summary', 'N/A')}"
                    
                    # Dynamic Results
                    st.subheader(f"🔮 Forecast to {target_date} ({forecast_days} days)")
                    forecasts = forecast.get('forecasts', {})
                    
                    # Top metrics in columns
                    top_metrics = dict(list(forecasts.items())[:4])
                    num_cols = max(1, min(4, len(top_metrics)))
                    cols = st.columns(num_cols)
                    for i, (metric, value) in enumerate(top_metrics.items()):
                        with cols[i]:
                            st.metric(metric, f"{value:.1f}")
                    
                    if len(forecasts) > 4:
                        with st.expander(f"📋 All {len(forecasts)} forecasts to {target_date}"):
                            st.json(forecasts)
                    
                    st.info(f"**Risk:** {forecast.get('risk_level', '?')} | Trends: {forecast.get('trend_summary', '')}")
                    
                    # NEW LLM Summaries
                    from summary_generator import get_forecast_summary, get_trends_summary, get_next_steps
                    with st.expander("📊 Forecast Summary", expanded=True):
                        st.markdown(get_forecast_summary(metrics, forecast))
                    
                    with st.expander("📈 Trends Analysis (All Metrics)"):
                        st.markdown(get_trends_summary(df, metrics))
                    
                    # Report
                    st.subheader("📄 AI Capacity Planning Report")
                    st.markdown(report)
                    
                    # Debug
                    with st.expander("🔍 Debug Info"):
                        st.json({
                            "detected_metrics": metrics['num_metrics'],
                            "forecast_keys": len(forecasts),
                            "rag_used": "Yes" if 'RAG' in str(forecast).upper() else "Fallback",
                            "full_forecast": forecast
                        })
                        
                except Exception as e:
                    st.error(f"Analysis error: {str(e)}")
                    st.caption("App handles any CSV - check preview for numerics")
    else:
        st.warning("❌ No numeric data detected. Ensure CSV has numeric columns.")
    
else:
    st.info("👆 Upload CSV with numeric metrics (CPU%, requests, etc.)")

st.markdown("---")
st.caption("Dynamic RAG-enabled POC | DeepSeek-R1 Forecast + GPT-4o-mini Reports")

