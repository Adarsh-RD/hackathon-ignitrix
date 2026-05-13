"""
returnX AI — RAG Knowledge Base
Retrieval-Augmented Generation using ChromaDB + LangChain.

Loads Indian tax rules into a vector store and retrieves
relevant context for the Tax Advisor agent.
"""

import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Path to knowledge base
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")


class TaxKnowledgeBase:
    """
    RAG component: Loads tax rules into ChromaDB vector store
    and retrieves relevant chunks for agent queries.
    """

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        self.vectorstore = None
        self._init_vectorstore()

    def _init_vectorstore(self):
        """Load or create the vector store from tax rules."""
        # Check if already built
        if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
            print("[RAG] Loading existing vector store...")
            self.vectorstore = Chroma(
                persist_directory=CHROMA_DIR,
                embedding_function=self.embeddings,
            )
            print(f"[RAG] Loaded {self.vectorstore._collection.count()} chunks")
            return

        # Build from knowledge files
        print("[RAG] Building vector store from knowledge base...")
        documents = self._load_documents()
        if not documents:
            print("[RAG] WARNING: No knowledge documents found")
            return

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_documents(documents)
        print(f"[RAG] Split into {len(chunks)} chunks")

        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=CHROMA_DIR,
        )
        print(f"[RAG] Vector store built with {len(chunks)} chunks")

    def _load_documents(self) -> list:
        """Load all .txt files from knowledge directory."""
        docs = []
        if not os.path.exists(KNOWLEDGE_DIR):
            return docs

        for filename in os.listdir(KNOWLEDGE_DIR):
            if filename.endswith(".txt"):
                filepath = os.path.join(KNOWLEDGE_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                docs.append(Document(
                    page_content=content,
                    metadata={"source": filename},
                ))
                print(f"[RAG] Loaded: {filename} ({len(content)} chars)")
        return docs

    def retrieve(self, query: str, k: int = 3) -> str:
        """
        Retrieve relevant tax knowledge for a query.

        Args:
            query: Natural language question about taxes
            k: Number of chunks to retrieve

        Returns:
            Concatenated relevant text chunks
        """
        if not self.vectorstore:
            return "No knowledge base available."

        results = self.vectorstore.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in results])
        print(f"[RAG] Retrieved {len(results)} chunks for: '{query[:50]}...'")
        return context
