# Mixed Content Document

This document contains various types of content and aclarai:id markers to test different scenarios.

## Regular Content

This is just regular markdown content without any special markers.

## Inline Block Content

Here's an important statement: The system should handle edge cases gracefully. <!-- aclarai:id=blk_edge_cases ver=2 -->
^blk_edge_cases

Another statement: Performance is crucial for user experience. <!-- aclarai:id=blk_performance ver=1 -->
^blk_performance

## Code Block Example

```python
def calculate_rate_limit(user_tier):
    """Calculate rate limit based on user tier."""
    limits = {
        'free': 100,
        'pro': 1000,
        'enterprise': 10000
    }
    return limits.get(user_tier, 100)
```

## List with Embedded Block

- Regular list item
- Another item
- Important architectural decision: We'll use Redis for session storage. <!-- aclarai:id=blk_redis_decision ver=1 -->
^blk_redis_decision

## Conclusion

This document demonstrates mixed content handling in the vault sync system.

<!-- aclarai:id=doc_mixed_content_example ver=1 -->