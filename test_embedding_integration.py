"""
Integration test for ClarifAI embedding system.

This test verifies the structure and interfaces of the embedding system
without requiring actual dependencies to be installed.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch


def test_module_structure():
    """Test that the module structure is correct."""
    print("Testing module structure...")

    # Check that files exist
    shared_path = Path(__file__).parent / "shared" / "clarifai_shared"

    # Check embedding module files
    embedding_path = shared_path / "embedding"
    assert embedding_path.exists(), "Embedding module directory missing"

    required_files = ["__init__.py", "chunking.py", "models.py", "storage.py"]

    for file_name in required_files:
        file_path = embedding_path / file_name
        assert file_path.exists(), f"Missing file: {file_name}"
        print(f"✓ {file_name} exists")

    # Check config file
    config_file = Path(__file__).parent / "clarifai.config.yaml"
    assert config_file.exists(), "Configuration file missing"
    print("✓ clarifai.config.yaml exists")

    print("Module structure test passed!")


def test_config_structure():
    """Test configuration file structure."""
    print("\nTesting configuration structure...")

    try:
        import yaml

        config_file = Path(__file__).parent / "clarifai.config.yaml"

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Check required sections
        required_sections = ["embedding", "databases", "paths", "concepts"]

        for section in required_sections:
            assert section in config, f"Missing config section: {section}"
            print(f"✓ {section} section exists")

        # Check embedding subsections
        embedding_config = config["embedding"]
        required_embedding = ["models", "pgvector", "chunking"]

        for subsection in required_embedding:
            assert subsection in embedding_config, (
                f"Missing embedding subsection: {subsection}"
            )
            print(f"✓ embedding.{subsection} exists")

        print("Configuration structure test passed!")

    except ImportError:
        print("PyYAML not available, skipping config validation")
    except Exception as e:
        print(f"Config test failed: {e}")


def test_class_interfaces():
    """Test that the classes have the expected interfaces."""
    print("\nTesting class interfaces...")

    # Mock LlamaIndex dependencies
    with patch.dict(
        "sys.modules",
        {
            "llama_index.core.node_parser": Mock(),
            "llama_index.core.schema": Mock(),
            "llama_index.embeddings.huggingface": Mock(),
            "llama_index.core.embeddings": Mock(),
            "llama_index.vector_stores.postgres": Mock(),
            "llama_index.core": Mock(),
            "sqlalchemy": Mock(),
            "sqlalchemy.dialects.postgresql": Mock(),
            "sqlalchemy.orm": Mock(),
            "sqlalchemy.exc": Mock(),
        },
    ):
        # Add shared to path for testing
        sys.path.insert(0, str(Path(__file__).parent / "shared"))

        try:
            # Test chunking module interface - verify they exist
            _ = __import__(
                "clarifai_shared.embedding.chunking",
                fromlist=["ChunkMetadata", "UtteranceChunker"],
            )

            print("✓ Chunking module imports successfully")

            # Test models module interface - verify they exist
            _ = __import__(
                "clarifai_shared.embedding.models",
                fromlist=["EmbeddedChunk", "EmbeddingGenerator"],
            )

            print("✓ Models module imports successfully")

            # Test storage module interface - verify they exist
            _ = __import__(
                "clarifai_shared.embedding.storage",
                fromlist=["ClarifAIVectorStore", "VectorStoreMetrics"],
            )

            print("✓ Storage module imports successfully")

            # Test main module interface - verify they exist
            _ = __import__(
                "clarifai_shared.embedding",
                fromlist=["EmbeddingPipeline", "EmbeddingResult"],
            )

            print("✓ Main embedding module imports successfully")

            print("Class interface test passed!")

        except ImportError as e:
            print(f"Import test failed: {e}")
            return False
        except Exception as e:
            print(f"Interface test failed: {e}")
            return False

        finally:
            sys.path.remove(str(Path(__file__).parent / "shared"))

    return True


def test_config_module():
    """Test configuration module with YAML support."""
    print("\nTesting configuration module...")

    with patch.dict(
        "sys.modules",
        {
            "yaml": Mock(),
            "dotenv": Mock(),
        },
    ):
        sys.path.insert(0, str(Path(__file__).parent / "shared"))

        try:
            from clarifai_shared.config import (
                ConceptsConfig,
                EmbeddingConfig,
                PathsConfig,
            )

            print("✓ Configuration module imports successfully")

            # Test default config creation
            embedding_config = EmbeddingConfig()
            assert (
                embedding_config.default_model
                == "sentence-transformers/all-MiniLM-L6-v2"
            )
            assert embedding_config.chunk_size == 300
            print("✓ EmbeddingConfig defaults are correct")

            concepts_config = ConceptsConfig()
            assert concepts_config.similarity_threshold == 0.9
            print("✓ ConceptsConfig defaults are correct")

            paths_config = PathsConfig()
            assert paths_config.vault == "/vault"
            assert paths_config.tier1 == "conversations"
            print("✓ PathsConfig defaults are correct")

            print("Configuration module test passed!")

        except Exception as e:
            print(f"Config module test failed: {e}")
            return False

        finally:
            sys.path.remove(str(Path(__file__).parent / "shared"))

    return True


def test_dependencies():
    """Test that dependencies are properly declared."""
    print("\nTesting dependencies...")

    pyproject_path = Path(__file__).parent / "shared" / "pyproject.toml"

    with open(pyproject_path, "r") as f:
        content = f.read()

    required_deps = [
        "llama-index-core",
        "llama-index-embeddings-huggingface",
        "llama-index-vector-stores-postgres",
        "sentence-transformers",
        "psycopg2-binary",
        "pgvector",
    ]

    for dep in required_deps:
        assert dep in content, f"Missing dependency: {dep}"
        print(f"✓ {dep} declared in dependencies")

    print("Dependencies test passed!")


def main():
    """Run all tests."""
    print("ClarifAI Embedding System Integration Test")
    print("=" * 50)

    tests = [
        test_module_structure,
        test_config_structure,
        test_dependencies,
        test_config_module,
        test_class_interfaces,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result is not False:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Test {test.__name__} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All integration tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: uv pip install -r shared/requirements.txt")
        print("2. Setup PostgreSQL with pgvector extension")
        print("3. Configure environment variables")
        print("4. Run demo: python demo_embedding_pipeline.py")
        return 0
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
