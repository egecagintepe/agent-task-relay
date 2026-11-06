# TASK-0002: Fix JWT Token Expiration Validation Edge Case

## Objective
Fix a bug where expired JWT tokens with zero-second drift are improperly accepted when verified at the exact boundary second.

## Context
- Authentication service in `src/auth/jwt_handler.py`.
- Function `verify_access_token(token: str) -> TokenPayload`.

## Scope
- Allowed: Modify `verify_access_token` expiration timestamp assertion and add regression test.
- Non-goals: Do not alter token signing key format or token payload claims structure.

## Acceptance criteria
- [ ] Token with `exp <= current_utc_time` raises `TokenExpiredException`
- [ ] Regression test `tests/test_jwt_expiration.py` covers boundary conditions (exp - 1s, exp == now, exp + 1s)
- [ ] All auth unit tests pass cleanly

## Validation & testing
- Run `pytest tests/test_jwt_expiration.py`
