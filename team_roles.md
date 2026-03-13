# Team Roles & Responsibilities - AI Capacity Planning Advisor (Team 15)

## 🎯 Team Structure (5 Members)

Based on project architecture (Streamlit AI app for infrastructure forecasting), here's logical division of roles matching the work done:

| Member | Role | Responsibilities | Key Contributions |
|--------|------|------------------|-------------------|
| **Member 1: Project Lead / Architect** | 🏗️ Overall Design & Integration | - Define architecture (data→forecast→decision→report)<br>- UI/UX (app.py Streamlit)<br>- API integration (TCS GenAI)<br>- Demo preparation | app.py (main app), requirements.txt, .env setup |
| **Member 2: Data Engineer** | 📊 Data Pipeline | - CSV processing/imputation (data_processor.py)<br>- Metrics stats & growth rates<br>- Data validation/anomaly detection<br>- Sample data (sample_metrics.csv) | data_processor.py, metrics_formatter.py |
| **Member 3: ML/AI Engineer** | 🤖 AI Core | - LLM forecasting (forecast_engine.py)<br>- Decision engine (decision_engine.py)<br>- Prompts engineering (prompts.py)<br>- RAG setup (rag_layer.py) | forecast_engine.py, decision_engine.py, prompts.py, rag_layer.py |
| **Member 4: Reports & UI Specialist** | 📈 Visualization & Output | - Report generation (report_generator.py)<br>- Summaries/Q&A (summary_generator.py)<br>- Plotly charts<br>- Documentation | report_generator.py, summary_generator.py, docs.md |
| **Member 5: DevOps/Optimizer** | ⚙️ Deployment & Enhancements | - Environment/dependencies<br>- Testing/scripts<br>- Optimizations (real-time, alerts)<br>- PPT/demo materials | presentation_prompt.txt, testing, future extensions planning |

## 📋 Work Division Rationale
- **Modular:** Each role owns 1-2 core modules.
- **Balanced:** ~20% code each; collaborative integration.
- **Hackathon Fit:** Clear ownership for 1-day build.
- **Demo Ready:** Lead handles presentation.

## 🔄 Collaboration
- **Daily Standups:** Progress on modules → Merge to app.py.
- **Shared Repo:** Git PRs per module.
- **Pairing:** AI Engineer + Data for prompts/tuning.

## 🚀 Demo Roles
- **Presenter:** Member 1 (Overview + Live Demo).
- **Backup:** Member 3 (AI Explainer), Member 4 (Reports).

---

*Team 15: Efficient division based on project codebase. Assign names as needed.*
