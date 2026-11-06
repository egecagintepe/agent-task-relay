# TASK-HELLO: Agent Task Relay Handshake

## Objective
Confirm that the Git-backed transport pipeline works end-to-end between the private bridge and local runner.

## Context
Initial setup handshake verification for Agent Task Relay.

## Scope
- Do not modify application source code.
- Return a brief confirmation response.

## Acceptance criteria
- [ ] Receive this task packet from `inbox/`
- [ ] Claim state persisted to `state/TASK-HELLO.json`
- [ ] Result report published to `outbox/TASK-HELLO.result.md`
- [ ] Status recorded as `completed`
