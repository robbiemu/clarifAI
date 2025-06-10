# 💡 Vault Layout and Document Type Inference

Early ClarifAI design inferred document types (Tier 1, 2, 3) by folder path. While convenient for structured vaults, this breaks down when:

- Users flatten their vault (common Obsidian practice)
- Files are moved across folders
- Team members mix types in shared directories

---

## Goals

- Allow **configurable folder layout** (but make it optional)
- Detect document type via **content markers**, not file path
- Let users **flatten, nest, or relocate** vault files freely

---

## Solution

### 1. Add `paths:` block to configuration

```yaml
paths:
  tier1: "tier1"
  summaries: "."
  concepts: "."
````

Each path is **where ClarifAI prefers to write**, but detection is **metadata-based**.

---

### 2. Infer document types using internal markers

| Type     | Required Marker                              |
| -------- | -------------------------------------------- |
| Tier 1   | `clarifai:id=blk_*` + `^blk_*` anchors       |
| Tier 2   | `clarifai:id=clm_*` + summary references     |
| Tier 3   | `clarifai:id=concept_*` + concept header/def |
| Override | `<!-- clarifai:type=tier2 -->` (optional)    |

---

### 3. ClarifAI Behaviors

* Writes files into configured folders.
* Scans all `.md` files when syncing.
* Uses ID prefix (`blk_`, `clm_`, `concept_`) and optional type comments to classify files.
* Creates folders if missing — **but doesn’t require them**.

---

## Benefits

* Supports flat vaults, traditional tiered layouts, or hybrids.
* Prevents misclassification when files are moved manually.
* Matches Obsidian’s flexibility without breaking ClarifAI’s automation.

---

## Next Steps

* Update `design_config_panel.md`
* Adjust sync layer to rely on ID-based classification
* Optionally add `clarifai:type` in new files for clarity and robustness

---

## What Belongs in the Vault (and What Doesn't)

The ClarifAI vault is intended exclusively for user-facing knowledge content: Tier 1, 2, and 3 Markdown files.

System-level configuration files, such as the main `settings/clarifai.config.yaml` and LLM prompt templates, are stored separately in the `./settings` directory. This separation ensures that your vault remains a clean, portable collection of your knowledge, while system configurations can be managed and versioned independently.
