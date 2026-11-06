# Coding Agent: Writing a Complete Result Report

Template for formatting the coding agent's final execution summary.

---

```markdown
When reporting completion of an approved task packet, format your summary using this standard structure:

### Summary of Implementation
[Describe exactly what architectural and code changes were made]

### Files Modified
- `path/to/file1.py` - Added endpoint handler
- `tests/test_file1.py` - Added test cases for happy path and error cases

### Verification & Test Results
- Command: `pytest tests/test_file1.py -v`
- Result: 4 passed, 0 failed, 0 warnings
- Test Output:
  ```text
  test_file1.py::test_endpoint_ok PASSED
  test_file1.py::test_endpoint_validation_error PASSED
  ```

### Blockers, Caveats & Review Items
- [List any assumptions made or items needing operator inspection]
- State clearly if any tools were denied or required elevated permissions.
```
