# ✅ Create Tier 1 Markdown files with `aclarai:id` comments and Obsidian `^anchors`

## What it does:
Converts a conversation (list of utterances) into a Markdown file where each utterance is:

* A `speaker: text` block
* Followed by:

  ```markdown
  <!-- aclarai:id=blk_xyz ver=1 -->
  ^blk_xyz
  ```

This allows:

* Precise linking between Markdown and graph nodes
* File-safe sync and version tracking
* Native compatibility with Obsidian block references

### 🧠 Context

We are generating a **Tier 1 document** — this is the raw transcript layer. It represents the conversation **as spoken**, with minimal transformation.

---

#### 💬 Example Conversation Input

```json
[
  { "speaker": "Alice", "text": "Let's release v1.2 next week." },
  { "speaker": "Bob", "text": "Sounds good. Should we announce it on Friday?" },
  { "speaker": "Alice", "text": "Yes, I'll prep the release notes." }
]
```

---

#### 📝 Tier 1 Markdown Output

```markdown
Alice: Let's release v1.2 next week.
<!-- aclarai:id=blk_1a2b3c ver=1 -->
^blk_1a2b3c

Bob: Sounds good. Should we announce it on Friday?
<!-- aclarai:id=blk_4d5e6f ver=1 -->
^blk_4d5e6f

Alice: Yes, I'll prep the release notes.
<!-- aclarai:id=blk_7g8h9i ver=1 -->
^blk_7g8h9i
```

---

#### 📌 Details

* Each utterance is one **block**, identified by a unique `aclarai:id`
* `ver=1` indicates it's the first version
* Obsidian’s `^anchor` is aligned to the block ID
* These anchors enable linking from Tier 2 summaries directly back to Tier 1
* This file is written into the **Tier 1 vault directory** as something like:
  `tier1/2024-05-20_team_chat.md`


### Implementation note:
IDs are UUIDs or hashes; `ver=1` starts at first write.
