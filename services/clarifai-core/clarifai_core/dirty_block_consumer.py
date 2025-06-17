"""
RabbitMQ consumer for processing dirty block notifications.

This module implements the reactive sync loop that consumes dirty block messages
from vault-watcher and updates graph nodes with proper version checking.
"""

import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import pika
from pika.exceptions import AMQPConnectionError

from clarifai_shared import load_config
from clarifai_shared.graph.neo4j_manager import Neo4jGraphManager


logger = logging.getLogger(__name__)


class DirtyBlockConsumer:
    """
    Consumer for processing dirty block notifications from RabbitMQ.

    Implements the reactive sync loop as specified in sprint_4-Block_syncing_loop.md,
    including proper version checking and conflict detection.
    """

    def __init__(self, config=None):
        """Initialize the dirty block consumer."""
        self.config = config or load_config(validate=True)
        self.graph_manager = Neo4jGraphManager(self.config)

        # RabbitMQ connection parameters
        self.rabbitmq_host = self.config.rabbitmq_host
        self.rabbitmq_port = getattr(self.config, "rabbitmq_port", 5672)
        self.rabbitmq_user = getattr(self.config, "rabbitmq_user", None)
        self.rabbitmq_password = getattr(self.config, "rabbitmq_password", None)
        self.queue_name = "clarifai_dirty_blocks"

        # Vault paths from config
        self.vault_path = Path(self.config.vault_path)

        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

        logger.info(
            "DirtyBlockConsumer: Initialized consumer",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "dirty_block_consumer.__init__",
                "rabbitmq_host": self.rabbitmq_host,
                "queue_name": self.queue_name,
            },
        )

    def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            # Set up connection parameters
            if self.rabbitmq_user and self.rabbitmq_password:
                credentials = pika.PlainCredentials(
                    self.rabbitmq_user, self.rabbitmq_password
                )
                parameters = pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    port=self.rabbitmq_port,
                    credentials=credentials,
                )
            else:
                parameters = pika.ConnectionParameters(
                    host=self.rabbitmq_host, port=self.rabbitmq_port
                )

            # Establish connection
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()

            # Declare the queue (creates it if it doesn't exist)
            self._channel.queue_declare(queue=self.queue_name, durable=True)

            logger.info(
                "DirtyBlockConsumer: Connected to RabbitMQ",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer.connect",
                    "rabbitmq_host": self.rabbitmq_host,
                    "queue_name": self.queue_name,
                },
            )

        except AMQPConnectionError as e:
            logger.error(
                f"DirtyBlockConsumer: Failed to connect to RabbitMQ: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer.connect",
                    "error": str(e),
                    "rabbitmq_host": self.rabbitmq_host,
                },
            )
            raise

    def disconnect(self) -> None:
        """Close the RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            self._connection = None
            self._channel = None

            logger.info(
                "DirtyBlockConsumer: Disconnected from RabbitMQ",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer.disconnect",
                },
            )

    def start_consuming(self) -> None:
        """Start consuming messages from the dirty blocks queue."""
        if not self._is_connected():
            self.connect()

        # Set up message consumer
        self._channel.basic_qos(prefetch_count=1)  # Process one message at a time
        self._channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._on_message_received,
            auto_ack=False,  # Manual acknowledgment for reliability
        )

        logger.info(
            "DirtyBlockConsumer: Starting to consume messages",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "dirty_block_consumer.start_consuming",
                "queue_name": self.queue_name,
            },
        )

        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info(
                "DirtyBlockConsumer: Stopping consumption due to interrupt",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer.start_consuming",
                },
            )
            self._channel.stop_consuming()
            self.disconnect()

    def _on_message_received(self, channel, method, properties, body) -> None:
        """
        Process a received dirty block message.

        Args:
            channel: RabbitMQ channel
            method: Message delivery method
            properties: Message properties
            body: Message body (JSON)
        """
        try:
            # Parse message
            message = json.loads(body.decode("utf-8"))

            logger.debug(
                "DirtyBlockConsumer: Received dirty block message",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._on_message_received",
                    "clarifai_id": message.get("clarifai_id"),
                    "change_type": message.get("change_type"),
                    "file_path": message.get("file_path"),
                },
            )

            # Process the dirty block
            success = self._process_dirty_block(message)

            if success:
                # Acknowledge message
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug(
                    "DirtyBlockConsumer: Successfully processed and acknowledged message",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._on_message_received",
                        "clarifai_id": message.get("clarifai_id"),
                    },
                )
            else:
                # Reject message and requeue for retry
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.warning(
                    "DirtyBlockConsumer: Failed to process message, requeuing",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._on_message_received",
                        "clarifai_id": message.get("clarifai_id"),
                    },
                )

        except json.JSONDecodeError as e:
            logger.error(
                f"DirtyBlockConsumer: Invalid JSON in message: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._on_message_received",
                    "error": str(e),
                },
            )
            # Acknowledge bad message to remove it from queue
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(
                f"DirtyBlockConsumer: Error processing message: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._on_message_received",
                    "error": str(e),
                },
            )
            # Reject and requeue for retry
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _process_dirty_block(self, message: Dict[str, Any]) -> bool:
        """
        Process a single dirty block message.

        Args:
            message: The dirty block message from RabbitMQ

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            clarifai_id = message["clarifai_id"]
            file_path = Path(message["file_path"])
            change_type = message["change_type"]

            # Skip deleted blocks for now (could be handled in future)
            if change_type == "deleted":
                logger.info(
                    "DirtyBlockConsumer: Skipping deleted block",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._process_dirty_block",
                        "clarifai_id": clarifai_id,
                        "change_type": change_type,
                    },
                )
                return True

            # Read and parse the current block from the file
            current_block = self._read_block_from_file(file_path, clarifai_id)
            if current_block is None:
                logger.warning(
                    "DirtyBlockConsumer: Could not read block from file",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._process_dirty_block",
                        "clarifai_id": clarifai_id,
                        "file_path": str(file_path),
                    },
                )
                return False

            # Sync block with graph using proper version checking
            return self._sync_block_with_graph(current_block, file_path)

        except KeyError as e:
            logger.error(
                f"DirtyBlockConsumer: Missing required field in message: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._process_dirty_block",
                    "error": str(e),
                },
            )
            return False
        except Exception as e:
            logger.error(
                f"DirtyBlockConsumer: Error processing dirty block: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._process_dirty_block",
                    "clarifai_id": message.get("clarifai_id"),
                    "error": str(e),
                },
            )
            return False

    def _read_block_from_file(
        self, file_path: Path, clarifai_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Read and parse a specific block from a Markdown file.

        Args:
            file_path: Path to the Markdown file
            clarifai_id: The clarifai:id to look for

        Returns:
            Block dictionary with clarifai_id, version, semantic_text, and content_hash
        """
        try:
            # Make file_path absolute if relative to vault
            if not file_path.is_absolute():
                file_path = self.vault_path / file_path

            if not file_path.exists():
                logger.warning(
                    "DirtyBlockConsumer: File does not exist",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._read_block_from_file",
                        "file_path": str(file_path),
                        "clarifai_id": clarifai_id,
                    },
                )
                return None

            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract the specific block
            blocks = self._extract_clarifai_blocks(content)
            for block in blocks:
                if block["clarifai_id"] == clarifai_id:
                    return block

            logger.warning(
                "DirtyBlockConsumer: Block not found in file",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._read_block_from_file",
                    "file_path": str(file_path),
                    "clarifai_id": clarifai_id,
                },
            )
            return None

        except Exception as e:
            logger.error(
                f"DirtyBlockConsumer: Error reading block from file: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._read_block_from_file",
                    "file_path": str(file_path),
                    "clarifai_id": clarifai_id,
                    "error": str(e),
                },
            )
            return None

    def _extract_clarifai_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract all clarifai:id blocks from Markdown content.

        This method is adapted from the VaultSyncJob implementation.
        """
        blocks = []

        # Pattern to match clarifai:id comments
        pattern = r"<!--\s*clarifai:id=([a-zA-Z0-9_]+)\s+ver=(\d+)\s*-->"

        for match in re.finditer(pattern, content):
            clarifai_id = match.group(1)
            version = int(match.group(2))

            # Extract semantic text for this block
            semantic_text = self._extract_semantic_text_for_block(content, match)
            if not semantic_text:
                continue

            # Calculate hash of semantic text
            content_hash = self._calculate_content_hash(semantic_text)

            block = {
                "clarifai_id": clarifai_id,
                "version": version,
                "semantic_text": semantic_text,
                "content_hash": content_hash,
                "comment_position": match.start(),
            }

            blocks.append(block)

        return blocks

    def _extract_semantic_text_for_block(self, content: str, id_match: re.Match) -> str:
        """
        Extract the semantic text (visible content) for a clarifai:id block.

        This implements the semantic_text concept by extracting the visible text
        while excluding metadata comments.
        """
        comment_pos = id_match.start()

        # Check if this is a file-level block (comment near end of file)
        remaining_content = content[comment_pos:].strip()
        if (
            len(remaining_content) <= len(id_match.group(0)) + 10
        ):  # Small buffer for whitespace
            # File-level block - hash entire file content excluding the comment
            semantic_text = content[:comment_pos].strip()
        else:
            # Inline block - find the text before the comment
            # Look backwards to find the start of the block
            lines_before_comment = content[:comment_pos].split("\n")

            # Find the actual content line (skip empty lines)
            content_line = None
            for line in reversed(lines_before_comment):
                if line.strip():
                    content_line = line.strip()
                    break

            semantic_text = content_line or ""

        return semantic_text

    def _calculate_content_hash(self, semantic_text: str) -> str:
        """Calculate SHA-256 hash of semantic text content."""
        # Normalize whitespace and encoding for consistent hashing
        normalized_text = " ".join(semantic_text.split())
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    def _sync_block_with_graph(self, block: Dict[str, Any], file_path: Path) -> bool:
        """
        Synchronize a block with the Neo4j graph using proper version checking.

        Implements the optimistic locking strategy from sprint_4-Block_syncing_loop.md:
        - Compare vault_ver with graph_ver
        - If vault_ver == graph_ver: Clean update, increment version
        - If vault_ver > graph_ver: Proceed with update (vault is more recent)
        - If vault_ver < graph_ver: Conflict detected, skip update and log

        Args:
            block: Block dictionary with clarifai_id, version, semantic_text, content_hash
            file_path: Path to the source file

        Returns:
            True if sync was successful, False otherwise
        """
        try:
            clarifai_id = block["clarifai_id"]
            vault_version = block["version"]

            # Get existing block from graph
            existing_block = self._get_block_from_graph(clarifai_id)

            if existing_block is None:
                # New block - create in graph
                self._create_block_in_graph(block, file_path)
                logger.info(
                    "DirtyBlockConsumer: Created new block in graph",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._sync_block_with_graph",
                        "clarifai_id": clarifai_id,
                        "file": str(file_path),
                        "action": "create",
                    },
                )
                return True

            # Existing block - perform version checking
            graph_version = existing_block.get("version", 1)
            existing_hash = existing_block.get("hash", "")
            new_hash = block["content_hash"]

            # Check if content actually changed
            if existing_hash == new_hash:
                logger.debug(
                    "DirtyBlockConsumer: Block content unchanged, skipping",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._sync_block_with_graph",
                        "clarifai_id": clarifai_id,
                        "action": "unchanged",
                    },
                )
                return True

            # Implement version checking logic
            if vault_version < graph_version:
                # Conflict detected - vault is stale
                logger.warning(
                    "DirtyBlockConsumer: Version conflict detected - vault is stale",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "dirty_block_consumer._sync_block_with_graph",
                        "clarifai_id": clarifai_id,
                        "vault_version": vault_version,
                        "graph_version": graph_version,
                        "action": "skip_conflict",
                        "file": str(file_path),
                    },
                )
                return True  # Skip update but don't fail the message

            # Proceed with update (vault_ver >= graph_ver)
            self._update_block_in_graph(block, existing_block, file_path)

            logger.info(
                "DirtyBlockConsumer: Updated block in graph",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._sync_block_with_graph",
                    "clarifai_id": clarifai_id,
                    "file": str(file_path),
                    "action": "update",
                    "vault_version": vault_version,
                    "graph_version": graph_version,
                    "old_hash": existing_hash[:8],
                    "new_hash": new_hash[:8],
                },
            )
            return True

        except Exception as e:
            logger.error(
                f"DirtyBlockConsumer: Error syncing block with graph: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "dirty_block_consumer._sync_block_with_graph",
                    "clarifai_id": block.get("clarifai_id"),
                    "file": str(file_path),
                    "error": str(e),
                },
            )
            return False

    def _get_block_from_graph(self, clarifai_id: str) -> Optional[Dict[str, Any]]:
        """Get block properties from Neo4j graph by clarifai_id."""
        cypher_query = """
        MATCH (b:Block {id: $clarifai_id})
        RETURN b.id as id, b.text as text, b.hash as hash, 
               b.version as version, b.last_updated as last_updated,
               b.needs_reprocessing as needs_reprocessing
        """

        def _execute_get_block():
            with self.graph_manager.session() as session:
                result = session.run(cypher_query, clarifai_id=clarifai_id)
                record = result.single()
                return dict(record) if record else None

        return self.graph_manager._retry_with_backoff(_execute_get_block)

    def _create_block_in_graph(self, block: Dict[str, Any], file_path: Path):
        """Create a new block in the Neo4j graph."""
        current_time = datetime.utcnow().isoformat()

        cypher_query = """
        MERGE (b:Block {id: $clarifai_id})
        ON CREATE SET
            b.text = $text,
            b.hash = $hash,
            b.version = $version,
            b.last_updated = datetime($last_updated),
            b.needs_reprocessing = true,
            b.source_file = $source_file
        """

        def _execute_create_block():
            with self.graph_manager.session() as session:
                session.run(
                    cypher_query,
                    clarifai_id=block["clarifai_id"],
                    text=block["semantic_text"],
                    hash=block["content_hash"],
                    version=block["version"],
                    last_updated=current_time,
                    source_file=str(file_path),
                )

        self.graph_manager._retry_with_backoff(_execute_create_block)

    def _update_block_in_graph(
        self, block: Dict[str, Any], existing_block: Dict[str, Any], file_path: Path
    ):
        """
        Update an existing block in the Neo4j graph.

        This implements the proper version incrementing as specified:
        - Increment the graph version (ver = ver + 1)
        - Mark with needs_reprocessing: true
        """
        current_time = datetime.utcnow().isoformat()

        # Increment the graph version, not use the vault version
        current_graph_version = existing_block.get("version", 1)
        new_version = current_graph_version + 1

        cypher_query = """
        MATCH (b:Block {id: $clarifai_id})
        SET b.text = $text,
            b.hash = $hash,
            b.version = $version,
            b.last_updated = datetime($last_updated),
            b.needs_reprocessing = true,
            b.source_file = $source_file
        """

        def _execute_update_block():
            with self.graph_manager.session() as session:
                session.run(
                    cypher_query,
                    clarifai_id=block["clarifai_id"],
                    text=block["semantic_text"],
                    hash=block["content_hash"],
                    version=new_version,
                    last_updated=current_time,
                    source_file=str(file_path),
                )

        self.graph_manager._retry_with_backoff(_execute_update_block)

    def _is_connected(self) -> bool:
        """Check if the RabbitMQ connection is active."""
        return (
            self._connection is not None
            and not self._connection.is_closed
            and self._channel is not None
            and self._channel.is_open
        )
