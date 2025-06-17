#!/usr/bin/env python3
"""
Simple test script to verify noun phrase extraction functionality.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_spacy_basic():
    """Test basic spaCy functionality."""
    try:
        import spacy
        
        # Load the model
        nlp = spacy.load("en_core_web_sm")
        
        # Test text
        text = "The large international consortium of researchers developed new algorithms for natural language processing."
        
        # Process text
        doc = nlp(text)
        
        # Extract noun chunks
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        print("Original text:", text)
        print("Extracted noun phrases:", noun_phrases)
        
        # Test normalization
        for phrase in noun_phrases:
            doc_phrase = nlp(phrase.lower())
            lemmatized = ' '.join([token.lemma_ for token in doc_phrase if not token.is_punct and not token.is_space])
            print(f"  '{phrase}' -> '{lemmatized}'")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_extractor_imports():
    """Test that our modules can be imported."""
    try:
        from clarifai_shared.noun_phrase_extraction.models import NounPhraseCandidate, ExtractionResult
        print("Successfully imported models")
        
        # Test creating a candidate
        candidate = NounPhraseCandidate(
            text="natural language processing",
            normalized_text="natural language processing",
            source_node_id="test_id",
            source_node_type="claim",
            clarifai_id="test_clarifai_id"
        )
        print(f"Created candidate: {candidate.text} -> {candidate.normalized_text}")
        
        return True
        
    except Exception as e:
        print(f"Import error: {e}")
        return False

if __name__ == "__main__":
    print("Testing spaCy functionality...")
    if test_spacy_basic():
        print("✓ spaCy test passed")
    else:
        print("✗ spaCy test failed")
        sys.exit(1)
    
    print("\nTesting extractor imports...")
    if test_extractor_imports():
        print("✓ Import test passed")
    else:
        print("✗ Import test failed")
        sys.exit(1)
    
    print("\n✓ All basic tests passed!")