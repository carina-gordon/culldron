from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def preload_model():
    """
    Pre-download the SentenceTransformer model to improve initial loading time.
    """
    try:
        logger.info("Starting model pre-download...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model successfully downloaded and cached")
        return model
    except Exception as e:
        logger.error(f"Error preloading model: {str(e)}")
        raise

if __name__ == "__main__":
    preload_model() 