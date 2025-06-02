
### 🟢 **Implement Fallback Plugin (LLM Agent)**

**Goal:** Ensure that ClarifAI can handle any unrecognized or irregular input file by using a last-resort plugin that invokes an LLM agent to convert the content into Tier 1 Markdown format.

---

#### **Task: Implement Fallback Plugin as a Conversion Agent**

**Description:**
Create a default plugin that always accepts the input, but delegates interpretation and formatting to an LLM-powered agent. This agent analyzes unstructured input and attempts to extract one or more conversations, converting each to standard ClarifAI Tier 1 Markdown format.

**Agent Responsibilities:**

* Determine if the input contains a conversation.

  * If none, return nothing (plugin skips file).
  * If multiple conversations are found, split and return each separately.
* For each conversation:

  * Format it as Markdown with `speaker: text` utterances.
  * Provide metadata: `title`, `participants`, `message_count`, etc.
  * Include a `plugin_metadata` field noting LLM inference was used.

**Plugin Behavior:**

* Always returns `True` from `can_accept(...)`
* Calls the agent in `convert(...)`
* Wraps each result as a `MarkdownOutput`, and passes through `ensure_defaults(...)`
* Skips file if agent returns `None`

**Why this matters:**
This ensures ClarifAI can gracefully handle unstructured input, pre-formatted Markdown, or obscure chat logs without needing a format-specific plugin. It also provides robust onboarding for messy data during early experimentation.
