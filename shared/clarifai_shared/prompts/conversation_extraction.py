"""Prompt templates for the default plugin conversation extractor."""

CONVERSATION_EXTRACTION_PROMPT = """
You are an expert conversation analyst. Your task is to analyze unstructured text and extract conversations in a specific format.

INSTRUCTIONS:
1. Identify if the input contains one or more conversations
2. If no conversation is found, respond with "NO_CONVERSATION"
3. If conversations are found, extract them in the following JSON format:

{{
  "conversations": [
    {{
      "title": "Brief descriptive title",
      "participants": ["speaker1", "speaker2", ...],
      "messages": [
        {{"speaker": "speaker_name", "text": "message content"}},
        ...
      ],
      "metadata": {{
        "source_format": "description of original format",
        "session_id": "session identifier if available",
        "duration": "duration if available"
      }}
    }}
  ]
}}

RULES:
- Extract speaker names consistently
- Preserve message order and content
- Include all available metadata
- Use clear, descriptive titles
- If timestamps exist, preserve them in metadata

INPUT TEXT:
{input_text}"""