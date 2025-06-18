"""
Test project structure and requirements for the Neo4j graph implementation.

These tests ensure that all files exist and contain the required functionality
as specified in the implementation requirements.
"""

import importlib.util
from pathlib import Path


def load_module_from_path(name: str, path: Path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestGraphProjectStructure:
    """Test that the graph module has the required structure."""

    def test_required_files_exist(self):
        """Ensure all required module files are present."""
        base_path = (
            Path(__file__).parent.parent / "shared" / "aclarai_shared" / "graph"
        )

        required_files = ["__init__.py", "models.py", "neo4j_manager.py"]

        for file_name in required_files:
            file_path = base_path / file_name
            assert file_path.is_file(), f"Required file is missing: {file_path}"
            assert file_path.stat().st_size > 0, f"File is empty: {file_path}"

    def test_neo4j_manager_has_required_methods(self):
        """Validate Neo4j manager has all required methods."""
        manager_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "neo4j_manager.py"
        )

        # Read file content to check for required methods
        with open(manager_path, "r") as f:
            content = f.read()

        required_methods = [
            "setup_schema",
            "create_claims",
            "create_sentences",
            "get_claim_by_id",
            "get_sentence_by_id",
            "count_nodes",
        ]

        for method in required_methods:
            assert f"def {method}" in content, (
                f"Neo4jGraphManager missing required method: {method}"
            )

    def test_neo4j_manager_uses_batch_operations(self):
        """Validate Neo4j manager uses UNWIND for batch operations."""
        manager_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "neo4j_manager.py"
        )

        with open(manager_path, "r") as f:
            content = f.read()

        # Check for batch operations with UNWIND
        assert "UNWIND" in content, (
            "Neo4jGraphManager should use UNWIND for batch operations"
        )
        assert "ORIGINATES_FROM" in content, (
            "Neo4jGraphManager should create ORIGINATES_FROM relationships"
        )

    def test_neo4j_manager_creates_schema(self):
        """Validate Neo4j manager creates proper schema."""
        manager_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "neo4j_manager.py"
        )

        with open(manager_path, "r") as f:
            content = f.read()

        # Check for schema creation
        assert "CREATE CONSTRAINT" in content, (
            "Neo4jGraphManager should create constraints"
        )
        assert "CREATE INDEX" in content, "Neo4jGraphManager should create indexes"


