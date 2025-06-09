<!-- clarifai:title=Team Discussion on 2023-12-22 -->
<!-- clarifai:created_at=2023-12-22T14:30:00Z -->
<!-- clarifai:participants=["U123456", "U789012", "U345678", "U901234"] -->
<!-- clarifai:message_count=9 -->
<!-- clarifai:plugin_metadata={"source_format": "slack_json", "original_platform": "slack", "note": "realistic_slack_export_format", "has_reactions": true, "has_user_mentions": true, "user_id_mapping": {"U123456": "alice", "U789012": "bob", "U345678": "carol", "U901234": "dave"}} -->

alice: Hey team, I just reviewed the ClarifAI architecture docs. The vault synchronization design looks solid.
<!-- clarifai:id=blk_sl1a2k ver=1 -->
^blk_sl1a2k

bob: Thanks Alice! I'm particularly excited about the pluggable format conversion system. Should handle multiple input types nicely.
<!-- clarifai:id=blk_sl2b3k ver=1 -->
^blk_sl2b3k

carol: Question about the clarifai:id format - are we using UUIDs or content hashes?
<!-- clarifai:id=blk_sl3c4k ver=1 -->
^blk_sl3c4k

alice: Good question @carol. According to the docs, IDs can be UUIDs or hashes. I think deterministic hashes would be better for consistency across re-imports.
<!-- clarifai:id=blk_sl4a5k ver=1 -->
^blk_sl4a5k

bob: Makes sense. That way if we re-process the same conversation, we get the same IDs and can detect duplicates properly.
<!-- clarifai:id=blk_sl5b6k ver=1 -->
^blk_sl5b6k

carol: Perfect! And the ^anchor format will work great with Obsidian. Users can link directly to specific utterances.
<!-- clarifai:id=blk_sl6c7k ver=1 -->
^blk_sl6c7k

dave: Just catching up - are we also handling metadata like participant lists and timestamps?
<!-- clarifai:id=blk_sl7d8k ver=1 -->
^blk_sl7d8k

alice: Yes @dave! File-level metadata goes in HTML comments at the top. Things like title, created_at, participants, message_count, etc.
<!-- clarifai:id=blk_sl8a9k ver=1 -->
^blk_sl8a9k

bob: And don't forget plugin_metadata for preserving source-specific info that might be useful later.
<!-- clarifai:id=blk_sl9b0k ver=1 -->
^blk_sl9b0k

<!-- clarifai:entailed_score=0.91 -->
<!-- clarifai:coverage_score=0.84 -->
<!-- clarifai:decontextualization_score=0.87 -->