from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self, model: Optional[SentenceTransformer] = None):
        """Initialize the NLP processor with an optional preloaded model."""
        self._model = model
        logger.info("NLPProcessor initialized (model will be loaded on first use)")

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model when first needed."""
        if self._model is None:
            logger.info("Loading sentence transformer model...")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
        return self._model

    def extract_thesis(self, text: str) -> List[str]:
        """Extract thesis statements from text."""
        try:
            # Split text into sentences
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return []
            
            # Get embeddings for all sentences
            embeddings = self.model.encode(sentences)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Find the most central sentence (highest average similarity to others)
            avg_similarities = np.mean(similarity_matrix, axis=1)
            central_idx = np.argmax(avg_similarities)
            
            # Return the most central sentence as the thesis
            return [sentences[central_idx]]
            
        except Exception as e:
            logger.error(f"Error extracting thesis: {str(e)}")
            return []

    def find_similar_theme(self, thesis: str, existing_themes: List[Tuple[int, str]], threshold: float = 0.8) -> Tuple[bool, Optional[int]]:
        """Find if there's a similar theme to the given thesis."""
        try:
            if not existing_themes:
                return False, None
                
            # Get embedding for the new thesis
            thesis_embedding = self.model.encode([thesis])[0]
            
            # Get embeddings for existing themes
            theme_texts = [theme[1] for theme in existing_themes]
            theme_embeddings = self.model.encode(theme_texts)
            
            # Calculate similarities
            similarities = cosine_similarity([thesis_embedding], theme_embeddings)[0]
            
            # Find the most similar theme
            max_similarity_idx = np.argmax(similarities)
            max_similarity = similarities[max_similarity_idx]
            
            if max_similarity >= threshold:
                return True, existing_themes[max_similarity_idx][0]
            return False, None
            
        except Exception as e:
            logger.error(f"Error finding similar theme: {str(e)}")
            return False, None 