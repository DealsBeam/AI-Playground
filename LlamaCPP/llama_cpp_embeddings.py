import gc
import os
from typing import List, Optional

from langchain_community.embeddings import LlamaCppEmbeddings
import utils

class LlamaCppEmbeddingModel:
    _instance = None
    
    @classmethod
    def get_instance(cls, repo_id: Optional[str] = None):
        """
        Get a singleton instance of the embedding model.
        If an instance already exists, return it.
        If repo_id is provided, create a new instance with that model.
        """
        if cls._instance is None and repo_id is not None:
            cls._instance = cls(repo_id)
        return cls._instance
    
    def __init__(self, repo_id: str = "ChristianAzinn/bge-small-en-v1.5-gguf"):
        """
        Initialize the embedding model class but don't load the model yet.
        The model will be loaded on-demand when needed.
        """
        self.repo_id = repo_id
        self.embedding = None
        self.embedding_model_path = repo_id
    
    def _load_model(self):
        """
        Dynamically load the model when needed.
        """
        if self.embedding is not None:
            return
            
        model_base_path = utils.get_model_path(5, "llama_cpp")  # 5 is the type for embedding models
        model_dir = os.path.join(
            '../service',
            model_base_path, 
            utils.repo_local_root_dir_name(self.repo_id),
            utils.extract_model_id_pathsegments(self.repo_id)
        )
        
        # Find the GGUF file in the directory
        gguf_files = [f for f in os.listdir(model_dir) if f.endswith('.gguf')]
        if not gguf_files:
            raise FileNotFoundError(f"No GGUF files found in {model_dir}")
        
        model_path = os.path.join(model_dir, gguf_files[0])
        
        print(f"******* loading LlamaCpp embedding model {model_path} start")
        self.embedding = LlamaCppEmbeddings(
            model_path=model_path
        )
        print(f"******* loading LlamaCpp embedding model {model_path} finish")

    def _unload_model(self):
        """
        Unload the model to free up VRAM.
        """
        if self.embedding is not None:
            del self.embedding
            self.embedding = None
            gc.collect()
            print(f"******* unloaded LlamaCpp embedding model to free VRAM")

    def embed_query(self, text: str):
        """
        Embed a single query.
        """
        try:
            self._load_model()
            return self.embedding.embed_query(text)
        finally:
            self._unload_model()

    def embed_documents(self, texts: List[str]):
        """
        Embed a list of documents.
        Loads the model if not already loaded, then unloads it after use.
        """
        try:
            self._load_model()
            return self.embedding.embed_documents(texts)
        finally:
            self._unload_model()
