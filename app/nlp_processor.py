from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
import os
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
        self.max_thesis_sentences = int(os.getenv("MAX_THESIS_SENTENCES", "2"))

    def extract_thesis(self, text: str) -> List[str]:
        """
        Extract the main thesis statements from the text.
        Returns a list of 1-2 key sentences that represent the main points.
        """
        # Split into sentences (simple approach - can be improved)
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not sentences:
            return []
        
        # Get embeddings for all sentences
        embeddings = self.model.encode(sentences)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Find the most representative sentences
        # (those that are most similar to other sentences)
        sentence_scores = np.sum(similarity_matrix, axis=1)
        top_indices = np.argsort(sentence_scores)[-self.max_thesis_sentences:]
        
        # Return the top sentences in their original order
        return [sentences[i] for i in sorted(top_indices)]

    def find_similar_theme(self, thesis: str, existing_themes: List[Tuple[int, str]]) -> Tuple[bool, int]:
        """
        Check if the thesis is similar to any existing theme.
        Returns (is_similar, theme_id) tuple.
        """
        if not existing_themes:
            return False, None

        # Get embeddings
        thesis_embedding = self.model.encode([thesis])[0]
        theme_embeddings = self.model.encode([t[1] for t in existing_themes])
        
        # Calculate similarities
        similarities = cosine_similarity([thesis_embedding], theme_embeddings)[0]
        
        # Find the most similar theme
        max_similarity_idx = np.argmax(similarities)
        max_similarity = similarities[max_similarity_idx]
        
        if max_similarity >= self.similarity_threshold:
            return True, existing_themes[max_similarity_idx][0]
        
        return False, None 