# core_library/redteam_commander/codebase_analyzer.py
import os
from pathlib import Path
from typing import Dict, Any, List

# --- LangChain Imports for RAG ---
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

from langchain_huggingface import HuggingFaceEmbeddings
from .commander_state import RedTeamCommanderState


class CodebaseAnalyzer:
    """
    Handles the RAG pipeline: loading, splitting, and indexing code files.
    """
    def __init__(self):
        # Initialize the text splitter for Python code
        self.python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=2000, chunk_overlap=200
        )
        # Initialize a powerful, locally-run embedding model
        # This is a good default model that balances performance and size.
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        print("--- CodebaseAnalyzer: RAG components initialized. ---")

    def _load_documents(self, file_paths: List[Path]) -> List[Any]:
        """Loads and returns a list of documents from file paths."""
        documents = []
        for file_path in file_paths:
            if file_path.suffix == ".py":
                # For Python files, we can use TextLoader and our special splitter
                loader = TextLoader(str(file_path), encoding="utf-8")
                documents.extend(loader.load_and_split(self.python_splitter))
            # We could add support for other file types like markdown or PDF here
            # elif file_path.suffix == ".md":
            #     loader = UnstructuredMarkdownLoader(str(file_path))
            #     documents.extend(loader.load())
        return documents

    def create_index(self, file_paths: List[Path]) -> Chroma:
        """Creates a ChromaDB vector store index from a list of file paths."""
        print(f"--- CodebaseAnalyzer: Loading and indexing {len(file_paths)} files... ---")
        documents = self._load_documents(file_paths)
        
        if not documents:
            raise ValueError("No documents were loaded. Check file paths and types.")

        # Create the vector store from the documents.
        # This will download the embedding model on the first run.
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model
        )
        print("--- CodebaseAnalyzer: In-memory vector store created successfully. ---")
        return vectorstore


# ==============================================================================
# --- LangGraph Node Functions ---
# ==============================================================================
# We instantiate the analyzer once to be reused by the nodes.
ANALYZER_INSTANCE = CodebaseAnalyzer()

def ingest_and_index_code_node(state: RedTeamCommanderState) -> Dict[str, Any]:
    """
    The first node in the graph. Reads the user's config, finds the target
    files, and creates the RAG index.
    """
    print("--- Node: Ingest & Index Code ---")
    
    target_config = state["target_config"]
    key_files = target_config.get("key_logic_files", [])
    
    if not key_files:
        raise ValueError("Configuration must provide 'key_logic_files'.")
    
    # Assume the file paths in the config are relative to the project root
    project_root = Path.cwd() # Gets the current working directory
    absolute_file_paths = [project_root / file for file in key_files]
    
    # Use the analyzer to create the index
    code_index = ANALYZER_INSTANCE.create_index(absolute_file_paths)
    
    return {"code_index": code_index}

def draft_capability_description_node(state: RedTeamCommanderState) -> Dict[str, Any]:
    """
    Uses the RAG index to generate a first draft of the agent's capabilities.
    """
    print("--- Node: Draft Capability Description ---")
    code_index = state["code_index"]
    
    # --- This is a placeholder for the RAG + LLM call ---
    
    retriever = code_index