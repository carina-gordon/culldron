import pytest
from app.nlp_processor import NLPProcessor

def test_extract_thesis():
    processor = NLPProcessor()
    
    # Test with a simple text
    text = "This is the first sentence. This is a similar sentence. This is a different topic."
    thesis = processor.extract_thesis(text)
    
    assert len(thesis) <= processor.max_thesis_sentences
    assert all(isinstance(s, str) for s in thesis)
    assert all(s in text for s in thesis)

def test_find_similar_theme():
    processor = NLPProcessor()
    
    # Test with similar themes
    existing_themes = [
        (1, "The impact of climate change on agriculture"),
        (2, "New developments in quantum computing")
    ]
    
    # Test similar theme
    is_similar, theme_id = processor.find_similar_theme(
        "Climate change effects on farming and crops",
        existing_themes
    )
    assert is_similar
    assert theme_id == 1
    
    # Test different theme
    is_similar, theme_id = processor.find_similar_theme(
        "The history of ancient Rome",
        existing_themes
    )
    assert not is_similar
    assert theme_id is None 