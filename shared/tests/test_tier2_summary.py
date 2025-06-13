"""
Tests for the Tier 2 Summary Agent module.

This test suite validates the functionality of the Tier 2 Summary Agent including
data models, summary generation, and file writing operations.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from clarifai_shared.tier2_summary import (
    Tier2SummaryAgent,
    SummaryInput,
    SummaryBlock,
    SummaryResult,
    generate_summary_id,
)
from clarifai_shared.config import ClarifAIConfig


class TestSummaryDataModels:
    """Test the data models for Tier 2 Summary."""

    def test_summary_input_creation(self):
        """Test SummaryInput object creation and properties."""
        claims = [
            {"id": "claim1", "text": "First claim", "node_type": "claim", "block_id": "blk_001"},
            {"id": "claim2", "text": "Second claim", "node_type": "claim", "block_id": "blk_002"},
        ]
        sentences = [
            {"id": "sent1", "text": "First sentence", "node_type": "sentence", "block_id": "blk_003"},
        ]

        summary_input = SummaryInput(
            claims=claims,
            sentences=sentences,
            group_context="Test context"
        )

        assert len(summary_input.claims) == 2
        assert len(summary_input.sentences) == 1
        assert summary_input.group_context == "Test context"

        # Test all_texts property
        all_texts = summary_input.all_texts
        assert len(all_texts) == 3
        assert "First claim" in all_texts
        assert "Second claim" in all_texts
        assert "First sentence" in all_texts

        # Test source_block_ids property
        block_ids = summary_input.source_block_ids
        assert len(block_ids) == 3
        assert "blk_001" in block_ids
        assert "blk_002" in block_ids
        assert "blk_003" in block_ids

    def test_summary_block_creation(self):
        """Test SummaryBlock object creation and markdown generation."""
        summary_block = SummaryBlock(
            summary_text="This is a test summary\nWith multiple lines",
            clarifai_id="clm_test123",
            version=2,
            source_block_ids=["blk_001", "blk_002"]
        )

        assert summary_block.summary_text == "This is a test summary\nWith multiple lines"
        assert summary_block.clarifai_id == "clm_test123"
        assert summary_block.version == 2
        assert summary_block.source_block_ids == ["blk_001", "blk_002"]
        assert summary_block.timestamp is not None

    def test_summary_block_markdown_generation(self):
        """Test markdown generation from SummaryBlock."""
        summary_block = SummaryBlock(
            summary_text="First point\nSecond point",
            clarifai_id="clm_abc123",
            version=1
        )

        markdown = summary_block.to_markdown()
        
        # Check structure
        assert "- First point" in markdown
        assert "- Second point ^clm_abc123" in markdown  # Last line gets anchor
        assert "<!-- clarifai:id=clm_abc123 ver=1 -->" in markdown
        assert "^clm_abc123" in markdown

        # Check it ends with anchor
        lines = markdown.strip().split('\n')
        assert lines[-1] == "^clm_abc123"

    def test_summary_result_creation(self):
        """Test SummaryResult object creation and properties."""
        block1 = SummaryBlock(
            summary_text="First summary",
            clarifai_id="clm_001"
        )
        block2 = SummaryBlock(
            summary_text="Second summary", 
            clarifai_id="clm_002"
        )

        result = SummaryResult(
            summary_blocks=[block1, block2],
            source_file_context="Test conversation",
            processing_time=1.5,
            model_used="gpt-3.5-turbo"
        )

        assert len(result.summary_blocks) == 2
        assert result.source_file_context == "Test conversation"
        assert result.processing_time == 1.5
        assert result.model_used == "gpt-3.5-turbo"
        assert result.is_successful is True
        assert result.error is None

    def test_summary_result_error_case(self):
        """Test SummaryResult with error."""
        result = SummaryResult(
            error="Test error message",
            processing_time=0.5
        )

        assert result.is_successful is False
        assert result.error == "Test error message"
        assert len(result.summary_blocks) == 0

    def test_summary_result_markdown_generation(self):
        """Test full markdown file generation from SummaryResult."""
        block1 = SummaryBlock(
            summary_text="First summary point",
            clarifai_id="clm_001"
        )
        block2 = SummaryBlock(
            summary_text="Second summary point",
            clarifai_id="clm_002"
        )

        result = SummaryResult(
            summary_blocks=[block1, block2],
            source_file_context="test_context"
        )

        markdown = result.to_markdown(title="Test Summary")
        
        # Check title
        assert "# Test Summary" in markdown
        
        # Check context metadata
        assert "<!-- clarifai:source_context=test_context -->" in markdown
        
        # Check both blocks are present
        assert "clm_001" in markdown
        assert "clm_002" in markdown
        
        # Check structure - blocks should be separated by empty lines
        assert "clm_001\n\n- Second summary point" in markdown

    def test_generate_summary_id(self):
        """Test summary ID generation."""
        id1 = generate_summary_id()
        id2 = generate_summary_id()
        
        # Should start with clm_
        assert id1.startswith("clm_")
        assert id2.startswith("clm_")
        
        # Should be unique
        assert id1 != id2
        
        # Should have correct length (clm_ + 8 hex chars = 12 total)
        assert len(id1) == 12
        assert len(id2) == 12


class TestTier2SummaryAgent:
    """Test the main Tier2SummaryAgent class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=ClarifAIConfig)
        
        # Create nested mock structure for llm and paths
        config.llm = Mock()
        config.llm.models = {"default": "gpt-3.5-turbo"}
        config.llm.temperature = 0.1
        config.llm.max_tokens = 1000
        
        config.paths = Mock()
        config.paths.vault = "/test/vault"
        config.paths.tier2 = "summaries"
        
        return config

    @pytest.fixture
    def mock_neo4j_manager(self):
        """Create a mock Neo4j manager for testing."""
        manager = Mock()
        # Mock execute_query to return test data
        manager.execute_query.return_value = [
            {
                'id': 'claim1',
                'text': 'Test claim 1',
                'entailed_score': 0.8,
                'coverage_score': 0.9,
                'decontextualization_score': 0.7,
                'version': 1,
                'timestamp': '2024-01-01T10:00:00Z'
            },
            {
                'id': 'claim2',
                'text': 'Test claim 2',
                'entailed_score': 0.75,
                'coverage_score': 0.85,
                'decontextualization_score': 0.8,
                'version': 1,
                'timestamp': '2024-01-01T11:00:00Z'
            }
        ]
        return manager

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = Mock()
        llm.model = "gpt-3.5-turbo"
        
        # Mock complete method
        response = Mock()
        response.text = "- Key finding from analysis\n- Important claim identified\n- Summary of main points"
        llm.complete.return_value = response
        
        return llm

    def test_agent_initialization(self, mock_config, mock_neo4j_manager, mock_llm):
        """Test agent initialization with different configurations."""
        # Test with all parameters provided
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        assert agent.config == mock_config
        assert agent.neo4j_manager == mock_neo4j_manager
        assert agent.llm == mock_llm

    def test_agent_initialization_defaults(self):
        """Test agent initialization with defaults."""
        # Mock ClarifAIConfig to avoid loading actual config file
        with patch('clarifai_shared.tier2_summary.agent.ClarifAIConfig') as mock_config_class:
            mock_config = Mock()
            mock_config.llm.models = {"default": "gpt-3.5-turbo"}
            mock_config.llm.temperature = 0.1
            mock_config.llm.max_tokens = 1000
            mock_config_class.return_value = mock_config

            with patch('clarifai_shared.tier2_summary.agent.OpenAI') as mock_openai:
                mock_llm = Mock()
                mock_openai.return_value = mock_llm
                
                agent = Tier2SummaryAgent()
                
                assert agent.config == mock_config
                mock_openai.assert_called_once_with(
                    model="gpt-3.5-turbo",
                    temperature=0.1,
                    max_tokens=1000
                )

    def test_get_all_claims(self, mock_config, mock_neo4j_manager, mock_llm):
        """Test retrieval of all claims from Neo4j."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        claims = agent._get_all_claims()
        
        assert len(claims) == 2
        assert claims[0]['id'] == 'claim1'
        assert claims[0]['text'] == 'Test claim 1'
        assert claims[0]['node_type'] == 'claim'
        assert claims[1]['id'] == 'claim2'
        
        # Verify Neo4j query was called
        mock_neo4j_manager.execute_query.assert_called_once()
        call_args = mock_neo4j_manager.execute_query.call_args[0]
        assert "MATCH (c:Claim)" in call_args[0]

    def test_get_all_claims_error_handling(self, mock_config, mock_llm):
        """Test error handling in claim retrieval."""
        mock_neo4j_manager = Mock()
        mock_neo4j_manager.execute_query.side_effect = Exception("Database error")
        
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        claims = agent._get_all_claims()
        
        # Should return empty list on error
        assert claims == []

    def test_generate_summary(self, mock_config, mock_neo4j_manager, mock_llm):
        """Test summary generation from SummaryInput."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        summary_input = SummaryInput(
            claims=[{"text": "Test claim", "node_type": "claim"}],
            sentences=[{"text": "Test sentence", "node_type": "sentence"}],
            group_context="Test context"
        )

        result = agent.generate_summary(summary_input)
        
        assert result.is_successful
        assert len(result.summary_blocks) == 1
        assert result.error is None
        assert result.processing_time is not None
        assert result.model_used == "gpt-3.5-turbo"
        
        # Check summary block content
        block = result.summary_blocks[0]
        assert "Key finding from analysis" in block.summary_text
        assert block.clarifai_id.startswith("clm_")
        
        # Verify LLM was called
        mock_llm.complete.assert_called_once()

    def test_generate_summary_empty_input(self, mock_config, mock_neo4j_manager, mock_llm):
        """Test summary generation with empty input."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        summary_input = SummaryInput()  # Empty input
        
        result = agent.generate_summary(summary_input)
        
        assert not result.is_successful
        assert result.error == "No content to summarize"
        assert len(result.summary_blocks) == 0

    def test_generate_summary_llm_error(self, mock_config, mock_neo4j_manager):
        """Test summary generation with LLM error."""
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM error")
        
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        summary_input = SummaryInput(
            claims=[{"text": "Test claim", "node_type": "claim"}]
        )

        result = agent.generate_summary(summary_input)
        
        assert not result.is_successful
        assert "LLM error" in result.error
        assert len(result.summary_blocks) == 0

    def test_create_summary_prompt(self, mock_config, mock_neo4j_manager, mock_llm):
        """Test prompt creation for LLM."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        summary_input = SummaryInput(
            claims=[{"text": "First claim", "node_type": "claim"}],
            sentences=[{"text": "Second sentence", "node_type": "sentence"}]
        )

        prompt = agent._create_summary_prompt(summary_input)
        
        # Check prompt structure
        assert "summarization agent" in prompt
        assert "bullet points" in prompt
        assert "First claim" in prompt
        assert "Second sentence" in prompt
        assert "1. First claim" in prompt
        assert "2. Second sentence" in prompt

    @patch('clarifai_shared.tier2_summary.agent.write_file_atomically')
    def test_write_summary_file_success(self, mock_write, mock_config, mock_neo4j_manager, mock_llm):
        """Test successful summary file writing."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        summary_block = SummaryBlock(
            summary_text="Test summary",
            clarifai_id="clm_test123"
        )
        
        result = SummaryResult(summary_blocks=[summary_block])
        
        success = agent.write_summary_file(result, "/test/path.md", title="Test Title")
        
        assert success is True
        mock_write.assert_called_once()
        
        # Check the arguments passed to write_file_atomically
        call_args = mock_write.call_args
        path_arg = call_args[0][0]
        content_arg = call_args[0][1]
        
        assert str(path_arg) == "/test/path.md"
        assert "# Test Title" in content_arg
        assert "clm_test123" in content_arg

    @patch('clarifai_shared.tier2_summary.agent.write_file_atomically')
    def test_write_summary_file_failed_result(self, mock_write, mock_config, mock_neo4j_manager, mock_llm):
        """Test writing summary file with failed result."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        result = SummaryResult(error="Generation failed")
        
        success = agent.write_summary_file(result, "/test/path.md")
        
        assert success is False
        mock_write.assert_not_called()

    @patch('clarifai_shared.tier2_summary.agent.write_file_atomically')
    def test_write_summary_file_write_error(self, mock_write, mock_config, mock_neo4j_manager, mock_llm):
        """Test handling of write errors."""
        mock_write.side_effect = Exception("Write error")
        
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        summary_block = SummaryBlock(
            summary_text="Test summary",
            clarifai_id="clm_test123"
        )
        result = SummaryResult(summary_blocks=[summary_block])
        
        success = agent.write_summary_file(result, "/test/path.md")
        
        assert success is False

    def test_retrieve_grouped_content_no_manager(self, mock_config, mock_llm):
        """Test content retrieval without Neo4j manager."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=None,  # No manager
            llm=mock_llm
        )

        groups = agent.retrieve_grouped_content()
        
        assert groups == []

    def test_retrieve_grouped_content_success(self, mock_config, mock_neo4j_manager, mock_llm):
        """Test successful content retrieval and grouping."""
        agent = Tier2SummaryAgent(
            config=mock_config,
            neo4j_manager=mock_neo4j_manager,
            llm=mock_llm
        )

        # Mock both claims and sentences
        mock_neo4j_manager.execute_query.side_effect = [
            [  # Claims query result
                {
                    'id': 'claim1',
                    'text': 'Test claim 1',
                    'entailed_score': 0.8,
                    'coverage_score': 0.9,
                    'decontextualization_score': 0.7,
                    'version': 1,
                    'timestamp': '2024-01-01T10:00:00Z'
                }
            ],
            [  # Sentences query result  
                {
                    'id': 'sent1',
                    'text': 'Test sentence 1',
                    'ambiguous': False,
                    'verifiable': True,
                    'version': 1,
                    'timestamp': '2024-01-01T11:00:00Z'
                }
            ]
        ]

        groups = agent.retrieve_grouped_content(min_group_size=2)
        
        assert len(groups) == 1  # Should create one group with claim + sentence
        group = groups[0]
        assert len(group.claims) == 1
        assert len(group.sentences) == 1
        assert group.group_context == "Mixed content group 1"


class TestAtomicFileWriting:
    """Test the atomic file writing functionality."""

    def test_atomic_write_integration(self):
        """Test that atomic write is used correctly."""
        # This test verifies the integration with the existing atomic write function
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_summary.md"
            
            summary_block = SummaryBlock(
                summary_text="Test summary content",
                clarifai_id="clm_integration"
            )
            result = SummaryResult(summary_blocks=[summary_block])
            
            # Create agent with minimal mocking
            with patch('clarifai_shared.tier2_summary.agent.ClarifAIConfig') as mock_config_class:
                mock_config = Mock()
                mock_config.llm.models = {"default": "gpt-3.5-turbo"}
                mock_config.llm.temperature = 0.1
                mock_config.llm.max_tokens = 1000
                mock_config_class.return_value = mock_config

                with patch('clarifai_shared.tier2_summary.agent.OpenAI') as mock_openai:
                    mock_llm = Mock()
                    mock_openai.return_value = mock_llm
                    
                    agent = Tier2SummaryAgent()
                    
                    # Write the file
                    success = agent.write_summary_file(result, test_file, title="Integration Test")
                    
                    assert success is True
                    assert test_file.exists()
                    
                    # Verify content
                    content = test_file.read_text()
                    assert "# Integration Test" in content
                    assert "Test summary content" in content
                    assert "clm_integration" in content
                    assert "<!-- clarifai:id=clm_integration ver=1 -->" in content
                    assert "^clm_integration" in content


if __name__ == "__main__":
    pytest.main([__file__])