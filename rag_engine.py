# rag_engine.py
import os
import re
from typing import Optional
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains import RetrievalQA

class RAGEngine:
    """
    RAG engine for smart home assistant:
    - Handles both knowledge base queries and device reasoning prompts.
    - Returns concise, friendly answers.
    """

    DEVICE_CONTROL_KEYWORDS = [
        "turn on", "turn off", "lock", "unlock", "dim",
        "set thermostat", "lights", "door", "thermostat",
        "temperature", "status", "alarm", "humidifier",
        "kitchen", "bedroom", "living room"
    ]

    EXPLANATION_KEYWORDS = [
        "why", "reason", "explain", "show me why", "give me the reasoning"
    ]

    def __init__(self, kb_path: str = "knowledge.txt"):
        self.kb_path = kb_path
        self.qa_chain = self._load_qa_chain()

    def _load_qa_chain(self):
        if not os.path.exists(self.kb_path):
            raise FileNotFoundError(f"Knowledge base not found: {self.kb_path}")

        # Load and split documents
        loader = TextLoader(self.kb_path)
        documents = loader.load()
        splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        split_docs = splitter.split_documents(documents)

        # Vectorstore + embeddings
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vectorstore = FAISS.from_documents(split_docs, embeddings)

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        llm = OllamaLLM(model="gemma:2b")
        return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

    def query(self, query_text: str) -> str:
        """
        Query the RAG chain. Handles:
        1. Device explanations ("why" questions)
        2. Standard KB queries
        """
        processed_query = self._preprocess_query(query_text)

        try:
            response = self.qa_chain.invoke({"query": processed_query})
            return self._postprocess_response(response.get("result", ""))
        except Exception as e:
            return f"Error during RAG query: {str(e)}"

    def _preprocess_query(self, query_text: str) -> str:
        """
        Adds context hints for device-related or explanation queries.
        """
        lower_text = query_text.lower()

        # Device control hint
        if any(kw in lower_text for kw in self.DEVICE_CONTROL_KEYWORDS):
            if any(kw in lower_text for kw in self.EXPLANATION_KEYWORDS):
                return f"Explain smart home action: {query_text}"
            return f"Smart Home Device Question: {query_text}"

        # General knowledge query
        if any(kw in lower_text for kw in self.EXPLANATION_KEYWORDS):
            return f"Explain: {query_text}"

        return query_text

    def _postprocess_response(self, response: Optional[str]) -> str:
        """
        Clean response for assistant-friendly output.
        """
        if not response:
            return "I'm not sure about that. Could you rephrase?"

        text = str(response).strip()
        # Remove verbose AI-style prefixes
        text = re.sub(r"^(As an AI[^\n]*\n?|Sure,|Okay,|Ok,)\s*", "", text, flags=re.IGNORECASE)

        # Limit length to 500 chars while preserving full sentences
        if len(text) > 500:
            snippet = text[:500]
            if "." in snippet:
                snippet = snippet.rsplit(".", 1)[0] + "."
            text = snippet

        # Clean extra spaces/lines
        return re.sub(r"\s+\n", "\n", text).strip()
