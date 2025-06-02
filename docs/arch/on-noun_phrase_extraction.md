## 🔍 What tool does **Claimify** use for noun phrase extraction?

Claimify uses **spaCy** — specifically, it leverages:

* `en_core_web_sm` or `en_core_web_trf` models
* `noun_chunks` (noun phrase iterator)
* Optionally custom rule-based matchers (e.g., for terminology normalization)

Claimify’s approach is fast, reliable, and good at inline noun phrase extraction without requiring fine-tuning.

---

## 🧪 Comparison with Other Python NLP Tools

### 🥇 **spaCy** (Claimify’s choice)

* ✅ Excellent speed and tokenization quality
* ✅ Built-in noun phrase chunker (`doc.noun_chunks`)
* ✅ Easy model deployment (even transformer-backed)
* ✅ Good support for entity linking / dependency parsing
* ❌ Slightly heavier install

---

### 🟡 **NLTK**

* ✅ Lightweight and simple
* ✅ Easy to prototype (uses regex NP grammars)
* ❌ Outdated parsing defaults (no pretrained parser)
* ❌ Less accurate chunking; requires manual POS tagging pipeline

```python
# NLTK noun phrase example (manual)
from nltk import pos_tag, word_tokenize, RegexpParser

text = "The large international consortium of researchers"
tokens = pos_tag(word_tokenize(text))
parser = RegexpParser("NP: {<DT>?<JJ>*<NN.*>+}")
result = parser.parse(tokens)
```

* Works — but brittle, no context-awareness

---

### 🟠 **Stanza** (Stanford NLP)

* ✅ High-quality models
* ✅ Good multilingual support
* ❌ Slower than spaCy
* ❌ Less commonly used in production for fast phrase extraction

---

### 🟣 **Transformers-only (e.g. BERT + attention)**

* ✅ Theoretical best performance (e.g. noun phrase masking via attention peaks)
* ❌ Requires complex logic and training
* ❌ No off-the-shelf noun chunker

---

Note: Multilingual support for claim processing is not necessary since claims are rewritten from raw sentence input by an agentic process.
