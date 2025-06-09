Okay, let's create a new architectural document detailing the Neo4j interaction methods, specifically tailored to the needs identified in the sprint tasks.

This document will live under `docs/arch/on-neo4j_interaction.md`.

---

## `docs/arch/on-neo4j_interaction.md`

# 🌐 Neo4j Interaction Strategy for ClarifAI

This document outlines the various methods ClarifAI will use to interact with the Neo4j knowledge graph. It details the choices between using the native Neo4j Python Driver for direct Cypher queries and the LlamaIndex `Neo4jGraphStore` abstraction, mapping these choices to specific tasks identified in the sprint plan.

---

## 🎯 Purpose

To define clear guidelines and technical approaches for all Neo4j operations, ensuring performance, data integrity, and alignment with ClarifAI's graph-based knowledge management.

---

## I. Overview of Interaction Methods

ClarifAI will primarily employ two main methods for interacting with Neo4j:

1.  **Neo4j Python Driver (Direct Cypher & GDS):** For fine-grained control, complex graph traversals, batch operations, and direct access to Neo4j's Graph Data Science (GDS) library. This offers maximum flexibility and performance optimization.
2.  **LlamaIndex `Neo4jGraphStore`:** A higher-level abstraction provided by LlamaIndex, ideal for simpler node and triplet (subject-predicate-object) management, aligning with LlamaIndex's data ingestion and querying patterns.

---

## II. Neo4j Python Driver (Direct Cypher & GDS)

This method provides full control over Cypher queries and access to Neo4j's advanced features like the Graph Data Science library.

### A. Core Connection & Session Management

```python
from neo4j import GraphDatabase

# Connection details (from .env)
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "password") # Or retrieve from environment variables

class Neo4jDriver:
    def __init__(self, uri, auth):
        self._driver = GraphDatabase.driver(uri, auth)
        self._driver.verify_connectivity()
        print("Neo4j driver initialized and connected.")

    def close(self):
        self._driver.close()
        print("Neo4j driver closed.")

    def query(self, cypher_query, parameters=None):
        with self._driver.session() as session:
            result = session.run(cypher_query, parameters)
            return [record for record in result]

# Example usage (in ClarifAI-Core or Scheduler)
# neo4j_conn = Neo4jDriver(URI, AUTH)
# records = neo4j_conn.query("MATCH (n:Concept) RETURN n.name LIMIT 5")
# neo4j_conn.close()
```

### B. Batch Operations (UNWIND)

For inserting or updating multiple nodes or relationships efficiently, `UNWIND` is crucial to minimize network round-trips.

```cypher
// Example: Batch creating Claims
UNWIND $claims_data AS claim_map
CREATE (c:Claim {
    id: claim_map.id,
    text: claim_map.text,
    entailed_score: claim_map.entailed_score,
    coverage_score: claim_map.coverage_score,
    decontextualization_score: claim_map.decontextualization_score,
    version: 1, // Initial version
    timestamp: datetime()
})
```

`$claims_data` would be a list of dictionaries passed as parameters: `[{'id': 'clm_1', 'text': '...', ...}, {'id': 'clm_2', 'text': '...', ...}]`.

### C. Graph Data Science (GDS) Library Integration

GDS algorithms like PageRank are executed via direct GDS calls within Cypher, using the `gds` prefix. Results can be written back to the graph.

```python
# Example: Running PageRank and writing results back to Concept nodes
# (from sprint_9-Implement_top_concepts_job.md)
cypher_query_pagerank = """
CALL gds.pageRank.write('concept_graph', {
    writeProperty: 'pagerank_score',
    maxIterations: 20,
    dampingFactor: 0.85
})
YIELD nodePropertiesWritten, ranIterations;
"""

# To run GDS, you first need to project a graph into GDS memory
# For PageRank on Concepts, this could involve all (:Concept) nodes and relevant relationships
cypher_project_graph = """
CALL gds.graph.project(
    'concept_graph',
    'Concept',
    {
        SUPPORTS_CONCEPT: {orientation: 'REVERSE'},
        MENTIONS_CONCEPT: {orientation: 'REVERSE'},
        RELATED_TO: {orientation: 'UNDIRECTED'}
    }
);
"""

# After running PageRank, you might query for top N concepts
cypher_query_top_concepts = """
MATCH (c:Concept)
RETURN c.name, c.pagerank_score
ORDER BY c.pagerank_score DESC
LIMIT $limit;
"""
```

