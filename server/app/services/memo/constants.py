"""
Memory System Constants

Centralized configuration for user/space identifiers used across the application.
These values must be consistent between chat_service.py, profile.py, and any other
modules that interact with the Memobase SDK.

Note: The Memobase SDK requires valid UUIDs for user_id, so we use uuid5 to generate
deterministic UUIDs from semantic namespace strings. This ensures:
1. Consistency across application restarts
2. Consistency across different environments (dev, prod)
3. Compatibility with SDK's UUID validation
"""
import uuid

# Deterministic UUID namespace for DouDouChat
DOUDOUCHAT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "doudouchat.memory")

# Default user ID - generated from semantic string for single-user mode
# Equivalent to the document requirement "default_user", but as a valid UUID
DEFAULT_USER_ID = str(uuid.uuid5(DOUDOUCHAT_NAMESPACE, "default_user"))

# Default space ID - uses the SDK's built-in root project
# The "__root__" project is auto-created by the SDK and is the only writable project
DEFAULT_SPACE_ID = "__root__"
