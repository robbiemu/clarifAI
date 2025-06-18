# 💡 Vault Layout and Document Type Inference

Early aclarai design inferred document types (Tier 1, 2, 3) by folder path. While convenient for structured vaults, this breaks down when:

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

Each path is **where aclarai prefers to write**, but detection is **metadata-based**.

---

### 2. Infer document types using internal markers

| Type     | Required Marker                              |
| -------- | -------------------------------------------- |
| Tier 1   | `aclarai:id=blk_*` + `^blk_*` anchors       |
| Tier 2   | `aclarai:id=clm_*` + summary references     |
| Tier 3   | `aclarai:id=concept_*` + concept header/def |
| Override | `<!-- aclarai:type=tier2 -->` (optional)    |

---

### 3. aclarai Behaviors

* Writes files into configured folders.
* Scans all `.md` files when syncing.
* Uses ID prefix (`blk_`, `clm_`, `concept_`) and optional type comments to classify files.
* Creates folders if missing — **but doesn’t require them**.

---

## Benefits

* Supports flat vaults, traditional tiered layouts, or hybrids.
* Prevents misclassification when files are moved manually.
* Matches Obsidian’s flexibility without breaking aclarai’s automation.

---

## Next Steps

* Update `design_config_panel.md`
* Adjust sync layer to rely on ID-based classification
* Optionally add `aclarai:type` in new files for clarity and robustness

---

## What Belongs in the Vault (and What Doesn't)

The aclarai vault is intended exclusively for user-facing knowledge content: Tier 1, 2, and 3 Markdown files.

System-level configuration files, such as the main `settings/aclarai.config.yaml` and LLM prompt templates, are stored separately in the `./settings` directory. This separation ensures that your vault remains a clean, portable collection of your knowledge, while system configurations can be managed and versioned independently.
