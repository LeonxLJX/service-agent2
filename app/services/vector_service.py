import numpy as np
import faiss
from typing import List, Tuple, Optional
from app.config import settings
from loguru import logger


class VectorService:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.vectors: List[np.ndarray] = []
        self.metadata: List[dict] = []

    def init_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        logger.info(f"FAISS index initialized with dimension {self.dimension}")

    def add_vector(self, vector: np.ndarray, metadata: dict):
        if self.index is None:
            self.init_index()

        vec = np.asarray(vector, dtype=np.float32)
        if vec.shape != (self.dimension,):
            vec = vec.reshape(-1)
            if vec.shape[0] < self.dimension:
                vec = np.pad(vec, (0, self.dimension - vec.shape[0]))
            else:
                vec = vec[:self.dimension]

        self.index.add(vec.reshape(1, -1))
        self.vectors.append(vec)
        self.metadata.append(metadata)

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[int, float, dict]]:
        if self.index is None or self.index.ntotal == 0:
            return []

        vec = np.asarray(query_vector, dtype=np.float32)
        if vec.shape != (self.dimension,):
            vec = vec.reshape(-1)
            if vec.shape[0] < self.dimension:
                vec = np.pad(vec, (0, self.dimension - vec.shape[0]))
            else:
                vec = vec[:self.dimension]

        distances, indices = self.index.search(vec.reshape(1, -1), min(top_k, self.index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                results.append((int(idx), float(distances[0][i]), self.metadata[idx]))

        return results

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        vec1 = vec1.flatten()
        vec2 = vec2.flatten()
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def text_to_vector(self, text: str) -> np.ndarray:
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        seed = int.from_bytes(hash_bytes[:4], byteorder='big')
        np.random.seed(seed % (2**32))
        return np.random.randn(self.dimension).astype(np.float32)


vector_service = VectorService(dimension=settings.vector_dimension)
