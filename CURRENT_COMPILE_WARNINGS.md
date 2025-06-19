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

### 3. Coverage Module Import Warning

**Warning Message:**
```
CoverageWarning: Module services was never imported.
```

**Source:** `pytest-cov` coverage tool configuration
**Files Triggering:** During CI test execution
**Explanation:** 
- The CI workflow runs tests from the repository root using pytest
- The coverage tool is configured to look for a top-level `services` package
- However, tests are run against individual service modules within the services/ directory
- The top-level `services` directory itself is never directly imported as a Python package
- This is expected behavior for our monorepo structure where services are independent modules

**Impact:** Cosmetic warning only - does not affect functionality or coverage accuracy
**Action Required:** None - this is expected behavior given our monorepo testing approach
**Alternative:** Could be silenced by configuring `pytest-cov` to ignore this specific warning in `pyproject.toml`

---

### 4. Network Connectivity Warnings (Testing Environment)

**Warning Message:**
```
OSError: We couldn't connect to 'https://huggingface.co' to load the files, and couldn't find them in the cached files.
```

**Source:** `transformers`/`sentence-transformers` packages attempting to download models
**Files Triggering:** Embedding and model tests that require external model downloads
**Context:** Limited internet access in CI/testing environments
**Impact:** Some tests fail when they cannot download required ML models
**Action Required:** 
- Consider pre-caching models in CI environment
- Or mock model loading in tests that don't specifically test model functionality
- Document that certain tests require internet connectivity for model downloads

---

## Maintenance

This document should be updated when:
- New dependency warnings are discovered
- Existing warnings are resolved through dependency updates
- New versions of dependencies introduce different warnings
- Testing infrastructure changes affect warning patterns

Last updated: January 2025
