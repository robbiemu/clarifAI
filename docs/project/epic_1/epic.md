# Selected User Stories for ClarifAI

Here is a selection of the necessary user stories, ensuring alignment with your defined product goals and technical specification

---

## User Stories

### Value Proposition / Broader Benefits

* As someone overwhelmed by digital communication, I want ClarifAI to help me quickly find information discussed previously, saving time and frustration.
* As a decision-maker, I want to easily recall past discussions and extracted facts, to make informed choices.
* As a knowledge worker, I want to transform transient conversations into a permanent asset, continually building on accumulated insights.

### Conversation Ingestion & Standardization

* As a user, I want to easily import my ChatGPT conversation history (JSON export) into ClarifAI, so that I can start organizing my AI interactions.

  * [Implement default plugin for pluggable format conversion system](sprint_plan.md#sprint-2-ingestion-and-block-generation-1-week)
  * [Build Gradio Import Panel](sprint_plan.md#sprint-7-import-ux--evaluation-display)
* As a user, I want ClarifAI to automatically convert imported conversations into standard Markdown, so that they integrate seamlessly with my Obsidian vault.

  * [Create Tier 1 Markdown files during import](sprint_plan.md#sprint-2-ingestion-and-block-generation-1-week)
* As a user, I want ClarifAI to detect and skip duplicate conversation imports, so that my vault remains clean.

  * [Create Tier 1 Markdown files during import](sprint_plan.md#sprint-2-ingestion-and-block-generation-1-week)

### AI-Powered Claim & Summary Generation

* As a knowledge worker, I want ClarifAI to automatically extract key factual claims from my long conversations, so that I can quickly identify important information.

  * [Implement core Claimify pipeline components](sprint_plan.md#sprint-3-claimify-mvp-2-weeks)
  * [Create (\:Claim) and (\:Sentence) nodes in Neo4j](sprint_plan.md#sprint-3-claimify-mvp-2-weeks)
* As a project manager, I want ClarifAI to generate concise summaries of each conversation, so that I can grasp main points without re-reading.

  * [Create the agent and integration to generate Tier 2 summaries with links back to Tier 1](sprint_plan.md#sprint-3-claimify-mvp-2-weeks)
* As a researcher, I want to easily navigate from a summarized claim back to its exact origin in the raw conversation, so that I can verify context or explore details.

  * [Create the agent and integration to generate Tier 2 summaries with links back to Tier 1](sprint_plan.md#sprint-3-claimify-mvp-2-weeks)
* As a fact-checker, I need to be able to define trust levels for extracted claims with Claimify (based on quality flags: verifiable, entailed\_score, self\_contained, context\_complete).

  * [UI or config file for model roles, similarity thresholds, and context windows](sprint_plan.md#sprint-5-config-panel--automation-control)
  * [Apply evaluation thresholds to linking and filtering](sprint_plan.md#sprint-6-evaluation-agents--filtering)

### Automatic Key Concept Identification & Linking

* As a knowledge manager, I want ClarifAI to automatically identify important concepts across conversations, so that I can centralize related information.

  * [Create noun phrase extractor on claims + summaries](sprint_plan.md#sprint-4-concept-linking-and-tier-3-generation)
* As an Obsidian user, I want ClarifAI to create dedicated Markdown pages for each identified concept, so that I have central hubs for related information.

  * [Create/update Tier 3 Markdown files (`[[Concept]]`) and (\:Concept) nodes](sprint_plan.md#sprint-4-concept-linking-and-tier-3-generation)
* As a note-taker, I want links to concept pages automatically created within summaries, so I can easily jump between discussions and overarching themes.

  * [Link claims to concepts with SUPPORTS\_CONCEPT, MENTIONS\_CONCEPT, etc.](sprint_plan.md#sprint-4-concept-linking-and-tier-3-generation)
* As someone building a knowledge graph, I want ClarifAI to suggest or create links between related concept pages, so I can discover unexpected connections.

  * [Use hnswlib for embedding-based concept detection](sprint_plan.md#sprint-5-config-panel--automation-control)

### Automatic Synthesis

#### ✅ **Top Concept Page**
* **As a knowledge worker**, I want a periodically updated summary of the "Top Concepts", so I can quickly see high-level insights and focus areas without navigating through individual concept pages.

* **As an Obsidian user**, I want ClarifAI to automatically maintain a "Top Concepts" page that aggregates and organizes significant knowledge clusters, ensuring efficient navigation within my vault.

* **As a decision-maker**, I want the "Top Concepts" page to reflect our knowledge evolution, helping me stay informed about critical developments or shifts in focus.

### ✅ **Subject Pages**

* **As a knowledge manager**, I want ClarifAI to automatically detect and create thematic clusters of related concepts, making it easier to explore comprehensive, interconnected knowledge areas.

* **As a researcher**, I want clearly defined subject pages aggregating relevant concept pages and content, enabling efficient deep-dives into specific thematic areas such as “Python Errors” or “GPU Configuration.”

* **As an Obsidian power user**, I want subject pages to dynamically reflect changes in related concepts, automatically maintaining accurate and updated knowledge structures without manual intervention.

### ✅ **Trending Topics / Concepts**

* **As a project manager**, I want ClarifAI to automatically highlight currently trending topics and concepts, enabling me to quickly identify and address emerging areas of interest or concern.

* **As an Obsidian user**, I want a regularly updated "Trending Topics" page, so I can easily track and explore content that is gaining increased attention or relevance.

* **As someone monitoring knowledge trends**, I want periodic snapshots (weekly or monthly) of trending topics, allowing analysis of evolving interests and historical trend patterns for strategic insights.


### Deep Obsidian Integration & Native Experience

* As an Obsidian user, I want all of ClarifAI's output to be standard Markdown files with wikilinks, so it feels like a native extension of my workflow.

  * [Create/update Tier 3 Markdown files (`[[Concept]]`) and (\:Concept) nodes](sprint_plan.md#sprint-4-concept-linking-and-tier-3-generation)
* As a user, I want the file and folder structure created by ClarifAI to be logical and intuitive, so I can easily find content within my vault.

  * [Create Tier 1 Markdown files during import](sprint_plan.md#sprint-2-ingestion-and-block-generation-1-week)
  * [Build Gradio Import Panel](sprint_plan.md#sprint-7-import-ux--evaluation-display)
  * [UI or config file for model roles, similarity thresholds, and context windows](sprint_plan.md#sprint-5-config-panel--automation-control)
* As an Obsidian power user, I want to modify files generated by ClarifAI and have the system accommodate changes without breaking connections.

  * [Vault file watcher with dirty block detection](sprint_plan.md#sprint-1-foundational-infrastructure-1-week)
  * [Block ID hashing + sync loop: update graph nodes if content changes](sprint_plan.md#sprint-1-foundational-infrastructure-1-week)
  * [Bootstrap scheduler container + vault sync job](sprint_plan.md#sprint-3-claimify-mvp-2-weeks)

### Underlying Knowledge Graph Integrity

* As a developer/advanced user, I want ClarifAI to maintain an internal knowledge graph that mirrors my Obsidian vault, ensuring consistency and robust linking.

  * [Vault file watcher with dirty block detection](sprint_plan.md#sprint-1-foundational-infrastructure-1-week)
  * [Block ID hashing + sync loop: update graph nodes if content changes](sprint_plan.md#sprint-1-foundational-infrastructure-1-week)
  * [Create (\:Claim) and (\:Sentence) nodes in Neo4j](sprint_plan.md#sprint-3-claimify-mvp-2-weeks)
  * [Create/update Tier 3 Markdown files (`[[Concept]]`) and (\:Concept) nodes](sprint_plan.md#sprint-4-concept-linking-and-tier-3-generation)
* As a user who edits files manually, I want ClarifAI to re-synchronize its internal graph with the Obsidian vault, so my knowledge base remains accurate.

  * [Bootstrap scheduler container + vault sync job](sprint_plan.md#sprint-3-claimify-mvp-2-weeks)
