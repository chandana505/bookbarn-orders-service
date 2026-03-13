import os
import json
import httpx
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from dotenv import load_dotenv
from typing import List
import requests
import urllib3

# Monkeypatch requests.get to bypass SSL for tiktoken downloads
original_get = requests.get
def ssl_bypass_get(url, *args, **kwargs):
    kwargs['verify'] = False
    return original_get(url, *args, **kwargs)
requests.get = ssl_bypass_get

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

class RAGLayer:
    def __init__(self, docs_path='sample_docs.json'):
        self.api_key = os.getenv("GENAI_API_KEY")
        if not self.api_key:
            raise ValueError("GENAI_API_KEY required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://genailab.tcs.in/v1",
            http_client=httpx.Client(verify=False)
        )
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.api_key,
            openai_api_base="https://genailab.tcs.in/v1",
            model="azure/genailab-maas-text-embedding-3-large",
            http_client=httpx.Client(verify=False)
        )
        
        self.vectorstore = self._load_or_create_vectorstore(docs_path)
    
    def _load_or_create_vectorstore(self, docs_path):
        import os
        index_dir = 'faiss_index'
        os.makedirs(index_dir, exist_ok=True)
        
        try:
            return FAISS.load_local(index_dir, self.embeddings, allow_dangerous_deserialization=True)
        except Exception as load_err:
            print(f"FAISS load failed: {load_err}")
            try:
                docs = self._load_sample_docs(docs_path)
                texts = [doc['content'] for doc in docs]
                vectorstore = FAISS.from_texts(texts, self.embeddings, 
                                      metadatas=[{'source': 'policy'} for _ in texts])
                vectorstore.save_local(index_dir)
                return vectorstore
            except Exception as create_err:
                print(f"RAG vectorstore creation failed: {create_err} - using mock")
                # Create minimal empty vectorstore
                vectorstore = FAISS.from_texts([""], self.embeddings)
                vectorstore.save_local(index_dir)
                return vectorstore
    
    def _load_sample_docs(self, path):
        with open(path, 'r') as f:
            return json.load(f)
    
    def add_documents(self, texts: List[str]):
        import os
        index_dir = 'faiss_index'
        os.makedirs(index_dir, exist_ok=True)
        self.vectorstore.add_texts(texts)
        self.vectorstore.save_local(index_dir)
    
    def retrieve_context(self, query: str, k: int = 2) -> str:
        docs = self.vectorstore.similarity_search(query, k=k)
        return '\n\n---\n\n'.join([doc.page_content for doc in docs])

rag = None

def has_metrics_docs(path='capacity-advisor/sample_docs.json') -> tuple[bool, str]:
    """
    Check if sample_docs contain metric-specific content.
    Returns (has_metrics, notification_msg)
    """
    try:
        import json
        with open(path, 'r') as f:
            docs = json.load(f)
        metrics_keywords = ['cpu', 'memory', 'disk', 'request', 'response_time', 'network', 'latency', 'throughput', 'error_rate', 'utilization', '*']
        has_metrics = any(
            any(keyword in doc['content'].lower() for keyword in metrics_keywords)
            for doc in docs if isinstance(doc, dict) and 'content' in doc
        )
        msg = "📊 RAG enabled (metric docs found)" 
        return has_metrics, msg
    except Exception as e:
        # print(f"RAG check failed: {e}")
        return False, "📊 Direct analysis "

def get_rag():
    global rag
    if rag is None:
        rag = RAGLayer()
    return rag

