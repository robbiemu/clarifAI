"""
Utility functions for the plugin system.
"""

from datetime import datetime
from pathlib import Path
from typing import List

from ..plugin_interface import Plugin, MarkdownOutput, UnknownFormatError


def ensure_defaults(md: MarkdownOutput, path: Path) -> MarkdownOutput:
    """
    Fill in any missing default metadata fields in a MarkdownOutput.
    
    This function ensures all required metadata fields are present
    with sensible defaults, as specified in docs/arch/on-pluggable_formats.md
    
    Args:
        md: The MarkdownOutput to process
        path: Path to the original file (for fallback metadata)
        
    Returns:
        A new MarkdownOutput with all required metadata fields filled
    """
    meta = md.metadata or {}
    created = meta.get("created_at") or datetime.fromtimestamp(path.stat().st_mtime).isoformat()
    
    # Only generate title if the original title is empty or None
    title = md.title
    if not title:
        title = meta.get("title") or f"Conversation last modified at {created}"

    return MarkdownOutput(
        title=title,
        markdown_text=md.markdown_text,
        metadata={
            "created_at": created,
            "participants": meta.get("participants", ["user", "assistant"]),
            "message_count": meta.get("message_count", 0),
            "duration_sec": meta.get("duration_sec"),
            "plugin_metadata": meta.get("plugin_metadata", {})
        }
    )


def convert_file_to_markdowns(input_path: Path, registry: List[Plugin]) -> List[MarkdownOutput]:
    """
    Main conversion function that tries plugins in order until one succeeds.
    
    This function implements the main execution flow as defined in
    docs/arch/on-pluggable_formats.md
    
    Args:
        input_path: Path to the input file
        registry: List of Plugin instances to try in order
        
    Returns:
        List of MarkdownOutput objects with defaults applied
        
    Raises:
        UnknownFormatError: If no plugin can handle the file
    """
    raw_input = input_path.read_text(encoding="utf-8")

    for plugin in registry:
        if plugin.can_accept(raw_input):
            try:
                raw_outputs = plugin.convert(raw_input, input_path)
                return [ensure_defaults(md, input_path) for md in raw_outputs]
            except Exception:
                continue

    raise UnknownFormatError(f"No plugin could handle file: {input_path}")