"""Secret redaction and output sanitization for reports."""
from __future__ import annotations

import re

MAX_RESPONSE_CHARS = 16_000

# Defense-in-depth patterns for credentials and tokens
REDACTION_PATTERNS = [
    # GitHub tokens
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{18,}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    # Anthropic API keys (must precede generic sk- pattern)
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}", re.IGNORECASE), "[REDACTED_ANTHROPIC_KEY]"),
    # OpenAI & generic API keys
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    # Google API Keys
    (re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE), "[REDACTED_GOOGLE_KEY]"),
    # AWS access key ID
    (re.compile(r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])"), None),  # handled selectively in key-value regex
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    # Slack tokens
    (re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}", re.IGNORECASE), "[REDACTED_SLACK_TOKEN]"),
    # Private keys
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    # Bearer tokens
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{15,}"), "Bearer [REDACTED_TOKEN]"),
    # Generic key-value secret assignments
    (
        re.compile(r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key|password|client[_-]?secret)\s*[:=]\s*['\"]?[^\s'\"]+['\"]?"),
        r"\1=[REDACTED]"
    ),
]


def redact_secrets(text: str, max_chars: int = MAX_RESPONSE_CHARS) -> str:
    """Sanitize and redact secrets from output text before publishing.
    
    Note: Redaction is defense-in-depth and cannot guarantee 100% detection of
    arbitrary bespoke secret formats. Sensitive files should never be read by runners.
    """
    if not text:
        return ""

    sanitized = text
    for pattern, replacement in REDACTION_PATTERNS:
        if replacement is not None:
            sanitized = pattern.sub(replacement, sanitized)

    if len(sanitized) > max_chars:
        sanitized = (
            sanitized[:max_chars]
            + f"\n\n... [Output truncated: exceeded {max_chars} characters. Check local logs for full output.]"
        )

    return sanitized


def sanitize_markdown_fences(text: str) -> str:
    """Escape triple backticks within text to prevent breaking Markdown reports."""
    return text.replace("```", "'''")