class TestGraphDataModelStructure:
    """Test data model requirements and schema compliance."""

    def test_claim_model_has_required_fields(self):
        """Verify the Claim model has all required fields for Neo4j storage."""
        models_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "models.py"
        )
        models = load_module_from_path("models", models_path)

        # Create test objects
        claim_input = models.ClaimInput(
            text="Test claim",
            block_id="block123",
            entailed_score=0.9,
            coverage_score=0.8,
            decontextualization_score=0.7,
        )
        claim = models.Claim.from_input(claim_input)
        claim_dict = claim.to_dict()

        # Check for properties required by technical_overview.md
        required_fields = {
            "id",
            "text",
            "entailed_score",
            "coverage_score",
            "decontextualization_score",
            "version",
            "timestamp",
        }
        assert required_fields.issubset(claim_dict.keys()), (
            f"Missing required fields in Claim model: {required_fields - set(claim_dict.keys())}"
        )

    def test_sentence_model_has_required_fields(self):
        """Verify the Sentence model has all required fields for Neo4j storage."""
        models_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "models.py"
        )
        models = load_module_from_path("models", models_path)

        # Create test objects
        sentence_input = models.SentenceInput(
            text="Test sentence", block_id="block123", ambiguous=True, verifiable=False
        )
        sentence = models.Sentence.from_input(sentence_input)
        sentence_dict = sentence.to_dict()

        required_fields = {
            "id",
            "text",
            "ambiguous",
            "verifiable",
            "version",
            "timestamp",
        }
        assert required_fields.issubset(sentence_dict.keys()), (
            f"Missing required fields in Sentence model: {required_fields - set(sentence_dict.keys())}"
        )

    def test_claim_input_validation(self):
        """Test ClaimInput has proper field validation."""
        models_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "models.py"
        )
        models = load_module_from_path("models", models_path)

        # Test required fields
        claim_input = models.ClaimInput(
            text="Test claim",
            block_id="block123",
            entailed_score=0.9,
            coverage_score=0.8,
            decontextualization_score=0.7,
        )

        # Check field presence
        assert hasattr(claim_input, "text"), "ClaimInput missing text field"
        assert hasattr(claim_input, "block_id"), "ClaimInput missing block_id field"
        assert hasattr(claim_input, "entailed_score"), (
            "ClaimInput missing entailed_score field"
        )
        assert hasattr(claim_input, "coverage_score"), (
            "ClaimInput missing coverage_score field"
        )
        assert hasattr(claim_input, "decontextualization_score"), (
            "ClaimInput missing decontextualization_score field"
        )
        assert hasattr(claim_input, "claim_id"), "ClaimInput missing claim_id field"

        # Check ID generation
        assert claim_input.claim_id.startswith("claim_"), (
            "ClaimInput claim_id should start with 'claim_'"
        )

    def test_sentence_input_validation(self):
        """Test SentenceInput has proper field validation."""
        models_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "models.py"
        )
        models = load_module_from_path("models", models_path)

        # Test required fields
        sentence_input = models.SentenceInput(
            text="Test sentence", block_id="block123", ambiguous=True
        )

        # Check field presence
        assert hasattr(sentence_input, "text"), "SentenceInput missing text field"
        assert hasattr(sentence_input, "block_id"), (
            "SentenceInput missing block_id field"
        )
        assert hasattr(sentence_input, "ambiguous"), (
            "SentenceInput missing ambiguous field"
        )
        assert hasattr(sentence_input, "sentence_id"), (
            "SentenceInput missing sentence_id field"
        )

        # Check ID generation
        assert sentence_input.sentence_id.startswith("sentence_"), (
            "SentenceInput sentence_id should start with 'sentence_'"
        )

    def test_metadata_fields_present(self):
        """Test that version and timestamp metadata are added during conversion."""
        models_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "models.py"
        )
        models = load_module_from_path("models", models_path)

        # Test Claim metadata
        claim_input = models.ClaimInput(text="Test claim", block_id="block123")
        claim = models.Claim.from_input(claim_input)

        assert hasattr(claim, "version"), "Claim missing version field"
        assert hasattr(claim, "timestamp"), "Claim missing timestamp field"
        assert claim.version == 1, "Claim version should default to 1"

        # Test Sentence metadata
        sentence_input = models.SentenceInput(text="Test sentence", block_id="block123")
        sentence = models.Sentence.from_input(sentence_input)

        assert hasattr(sentence, "version"), "Sentence missing version field"
        assert hasattr(sentence, "timestamp"), "Sentence missing timestamp field"
        assert sentence.version == 1, "Sentence version should default to 1"

    def test_schema_compliance_with_technical_overview(self):
        """Validate schema compliance with technical_overview.md requirements."""
        models_path = (
            Path(__file__).parent.parent
            / "shared"
            / "aclarai_shared"
            / "graph"
            / "models.py"
        )
        models = load_module_from_path("models", models_path)

        # Create test objects
        claim_input = models.ClaimInput(text="Test", block_id="block123")
        claim = models.Claim.from_input(claim_input)

        sentence_input = models.SentenceInput(text="Test", block_id="block123")
        sentence = models.Sentence.from_input(sentence_input)

        # Validate Claim schema compliance with technical overview
        claim_dict = claim.to_dict()

        technical_overview_claim_props = [
            "id",  # claim_id in the spec
            "text",
            "entailed_score",
            "coverage_score",
            "decontextualization_score",
        ]

        for prop in technical_overview_claim_props:
            assert prop in claim_dict, (
                f"Claim missing property from technical_overview.md: {prop}"
            )

        # Check for additional metadata requirements
        metadata_props = ["version", "timestamp"]
        for prop in metadata_props:
            assert prop in claim_dict, f"Claim missing metadata property: {prop}"

        # Validate Sentence schema compliance
        sentence_dict = sentence.to_dict()

        technical_overview_sentence_props = [
            "id",  # sentence_id in the spec
            "text",
            "ambiguous",
        ]

        for prop in technical_overview_sentence_props:
            assert prop in sentence_dict, (
                f"Sentence missing property from technical_overview.md: {prop}"
            )
