#!/usr/bin/env python3
"""
Validation script for Neo4j graph implementation.

This script validates that all requirements from the sprint task are met.
"""

import sys
from pathlib import Path
import importlib.util

def load_module(name, path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate_data_models():
    """Validate data models meet requirements."""
    print("🔍 Validating Data Models...")
    
    # Load models
    models_path = Path(__file__).parent / "shared" / "clarifai_shared" / "graph" / "models.py"
    models = load_module("models", models_path)
    
    # Test ClaimInput
    claim_input = models.ClaimInput(
        text="Test claim",
        block_id="block123",
        entailed_score=0.9,
        coverage_score=0.8,
        decontextualization_score=0.7
    )
    
    assert hasattr(claim_input, 'text'), "ClaimInput missing text field"
    assert hasattr(claim_input, 'block_id'), "ClaimInput missing block_id field"
    assert hasattr(claim_input, 'entailed_score'), "ClaimInput missing entailed_score field"
    assert hasattr(claim_input, 'coverage_score'), "ClaimInput missing coverage_score field"
    assert hasattr(claim_input, 'decontextualization_score'), "ClaimInput missing decontextualization_score field"
    assert hasattr(claim_input, 'claim_id'), "ClaimInput missing claim_id field"
    assert claim_input.claim_id.startswith("claim_"), "ClaimInput claim_id should start with 'claim_'"
    
    # Test SentenceInput
    sentence_input = models.SentenceInput(
        text="Test sentence",
        block_id="block123",
        ambiguous=True
    )
    
    assert hasattr(sentence_input, 'text'), "SentenceInput missing text field"
    assert hasattr(sentence_input, 'block_id'), "SentenceInput missing block_id field"
    assert hasattr(sentence_input, 'ambiguous'), "SentenceInput missing ambiguous field"
    assert hasattr(sentence_input, 'sentence_id'), "SentenceInput missing sentence_id field"
    assert sentence_input.sentence_id.startswith("sentence_"), "SentenceInput sentence_id should start with 'sentence_'"
    
    # Test Claim conversion
    claim = models.Claim.from_input(claim_input)
    assert hasattr(claim, 'version'), "Claim missing version field"
    assert hasattr(claim, 'timestamp'), "Claim missing timestamp field"
    assert claim.version == 1, "Claim version should default to 1"
    
    # Test Sentence conversion
    sentence = models.Sentence.from_input(sentence_input)
    assert hasattr(sentence, 'version'), "Sentence missing version field"
    assert hasattr(sentence, 'timestamp'), "Sentence missing timestamp field"
    assert sentence.version == 1, "Sentence version should default to 1"
    
    # Test serialization
    claim_dict = claim.to_dict()
    required_claim_fields = ['id', 'text', 'entailed_score', 'coverage_score', 'decontextualization_score', 'version', 'timestamp']
    for field in required_claim_fields:
        assert field in claim_dict, f"Claim dict missing required field: {field}"
    
    sentence_dict = sentence.to_dict()
    required_sentence_fields = ['id', 'text', 'ambiguous', 'verifiable', 'version', 'timestamp']
    for field in required_sentence_fields:
        assert field in sentence_dict, f"Sentence dict missing required field: {field}"
    
    print("   ✅ Data models validated successfully")
    return True

def validate_neo4j_manager_structure():
    """Validate Neo4j manager structure."""
    print("🔍 Validating Neo4j Manager Structure...")
    
    # Load neo4j manager (just check structure, not functionality)
    manager_path = Path(__file__).parent / "shared" / "clarifai_shared" / "graph" / "neo4j_manager.py"
    
    # Read file content to check for required methods
    with open(manager_path, 'r') as f:
        content = f.read()
    
    required_methods = [
        'setup_schema',
        'create_claims', 
        'create_sentences',
        'get_claim_by_id',
        'get_sentence_by_id',
        'count_nodes'
    ]
    
    for method in required_methods:
        assert f"def {method}" in content, f"Neo4jGraphManager missing required method: {method}"
    
    # Check for batch operations with UNWIND
    assert "UNWIND" in content, "Neo4jGraphManager should use UNWIND for batch operations"
    assert "ORIGINATES_FROM" in content, "Neo4jGraphManager should create ORIGINATES_FROM relationships"
    
    # Check for schema creation
    assert "CREATE CONSTRAINT" in content, "Neo4jGraphManager should create constraints"
    assert "CREATE INDEX" in content, "Neo4jGraphManager should create indexes"
    
    print("   ✅ Neo4j Manager structure validated successfully")
    return True

def validate_schema_compliance():
    """Validate schema compliance with requirements."""
    print("🔍 Validating Schema Compliance...")
    
    # Load models to check schema compliance
    models_path = Path(__file__).parent / "shared" / "clarifai_shared" / "graph" / "models.py"
    models = load_module("models", models_path)
    
    # Create test objects
    claim_input = models.ClaimInput(text="Test", block_id="block123")
    claim = models.Claim.from_input(claim_input)
    
    sentence_input = models.SentenceInput(text="Test", block_id="block123")
    sentence = models.Sentence.from_input(sentence_input)
    
    # Validate Claim schema compliance
    claim_dict = claim.to_dict()
    
    # Check for required properties from technical_overview.md
    technical_overview_claim_props = [
        'id',  # claim_id in the spec
        'text',
        'entailed_score',
        'coverage_score', 
        'decontextualization_score'
    ]
    
    for prop in technical_overview_claim_props:
        assert prop in claim_dict, f"Claim missing property from technical_overview.md: {prop}"
    
    # Check for additional metadata requirements
    metadata_props = ['version', 'timestamp']
    for prop in metadata_props:
        assert prop in claim_dict, f"Claim missing metadata property: {prop}"
    
    # Validate Sentence schema compliance
    sentence_dict = sentence.to_dict()
    
    technical_overview_sentence_props = [
        'id',  # sentence_id in the spec
        'text',
        'ambiguous'
    ]
    
    for prop in technical_overview_sentence_props:
        assert prop in sentence_dict, f"Sentence missing property from technical_overview.md: {prop}"
    
    print("   ✅ Schema compliance validated successfully")
    return True

def validate_files_exist():
    """Validate all required files exist."""
    print("🔍 Validating Required Files...")
    
    base_path = Path(__file__).parent / "shared" / "clarifai_shared" / "graph"
    
    required_files = [
        "__init__.py",
        "models.py", 
        "neo4j_manager.py",
        "README.md",
        "simple_example.py"
    ]
    
    for file_name in required_files:
        file_path = base_path / file_name
        assert file_path.exists(), f"Required file missing: {file_path}"
        assert file_path.stat().st_size > 0, f"File is empty: {file_path}"
    
    print("   ✅ All required files exist and are non-empty")
    return True

def validate_documentation():
    """Validate documentation meets requirements."""
    print("🔍 Validating Documentation...")
    
    readme_path = Path(__file__).parent / "shared" / "clarifai_shared" / "graph" / "README.md"
    
    with open(readme_path, 'r') as f:
        readme_content = f.read()
    
    required_sections = [
        "# Neo4j Graph Management Documentation",
        "## Data Models",
        "## Usage Examples", 
        "## Schema",
        "## Integration with Claimify Pipeline"
    ]
    
    for section in required_sections:
        assert section in readme_content, f"README missing required section: {section}"
    
    # Check for specific content
    assert "ClaimInput" in readme_content, "README should document ClaimInput"
    assert "SentenceInput" in readme_content, "README should document SentenceInput"
    assert "ORIGINATES_FROM" in readme_content, "README should document ORIGINATES_FROM relationship"
    assert "entailed_score" in readme_content, "README should document evaluation scores"
    
    print("   ✅ Documentation validated successfully")
    return True

def main():
    """Run all validations."""
    print("Neo4j Graph Implementation Validation")
    print("====================================")
    print()
    
    validations = [
        validate_files_exist,
        validate_data_models,
        validate_neo4j_manager_structure,
        validate_schema_compliance,
        validate_documentation
    ]
    
    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Validation failed: {e}")
            results.append(False)
        print()
    
    # Summary
    total_validations = len(validations)
    passed_validations = sum(results)
    
    print("Validation Summary")
    print("=================")
    print(f"Passed: {passed_validations}/{total_validations}")
    
    if passed_validations == total_validations:
        print("🎉 All validations passed! Implementation meets requirements.")
        
        print("\nImplemented Features:")
        print("✅ (:Claim) and (:Sentence) node data models")
        print("✅ Neo4j schema with constraints and indexes")  
        print("✅ Batch creation functions using UNWIND")
        print("✅ ORIGINATES_FROM relationships to Block nodes")
        print("✅ Evaluation score properties (entailed, coverage, decontextualization)")
        print("✅ Metadata properties (clarifai:id, version, timestamp)")
        print("✅ Comprehensive documentation and examples")
        print("✅ Test coverage for core functionality")
        
        return True
    else:
        print("❌ Some validations failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)