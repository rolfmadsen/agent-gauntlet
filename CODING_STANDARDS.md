# Coding Standards: Python

This repository follows the **Google Python Style Guide** and **PEP 8 / PEP 484** type conventions, tailored for high-assurance, testable, and AI-navigable architectures.

---

## 1. Type Annotations & Static Analysis
- **Strict Typing:** All function and method signatures MUST have explicit argument and return type annotations.
- **Modern Syntax:** Use Python 3.10+ native type syntax (`list[str]`, `dict[str, Any]`, `X | None` instead of `Optional[X]`, `Union[X, Y]`).
- **No Untyped Any:** Avoid bare `Any` in public signatures; use concrete types, type variables, or `object` with runtime type guards.

## 2. Immutability & Data Modeling
- **Value Objects:** Prefer `@dataclass(frozen=True)` or Pydantic `BaseModel(frozen=True)` for domain models and data transfer objects (DTOs).
- **Pure Functions:** Prefer stateless, side-effect-free pure functions where practical. Avoid mutable global or module-level state.
- **Default Arguments:** Never use mutable default arguments (`def foo(items=[])` is strictly forbidden; use `def foo(items: list[str] | None = None)`).

## 3. Architecture & Package Structure
- **Package-by-Feature (Screaming Architecture):** Colocate related business logic, models, services, and repositories within cohesive feature directories (`features/<feature_name>/`).
- **Dependency Inversion:** High-level policy modules must not depend directly on low-level detail/I/O modules; depend on abstractions/protocols (`typing.Protocol`).
- **No Circular Imports:** Architecture must be strictly acyclic.

## 4. Error Handling & Exceptions
- **Domain Exceptions:** Define explicit, domain-specific exception hierarchies deriving from a base project exception (`class DomainError(Exception): pass`).
- **No Bare Excepts:** Catching bare `except:` or broad `except Exception:` without re-raising or structured logging is strictly forbidden.
- **Fail-Closed:** In security or verification boundaries, unexpected states must fail closed (deny/abort) rather than swallow errors.

## 5. Documentation & Google Docstrings
- **AI-Native Documentation:** Document *Why* (invariants, architectural boundaries, edge cases) rather than restating *What* the code does. Avoid noisy line-by-line comments.
- **Module Docstrings:** Every Python module MUST start with a top-level docstring summarizing its responsibility and boundary invariants.
- **Google Docstrings Standard:** All public functions, classes, and methods MUST use structured Google-style docstrings with explicit `Args:`, `Returns:`, and `Raises:` sections.

## 6. Concrete DO / DON'T Examples

### ❌ DON'T (Anti-pattern: Untyped, mutable defaults, swallowed exceptions, noisy comments)
```python
# bad_module.py
# loop over users and get data
def get_user_data(user_id, cache={}):  # ❌ Mutable default argument
    # check if user is in cache
    try:
        return cache[user_id]
    except:  # ❌ Bare except masks bugs
        return None
```

### ✅ DO (Idiomatic: Strict types, frozen dataclass, Google docstrings, domain exceptions)
```python
"""User data access and cache management feature."""

from collections.abc import Mapping
from dataclasses import dataclass


class UserNotFoundError(Exception):
    """Raised when the requested user profile cannot be located."""


@dataclass(frozen=True)
class UserProfile:
    """Immutable domain representation of a user profile."""

    user_id: str
    email: str
    is_active: bool = True


def get_user_data(
    user_id: str,
    cache: Mapping[str, UserProfile] | None = None,
) -> UserProfile:
    """Retrieves user profile data from cache or repository.

    Args:
        user_id: Unique string identifier for the user.
        cache: Optional pre-warmed cache map. Defaults to None.

    Returns:
        The resolved immutable UserProfile.

    Raises:
        ValueError: If user_id is empty or malformed.
        UserNotFoundError: If the user profile does not exist.
    """
    if not user_id.strip():
        raise ValueError("user_id cannot be empty")

    local_cache = cache or {}
    if user_id not in local_cache:
        raise UserNotFoundError(f"User '{user_id}' not found in cache")

    return local_cache[user_id]
```