**Note:** GDS algorithms run in a separate process space within Neo4j and are highly optimized for graph computation. ClarifAI will manage graph projection, algorithm execution, and result retrieval.

---

## III. LlamaIndex `Neo4jGraphStore`

LlamaIndex provides a convenient abstraction for managing knowledge graphs, especially for triplet-based ingestion and retrieval.

### A. Core Initialization

```python
from llama_index.graph_stores import Neo4jGraphStore
from llama_index import KnowledgeGraphIndex, ServiceContext
from llama_index.llms import OpenAI # Example LLM

# Configuration (from .env or ./settings/clarifai.config.yaml)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"

# Initialize Graph Store
graph_store = Neo4jGraphStore(
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    url=NEO4J_URI,
    database="neo4j" # Default database
)

# Optional: ServiceContext if integrating with other LlamaIndex components
# service_context = ServiceContext.from_defaults(llm=OpenAI())
# index = KnowledgeGraphIndex.from_documents(..., graph_store=graph_store, service_context=service_context)
```

### B. Adding Data (Triplets)

The `Neo4jGraphStore` primarily works with subject-predicate-object triplets.

```python
# Example: Adding a Claim and its relationship to a Block
# This maps to (:Subject)-[:PREDICATE]->(:Object)
triplets_to_add = [
    ("claim_id_xyz", "text_property", "This is the claim text."),
    ("claim_id_xyz", "originates_from", "block_id_abc"),
    # For properties on the relationship itself, direct Cypher is usually more explicit.
    # LlamaIndex's triplet model might not directly support this granularity easily.
]
graph_store.add_triplets(triplets_to_add)

# Note: For complex node properties (like entailed_score, coverage_score)
# or specific relationship properties (like strength on SUPPORTS_CONCEPT),
# direct Cypher with the Neo4j Python Driver might be more suitable.
```

---

## IV. Application to ClarifAI Tasks

### 1. `sprint_3-Create_nodes_in_neo4j.md` (Criar nós (:Claim) e (:Sentence))

*   **Preferred Method:** **Neo4j Python Driver (Direct Cypher)**.
    *   **Reasoning:** This task requires creating nodes (`:Claim`, `:Sentence`) with multiple specific properties (`id`, `text`, `entailed_score`, `coverage_score`, `decontextualization_score`, `version`, `timestamp`) and a well-defined relationship (`:ORIGINATES_FROM`) to a `(:Block)` node.
    *   While `LlamaIndex`'s `add_triplets` can create nodes and simple relationships, managing precise property types and setting multiple properties on both nodes and relationships (especially `version` and nullable scores) is more explicitly and efficiently handled with direct Cypher queries and `UNWIND` for batching.
    *   **Example Cypher (Python Driver):**
        ```python
        # Batch create Claims and their ORIGINATES_FROM relationships
        cypher_batch_create_claims = """
        UNWIND $claims_data AS data
        MERGE (c:Claim {id: data.id})
        ON CREATE SET
            c.text = data.text,
            c.entailed_score = data.entailed_score,
            c.coverage_score = data.coverage_score,
            c.decontextualization_score = data.decontextualization_score,
            c.version = 1,
            c.timestamp = datetime()
        MERGE (b:Block {id: data.block_id}) // Assuming Block nodes already exist
        MERGE (c)-[:ORIGINATES_FROM]->(b);
        """
        # Similar logic for Sentence nodes.
        ```

### 2. `sprint_5-Link_claims_to_concepts.md` (Vincular claims a conceitos)

