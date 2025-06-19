# Current Compile Warnings

This document tracks known warnings that appear during compilation, testing, and runtime that originate from external dependencies rather than our codebase. These warnings are documented to help reviewers distinguish between issues in our code and known dependency issues that are beyond our control.

---

## Guidelines for Reviewers

When reviewing code changes:

1. **Ignore warnings listed above** - These are known dependency issues beyond our control
2. **Flag new warnings** - Any warnings not documented here should be investigated
3. **Check warning sources** - Look at the file paths to distinguish our code from dependencies
4. **Focus on our code** - Prioritize warnings coming from files in our `shared/`, `services/`, or root directories

---

## Dependency Warnings

### 1. Spacy/Weasel Click Deprecation Warning

**Warning Message:**
```
DeprecationWarning: Importing 'parser.split_arg_string' is deprecated, it will only be available in 'shell_completion' in Click 9.0.
```

**Source:** `spacy` and `weasel` packages
**Files Triggering:** 
- `/site-packages/spacy/cli/_util.py:23`
- `/site-packages/weasel/util/config.py:8`

**Impact:** Non-breaking deprecation warning for future Click 9.0 compatibility
**Action Required:** None from our side - dependency maintainers need to update their code
**Expected Resolution:** Will be resolved when spacy/weasel packages update to use the new Click API

---

### 2. Websockets Legacy API Deprecation Warning

**Warning Message:**
```
DeprecationWarning: websockets.legacy is deprecated; see https://websockets.readthedocs.io/en/stable/howto/upgrade.html for upgrade instructions
```

**Source:** Dependencies used by UI frameworks (likely Gradio)
**Files Triggering:** During `aclarai-ui` tests and runtime
**Impact:** Non-breaking deprecation warning for future websockets library compatibility
**Action Required:** Monitor for Gradio updates that address this deprecation
**Expected Resolution:** Will be resolved when UI framework dependencies update to modern websockets API

---

## Maintenance

This document should be updated when:
- New dependency warnings are discovered
- Existing warnings are resolved through dependency updates
- New versions of dependencies introduce different warnings
- Testing infrastructure changes affect warning patterns

Last updated: January 2025
