## 🧩 Skeleton for the Pluggable Format Conversion System

### 🔁 Main Execution Flow

```python
def convert_file_to_markdowns(input_path: Path, registry: list[Plugin]) -> list[MarkdownOutput]:
    raw_input = input_path.read_text(encoding="utf-8")

    for plugin in registry:
        if plugin.can_accept(raw_input):
            try:
                raw_outputs = plugin.convert(raw_input, input_path)
                return [ensure_defaults(md, input_path) for md in raw_outputs]
            except Exception:
                continue

    raise UnknownFormatError(f"No plugin could handle file: {input_path}")
```

---

### 📦 `MarkdownOutput` Structure

```python
@dataclass
class MarkdownOutput:
    title: str                 # Will be overwritten if missing
    markdown_text: str        # Full Markdown content to write
    metadata: dict            # Optional fields described below
```

---

### 🧾 Expected Metadata Fields (plugin-provided, all optional)

| Key             | Type        | Default if missing                       |
|-----------------|-------------|------------------------------------------|
| `title`         | str         | "Conversation last modified at {created_at}" |
| `created_at`    | str (ISO)   | File mtime                              |
| `participants`  | list[str]   | ["user", "assistant"]                   |
| `message_count` | int         | 0                                       |
| `duration_sec`  | int         | None                                    |
| `plugin_metadata` | dict     | {}                                      |

---

### 🔧 `ensure_defaults(...)`

```python
def ensure_defaults(md: MarkdownOutput, path: Path) -> MarkdownOutput:
    meta = md.metadata or {}
    created = meta.get("created_at") or datetime.fromtimestamp(path.stat().st_mtime).isoformat()
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
```

---

### 🧩 Plugin Interface

```python
class Plugin(ABC):
    @abstractmethod
    def can_accept(self, raw_input: str) -> bool:
        ...

    @abstractmethod
    def convert(self, raw_input: str, path: Path) -> list[MarkdownOutput]:
        ...
```

This structure ensures:
- Plugins remain focused on detection and conversion only
- The system fills all required defaults for consistent downstream processing
- Future non-file sources (e.g. clipboard, uploads) can be supported without change