*   **Preferred Method:** **Neo4j Python Driver (Direct Cypher)**.
    *   **Reasoning:** This task is critical for establishing rich semantic links (`SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`, `CONTRADICTS_CONCEPT`) with *specific properties on the relationship itself* (`strength`, `entailed_score`, `coverage_score`). LlamaIndex's triplet model (`(subject, predicate, object)`) typically doesn't natively support complex properties on the `predicate` (relationship type) easily. Direct Cypher allows precise definition and update of these edge properties.
    *   **Example Cypher (Python Driver):**
        ```python
        # Batch create/update relationships between claims and concepts
        cypher_batch_link_claims_concepts = """
        UNWIND $links_data AS link
        MATCH (c:Claim {id: link.claim_id})
        MATCH (k:Concept {name: link.concept_name}) // Assuming Concept names are unique identifiers
        MERGE (c)-[r]->(k)
        ON CREATE SET
            r.type = link.relation_type, // Storing relation type as a property if needed, or use dynamic relation MERGE (c)-[r_type:link.relation_type]->(k)
            r.strength = link.strength,
            r.entailed_score = link.entailed_score,
            r.coverage_score = link.coverage_score
        ON MATCH SET // Update existing relationship properties
            r.strength = link.strength,
            r.entailed_score = link.entailed_score,
            r.coverage_score = link.coverage_score;
        """
        # Dynamic relationship type (e.g., :SUPPORTS_CONCEPT) would be part of MERGE
        # MERGE (c)-[r_type:link.relation_type {strength: link.strength, ...}]->(k)
        # This requires careful handling of relation_type in Cypher.
        ```

### 3. `sprint_9-Implement_top_concepts_job.md` (Implementar Job de Top Concepts)

*   **Preferred Method:** **Neo4j Python Driver (Direct Cypher with GDS)**.
    *   **Reasoning:** This task explicitly requires running Neo4j's native PageRank algorithm, which is part of the GDS library. LlamaIndex does not directly expose or abstract GDS calls. The process involves projecting the graph into GDS memory, running the algorithm, and writing the results back to the graph, all best done via the native driver.
    *   **Example Cypher (Python Driver - see Section II.C for snippets):**
        *   `gds.graph.project` to define the graph for GDS.
        *   `gds.pageRank.write` to execute PageRank and store `pagerank_score` on `(:Concept)` nodes.
        *   Standard Cypher queries to retrieve `(:Concept)` nodes ordered by `pagerank_score`.

### 4. General Vault Sync & Updates (e.g., `sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`, `sprint_4-Block_syncing_loop.md`)

*   **Preferred Method:** **Neo4j Python Driver (Direct Cypher)**.
    *   **Reasoning:** These tasks involve reading specific node properties (e.g., `hash`, `ver=`) to detect drift and then updating these properties (`text`, `hash`, `ver=`, `needs_reprocessing: true`). These are highly specific property updates that are most directly and efficiently handled by targeted Cypher `MATCH` and `SET` clauses, often batched with `UNWIND` for performance.
    *   **Example Cypher (Python Driver):**
        ```python
        # Update node properties for a changed block
        cypher_update_block_props = """
        MATCH (n {id: $block_id}) // Match by ID (assumed unique across node labels for simplicity here)
        SET
            n.text = $new_text,
            n.hash = $new_hash,
            n.version = n.version + 1, // Increment version
            n.needs_reprocessing = TRUE,
            n.last_synced = datetime();
        """
        ```

---

## V. Considerations & Best Practices

*   **Consistency:** While different methods are used, ensure that the schema (node labels, relationship types, property names) remains consistent across all interactions, as defined in `docs/project/technical_overview.md`.
*   **Transactions:** Always wrap database operations within explicit transactions (or implicitly via `session.run()` which uses auto-commit by default but can be controlled) to ensure atomicity and data integrity, especially for multi-step operations.
*   **Batching:** For any operation involving multiple nodes or relationships (creation, update, deletion), use `UNWIND` with the Neo4j Python Driver to send data in batches. This significantly reduces network overhead and improves performance.
*   **Indexing:** Ensure appropriate indexes are created on frequently queried properties (e.g., `id`, `name`, `timestamp`) for optimal read performance.
*   **Error Handling:** Implement robust `try-except` blocks around database interactions, with retries (e.g., exponential backoff) for transient network or database errors.
*   **Logging:** Log all critical database operations (e.g., start/end of large batch jobs, successful/failed updates, GDS algorithm runs) for observability and debugging.
*   **LlamaIndex `KnowledgeGraphIndex` Role:** The `KnowledgeGraphIndex` will primarily be used for higher-level RAG workflows, where LlamaIndex's ability to abstract complex querying and data retrieval for LLM context generation is beneficial. It sits *on top* of the graph store, using the mechanisms defined here to persist its underlying graph data.
