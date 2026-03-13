import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict
from prompts import get_report_prompt
import rag_layer
from rag_layer import get_rag

load_dotenv()

class ReportGenerator:
    def __init__(self):
        api_key = os.getenv("GENAI_API_KEY")
        if not api_key:
            raise ValueError("Set GENAI_API_KEY environment variable")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://genailab.tcs.in/v1",
            http_client=httpx.Client(verify=False)
        )
    
    def generate_report(self, forecast: Dict, decision: Dict) -> str:
        """
        Generate report with RAG context using GPT-4o-mini.
        """
# Conditional RAG context
        rag_context = ""
        try:
            has_metrics, _ = rag_layer.has_metrics_docs()
            if has_metrics:
                rag = get_rag()
                query = f"capacity planning report for {list(forecast.get('forecasts', {}).keys())} trends {decision['urgency']}"
                rag_context = rag.retrieve_context(query)
        except Exception as rag_err:
            print(f"⚠️ Report RAG failed: {rag_err}")
        
        prompt = get_report_prompt(forecast, decision, rag_context)
        
        response = self.client.chat.completions.create(
            model="azure/genailab-maas-gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Professional cloud architect. Write concise, actionable executive reports incorporating policies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=400
        )
        
        return response.choices[0].message.content.strip()

