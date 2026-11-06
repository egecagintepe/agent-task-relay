# Test and Verification Task Packet Prompt

Use this prompt to instruct the coding agent to write unit tests, integration tests, or benchmarks for an existing module.

---

```markdown
Create an Agent Task Relay task packet focused on automated test coverage and verification:

### Target Component:
[Specify module, class, or service to test]

### Test Requirements:
1. Increase branch and edge-case test coverage for the target module.
2. Cover:
   - Happy path scenarios.
   - Fault tolerance (invalid inputs, network timeouts, error returns).
   - Boundary condition testing.
3. Test framework: [Specify pytest, unittest, jest, go test, etc.]

### Constraints:
- Filename: `inbox/TASK-test-<component>.md`
- The agent may add new test files under `tests/` but must not weaken existing assertions or delete existing tests.
- Acceptance criteria must require all tests to pass with 0 failures.

Submit to my private bridge repository or output the full Markdown block.
```
