# ClarifAI: Your AI for Conversational Clarity

**ClarifAI** is an AI-powered knowledge system that transforms your scattered digital conversations (from chats, meeting transcripts, AI interactions, etc.) into a deeply interconnected and organized knowledge base directly within your Obsidian vault. It acts as an intelligent assistant that reads, understands, and links your conversational data, making it instantly accessible and actionable.

Think of it as turning your transient dialogues into a lasting, explorable library of insights, facts, and ideas, all seamlessly woven into your existing Obsidian workflow.

---

## Key Features:

### Effortless Conversation Ingestion & Standardization:
  * Easily import conversations from various sources and formats (e.g., ChatGPT JSON exports, plain text, other platform outputs via a plugin system).
  * Automatically converts diverse inputs into a consistent, clean Markdown format, ready for your vault.
  * Smartly detects and prevents the addition of duplicate conversation histories, keeping your vault tidy.

### AI-Powered Claim & Summary Generation:
  * **Automated Factual Claim Extraction:** Intelligently identifies and extracts key factual statements from lengthy conversations – claims that meet ClarifAI's claim-quality criteria (each claim is logically supported by the source, captures all important details, and stands on its own without extra context). This ensures we capture robust signal and filter out noise through automated evaluation of support, completeness, and independence.
  * **Structured Conversation Summaries (Tier 2 Documents):** Generates concise, organized summaries for each conversation, outlining the flow of dialogue and presenting the extracted claims in context. These summaries act as your go-to for understanding "what happened" and "what was stated."

### Automatic Key Concept Identification & Linking (Tier 3 Documents):
  * **Intelligent Concept Discovery:** Scans across all processed conversations to identify recurring themes, important nouns, projects, and key ideas.
  * **Dedicated Concept Pages:** Automatically creates (or updates) dedicated Markdown pages within Obsidian for each significant concept, providing a central place for that idea.
  * **Rich Interlinking:**
    * Links claims in summaries back to their exact origin in the raw conversation (Tier 2 -> Tier 1).
    * Links mentions of key concepts within conversation summaries to their dedicated concept pages (Tier 2 -> Tier 3).
    * **origin/reference links** Links concept pages back to all conversation summaries where they are discussed (Tier 3 -> Tier 2).
    * Creates links between related concept pages (Tier 3 -> Tier 3).

### Deep Obsidian Integration & Native Experience:
  * All outputs are standard Markdown files, utilizing Obsidian's `[[wikilinks]]` for all connections.
  * The system creates a logical, tiered information architecture (Raw Data -> Summaries -> Concepts) that feels native to Obsidian.
  * Leverages Obsidian's graph view and backlinking capabilities to visualize and navigate the interconnected knowledge.

### Underlying Knowledge Graph Integrity:
  * Maintains an internal knowledge graph (using Neo4j) that mirrors and powers the relationships within your Obsidian vault, explicitly modeling claims with their quality attributes through three evaluation agents (entailment, coverage, decontextualization), ensuring consistency.
  * Includes mechanisms to help synchronize this graph with the actual state of your vault files.

---

## Claim Quality Evaluation

ClarifAI's claim extraction is powered by a sophisticated three-factor evaluation system that ensures only high-quality, actionable information makes it into your knowledge base:

* **Entailment:** Verifies that each claim is logically supported by and flows from the source conversation
* **Coverage:** Ensures claims capture all important details and omit no critical elements  
* **Decontextualization:** Confirms claims can stand independently without requiring additional context

This evaluation framework (inspired by the Claimify rubric) uses graded scoring to capture nuanced quality levels rather than simple pass/fail judgments.

---

## Why Would You Want ClarifAI? (The Value Proposition)

* **Unlock Hidden Insights from Your Conversations:** Stop valuable information from being lost in endless chat logs or forgotten meetings. **ClarifAI** surfaces critically evaluated facts and ideas automatically.

* **Save Significant Time & Boost Productivity:** Drastically reduce the time spent manually reviewing, summarizing, and trying to find specific information within past conversations. Get to the point, faster.

* **Build a Powerful, Evolving Personal or Team Knowledge Graph:** Transform ephemeral discussions into a permanent, interconnected, and growing knowledge asset. Every new conversation enriches the existing network with quality-assessed information.

* **Discover Unexpected Connections & Foster Deeper Understanding:** By automatically linking related ideas and conversations, **ClarifAI** helps you see patterns, connections, and relationships you might have otherwise missed.

* **Supercharge Your Obsidian Workflow:** If you're an Obsidian user, **ClarifAI** amplifies its power by automating the creation of a highly structured and interlinked knowledge base from a typically unstructured data source. It does the heavy lifting of organizing, quality-assessing, and connecting, so you can focus on thinking and creating.

* **Improve Decision Making & Recall:** With clearly extracted, quality-rated claims and easy access to conversation context, make more informed decisions and easily recall what was discussed and agreed upon.

In essence, **ClarifAI** helps you turn the "noise" of your daily digital dialogues into a structured, searchable, and deeply insightful "signal" within the tool you already use for knowledge management – Obsidian.