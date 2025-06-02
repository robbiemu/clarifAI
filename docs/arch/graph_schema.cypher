// conceptual
// Node: Claim
CREATE CONSTRAINT ON (c:Claim) ASSERT c.claim_id IS UNIQUE;
// Properties for Claim:
// claim_id: String (Unique ID)
// text: String (Claim text)
// verifiable: Boolean
// entailed_score: Float
// self_contained: Boolean
// context_complete: Boolean

// Node: Sentence (for ambiguous/lower-quality statements)
// Properties for Sentence:
// text: String
// ambiguous: Boolean
// verifiable: Boolean (etc., for any relevant flags that failed)
// sentence_id: String (Unique ID)

// Node: Block (Markdown segment in Tier 1)
// Properties for Block:
// block_id: String (Unique ID, e.g., ^blockIdxyz)
// content_hash: String
// source_file: String

// Node: Summary (Tier 2 document)
// Properties for Summary:
// file_path: String
// title: String

// Node: Concept (Tier 3 document/entity)
// Properties for Concept:
// file_path: String
// name: String (Concept name)
// definition: String

// Relationship Types (examples, not exhaustive list for CREATE statements)
// ORIGINATES_FROM: (:Claim)-[:ORIGINATES_FROM]->(:Block)
// ORIGINATES_FROM: (:Sentence)-[:ORIGINATES_FROM]->(:Block)
// SUMMARIZED_IN: (:Claim)-[:SUMMARIZED_IN]->(:Summary)
// SUPPORTS_CONCEPT: (:Claim)-[:SUPPORTS_CONCEPT {strength: Float, entailed_score: Float, coverage_score: Float}]->(:Concept)
// CONTRADICTS_CONCEPT: (:Claim)-[:CONTRADICTS_CONCEPT {strength: Float, entailed_score: Float, coverage_score: Float}]->(:Concept)
// MENTIONS_CONCEPT: (:Claim)-[:MENTIONS_CONCEPT]->(:Concept)
// ENTAILS_CLAIM: (:Claim)-[:ENTAILS_CLAIM]->(:Claim)
// REFINES_CLAIM: (:Claim)-[:REFINES_CLAIM]->(:Claim)
// AMBIGUOUS_WITH: (:Sentence)-[:AMBIGUOUS_WITH]->(:Sentence)
// RELATED_TO: (:Concept)-[:RELATED_TO]->(:Concept)

// Indexes for performance (examples)
CREATE INDEX ON :Claim(verifiable);
CREATE INDEX ON :Claim(entailed_score);
CREATE INDEX ON :Concept(name);