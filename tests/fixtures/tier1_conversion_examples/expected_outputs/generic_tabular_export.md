<!-- aclarai:title=Team Discussion on 2023-12-22 -->
<!-- aclarai:created_at=2023-12-22T14:30:00Z -->
<!-- aclarai:participants=["alice", "bob", "carol", "dave"] -->
<!-- aclarai:message_count=9 -->
<!-- aclarai:plugin_metadata={"source_format": "csv", "original_platform": "generic_tabular", "note": "generic_csv_format_for_testing", "has_reactions": true, "has_threads": false} -->

alice: Hey team, I just reviewed the aclarai architecture docs. The vault synchronization design looks solid.
<!-- aclarai:id=blk_s1t2u3 ver=1 -->
^blk_s1t2u3

bob: Thanks Alice! I'm particularly excited about the pluggable format conversion system. Should handle multiple input types nicely.
<!-- aclarai:id=blk_v4w5x6 ver=1 -->
^blk_v4w5x6

carol: Question about the aclarai:id format - are we using UUIDs or content hashes?
<!-- aclarai:id=blk_y7z8a9 ver=1 -->
^blk_y7z8a9

alice: Good question @carol. According to the docs, IDs can be UUIDs or hashes. I think deterministic hashes would be better for consistency across re-imports.
<!-- aclarai:id=blk_b0c1d2 ver=1 -->
^blk_b0c1d2

bob: Makes sense. That way if we re-process the same conversation, we get the same IDs and can detect duplicates properly.
<!-- aclarai:id=blk_e3f4g5 ver=1 -->
^blk_e3f4g5

carol: Perfect! And the ^anchor format will work great with Obsidian. Users can link directly to specific utterances.
<!-- aclarai:id=blk_h6i7j8 ver=1 -->
^blk_h6i7j8

dave: Just catching up - are we also handling metadata like participant lists and timestamps?
<!-- aclarai:id=blk_k9l0m1 ver=1 -->
^blk_k9l0m1

alice: Yes @dave! File-level metadata goes in HTML comments at the top. Things like title, created_at, participants, message_count, etc.
<!-- aclarai:id=blk_n2o3p4 ver=1 -->
^blk_n2o3p4

bob: And don't forget plugin_metadata for preserving source-specific info that might be useful later.
<!-- aclarai:id=blk_q5r6s7 ver=1 -->
^blk_q5r6s7
<!-- aclarai:entailed_score=0.88 -->
<!-- aclarai:coverage_score=0.82 -->
<!-- aclarai:decontextualization_score=0.85 -->