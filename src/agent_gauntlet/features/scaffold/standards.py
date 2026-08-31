"""Composable Coding Standards Generator for Polyglot Workspaces."""

from __future__ import annotations

from collections.abc import Sequence

UNIVERSAL_PRINCIPLES = """## 1. Transversal Engineering & Architectural Principles

All code across all languages in this repository adheres to these core craftsmanship invariants:

- **Uncle Bob Clean Architecture & TDD:** Follow the strict Red $\\to$ Green $\\to$ Refactor cycle. Write black-box acceptance tests first, prove they fail with expected behavior, write the minimal implementation, and refactor while assertions remain frozen.
- **Package-by-Feature (Screaming Architecture):** Colocate related domain models, business logic, schemas, services, and tests within cohesive feature directories. Architecture must be strictly acyclic.
- **Fail-Closed Security & Verification:** In security, authorization, and verification boundaries, unexpected or undefined states MUST fail closed (deny/abort) rather than swallow exceptions or fall through.
- **Invariant Property Testing:** Verify mathematical and business invariants (round-trip serialization, idempotence, monotonicity) using property-based testing (`hypothesis`, `fast-check`, `proptest`).
- **Evidence-First Development:** Line-by-line review is backed by executable evidence. Verification reports and test suites must be 100% green with zero mutation survivors.
- **Clean Documentation:** Document *Why* (invariants, architectural boundaries, failure modes) rather than restating *What* code lines do. Avoid noisy comments."""

STANDARDS_PYTHON_BODY = """### Type Annotations & Static Analysis
- **Strict Typing:** All function and method signatures MUST have explicit argument and return type annotations.
- **Modern Syntax:** Use Python 3.10+ native type syntax (`list[str]`, `dict[str, Any]`, `X | None` instead of `Optional[X]`, `Union[X, Y]`).
- **No Untyped Any:** Avoid bare `Any` in public signatures; use concrete types, type variables, or `object` with runtime type guards.

### Immutability & Data Modeling
- **Value Objects:** Prefer `@dataclass(frozen=True)` or Pydantic `BaseModel(frozen=True)` for domain models and data transfer objects (DTOs).
- **Pure Functions:** Prefer stateless, side-effect-free pure functions where practical. Avoid mutable global or module-level state.
- **Default Arguments:** Never use mutable default arguments (`def foo(items=[])` is strictly forbidden; use `def foo(items: list[str] | None = None)`).

### Error Handling & Exceptions
- **Domain Exceptions:** Define explicit, domain-specific exception hierarchies deriving from a base project exception (`class DomainError(Exception): pass`).
- **No Bare Excepts:** Catching bare `except:` or broad `except Exception:` without re-raising or structured logging is strictly forbidden.
- **Fail-Closed:** In security or verification boundaries, unexpected states must fail closed (deny/abort) rather than swallow errors.

### Documentation & Google Docstrings
- **Google Docstrings Standard:** All public functions, classes, and methods MUST use structured Google-style docstrings with explicit `Args:`, `Returns:`, and `Raises:` sections.
- **Module Docstrings:** Every Python module MUST start with a top-level docstring summarizing its responsibility and boundary invariants.

### Concrete Python DO / DON'T Examples

#### ❌ DON'T (Anti-pattern: Untyped, mutable defaults, swallowed exceptions)
```python
# bad_module.py
def get_user_data(user_id, cache={}):  # ❌ Mutable default argument
    try:
        return cache[user_id]
    except:  # ❌ Bare except masks bugs
        return None
```

#### ✅ DO (Idiomatic: Strict types, frozen dataclass, Google docstrings, domain exceptions)
```python
\"\"\"User data access and cache management feature.\"\"\"

from collections.abc import Mapping
from dataclasses import dataclass


class UserNotFoundError(Exception):
    \"\"\"Raised when the requested user profile cannot be located.\"\"\"


@dataclass(frozen=True)
class UserProfile:
    \"\"\"Immutable domain representation of a user profile.\"\"\"

    user_id: str
    email: str
    is_active: bool = True


def get_user_data(
    user_id: str,
    cache: Mapping[str, UserProfile] | None = None,
) -> UserProfile:
    \"\"\"Retrieves user profile data from cache or repository.

    Args:
        user_id: Unique string identifier for the user.
        cache: Optional pre-warmed cache map. Defaults to None.

    Returns:
        The resolved immutable UserProfile.

    Raises:
        ValueError: If user_id is empty or malformed.
        UserNotFoundError: If the user profile does not exist.
    \"\"\"
    if not user_id.strip():
        raise ValueError("user_id cannot be empty")

    local_cache = cache or {}
    if user_id not in local_cache:
        raise UserNotFoundError(f"User '{user_id}' not found in cache")

    return local_cache[user_id]
```"""

STANDARDS_TYPESCRIPT_BODY = """### Type Safety & TypeScript Disciplines
- **Strict Mode:** Code must compile with `strict: true` and zero compiler warnings.
- **Full Typecheck & Project References:** In modern TypeScript/Vite/Solution architectures (where root `tsconfig.json` contains `"files": []` and `"references": [...]`), blind `tsc --noEmit` exits with code 0 without checking source files. Verification layers MUST use `tsc -b` (build mode) or `tsc --noEmit -p tsconfig.app.json` to ensure full type validation across all composite sub-projects.
- **No `any`:** `any` is strictly prohibited. Use `unknown` combined with type narrowing, type predicates (`is`), or validation libraries (`zod`) at runtime I/O boundaries.
- **Interfaces vs Types:** Use `interface` for public API object shapes and extensible contracts; use `type` for unions, intersections, tuple types, and utility types.
- **Discriminated Unions:** Model state machines and mutually exclusive states using discriminated unions (e.g. `{ status: 'success'; data: T } | { status: 'error'; error: Error }`) rather than parallel optional boolean flags.

### React & Component Architecture
- **Functional Components:** All components must be pure functional components with explicit props interfaces (`interface ButtonProps { ... }`).
- **Custom Hooks for Logic:** JSX templates must remain declarative presentation layers. Extract non-trivial business logic, asynchronous state, and side-effects into custom hooks (`use[Feature]`).
- **Component File Budget:** Components should stay focused and ideally under 150 lines. Decompose complex UIs into smaller, single-responsibility sub-components.
- **Immutability First:** Prefer `const` over `let`. Never mutate props or state objects directly; use shallow copies or immutable updates.

### Documentation & TSDoc Standards
- **TSDoc Documentation Standard:** All exported functions, hooks, interfaces, and component props MUST be documented with TSDoc tags (`@param`, `@returns`, `@throws`, `@example`).
- **Self-Documenting Types:** Do not write comments that merely rephrase type signatures. Document semantic invariants and edge-case behavior.

### Concrete TypeScript DO / DON'T Examples

#### ❌ DON'T (Anti-pattern: `any`, bloated component with inline async side-effects)
```tsx
// ❌ any type, mutable let, unhandled async in render
export default function UserCard(props: any) {
  let [data, setData] = React.useState<any>(null);
  React.useEffect(() => {
    fetch('/api/user/' + props.id).then(r => r.json()).then(d => setData(d));
  }, [props.id]);
  return <div>{data?.name}</div>;
}
```

#### ✅ DO (Idiomatic: Typed props interface, custom hook, TSDoc, discriminated union)
```tsx
import React from 'react';

/** State model for asynchronous user profile loading. */
export type UserState =
  | { status: 'idle' | 'loading' }
  | { status: 'success'; profile: UserProfile }
  | { status: 'error'; error: Error };

export interface UserProfile {
  readonly id: string;
  readonly name: string;
  readonly email: string;
}

export interface UserCardProps {
  /** The unique user identifier to display. */
  readonly userId: string;
  /** Optional callback fired when the profile card is clicked. */
  readonly onSelect?: (userId: string) => void;
}

/**
 * Custom hook to manage user profile fetching and lifecycle state.
 *
 * @param userId - Unique identifier for the user.
 * @returns Discriminated union state representing loading, success, or error.
 */
export function useUserProfile(userId: string): UserState {
  const [state, setState] = React.useState<UserState>({ status: 'idle' });

  React.useEffect(() => {
    let isMounted = true;
    setState({ status: 'loading' });

    fetch(`/api/users/${encodeURIComponent(userId)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load user: ${res.statusText}`);
        return res.json();
      })
      .then((profile: UserProfile) => {
        if (isMounted) setState({ status: 'success', profile });
      })
      .catch((error: Error) => {
        if (isMounted) setState({ status: 'error', error });
      });

    return () => {
      isMounted = false;
    };
  }, [userId]);

  return state;
}

/**
 * Presentational component rendering user profile details.
 */
export const UserCard: React.FC<UserCardProps> = ({ userId, onSelect }) => {
  const state = useUserProfile(userId);

  if (state.status === 'loading') return <div>Loading profile...</div>;
  if (state.status === 'error') return <div role="alert">{state.error.message}</div>;
  if (state.status !== 'success') return null;

  return (
    <article onClick={() => onSelect?.(userId)} className="user-card">
      <h3>{state.profile.name}</h3>
      <p>{state.profile.email}</p>
    </article>
  );
};
```"""

STANDARDS_RUST_BODY = """### Naming & Case Conventions (C-CASE)
- **Naming Conventions:**
  - `UpperCamelCase` for types and traits (e.g., `VerificationReport`, `TaskContract`).
  - `snake_case` for functions, methods, and modules (e.g., `execute_verify`, `parse_task_file`).
  - `SCREAMING_SNAKE_CASE` for constants and statics.
- **Constructors:** Use `new()` or `with_capacity()` as standard constructor names.

### Error Handling & Invariants (C-GOOD-ERR)
- **Error Handling:**
  - `unwrap()` and `expect()` are strictly forbidden in production code. Use `?` operator for clean error propagation.
  - Libraries must define structured, strongly-typed errors implementing `std::error::Error` (via `thiserror`). Application binaries may use `anyhow` for top-level context.
  - Panics are acceptable only in test assertions and invariant property tests.

### Ergonomics & Ownership (C-CONV, C-GENERIC)
- **Borrowing over Cloning:** Pass shared references (`&str`, `&[T]`) instead of owned types (`&String`, `&Vec<T>`) in function arguments.
- **Standard Conversions:** Implement standard conversion traits (`From`, `TryFrom`, `AsRef`) where natural conversions exist.
- **Newtype Pattern (C-NEWTYPE):** Wrap primitive types in lightweight domain structs (e.g., `struct UserId(String);`) to prevent *Primitive Obsession*.

### Documentation & Tests (C-DOC)
- **Rustdoc Documentation Standard:** All public items MUST have `///` doc comments detailing purpose, `# Arguments`, `# Returns`, `# Errors`, `# Panics`, and `# Examples`.
- **Clippy Strictness:** Code must pass `cargo clippy -- -D warnings` with zero warnings.

### Concrete Rust DO / DON'T Examples

#### ❌ DON'T (Anti-pattern: Production `unwrap()`, excessive cloning, primitive obsession)
```rust
// ❌ unwrap in production, taking &String instead of &str, cloning everywhere
pub fn fetch_user_name(id: &String) -> String {
    let db = open_connection().unwrap(); // ❌ Panic in production
    let user = db.query(id.clone()).unwrap();
    user.name
}
```

#### ✅ DO (Idiomatic: Newtype pattern, `thiserror`, borrowing, standard doc comments)
```rust
use std::path::Path;
use thiserror::Error;

/// Structured domain error hierarchy.
#[derive(Debug, Error)]
pub enum UserError {
    #[error("User '{0}' not found")]
    NotFound(String),
    #[error("Database connection failed: {0}")]
    ConnectionFailed(String),
}

/// Strongly-typed User identifier preventing primitive obsession.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(String);

impl UserId {
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}
```"""

CROSS_STACK_INVARIANTS = """In polyglot repositories where multiple languages communicate (e.g. TypeScript frontend + Python/Rust backend):

- **Explicit Schema Contracts:** All boundary APIs (REST HTTP, GraphQL, WebSockets, IPC, CLI JSON) MUST be governed by machine-readable, versioned schema definitions (OpenAPI, JSON Schema, Protobuf).
- **Zero Untyped JSON Bridges:** Untyped dictionary/object mappings across boundaries are prohibited. Payloads must be validated with runtime validators (`zod` in TypeScript, Pydantic in Python, `serde` with strong types in Rust).
- **Uniform Error Envelope:** All boundary endpoints must emit a standardized error envelope (`{ "error": { "code": string, "message": string, "details": object } }`).
- **Deterministic Serialization:** Invariant round-trip tests must guarantee that data serialized in one stack deserializes identically in other stacks without precision or field loss."""

# Standalone single-stack standards (Backward-compatible format)
CODING_STANDARDS_PYTHON = """# Coding Standards: Python

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
\"\"\"User data access and cache management feature.\"\"\"

from collections.abc import Mapping
from dataclasses import dataclass


class UserNotFoundError(Exception):
    \"\"\"Raised when the requested user profile cannot be located.\"\"\"


@dataclass(frozen=True)
class UserProfile:
    \"\"\"Immutable domain representation of a user profile.\"\"\"

    user_id: str
    email: str
    is_active: bool = True


def get_user_data(
    user_id: str,
    cache: Mapping[str, UserProfile] | None = None,
) -> UserProfile:
    \"\"\"Retrieves user profile data from cache or repository.

    Args:
        user_id: Unique string identifier for the user.
        cache: Optional pre-warmed cache map. Defaults to None.

    Returns:
        The resolved immutable UserProfile.

    Raises:
        ValueError: If user_id is empty or malformed.
        UserNotFoundError: If the user profile does not exist.
    \"\"\"
    if not user_id.strip():
        raise ValueError("user_id cannot be empty")

    local_cache = cache or {}
    if user_id not in local_cache:
        raise UserNotFoundError(f"User '{user_id}' not found in cache")

    return local_cache[user_id]
```
"""

CODING_STANDARDS_TYPESCRIPT = """# Coding Standards: TypeScript & React

This repository follows the **Google TypeScript Style Guide** and modern **Functional React & Clean Architecture** principles.

---

## 1. Type Safety & TypeScript Disciplines
- **Strict Mode:** Code must compile with `strict: true` and zero compiler warnings.
- **Full Typecheck & Project References:** In modern TypeScript/Vite/Solution architectures (where root `tsconfig.json` contains `"files": []` and `"references": [...]`), blind `tsc --noEmit` exits with code 0 without checking source files. Verification layers MUST use `tsc -b` (build mode) or `tsc --noEmit -p tsconfig.app.json` to ensure full type validation across all composite sub-projects.
- **No `any`:** `any` is strictly prohibited. Use `unknown` combined with type narrowing, type predicates (`is`), or validation libraries (`zod`) at runtime I/O boundaries.
- **Interfaces vs Types:** Use `interface` for public API object shapes and extensible contracts; use `type` for unions, intersections, tuple types, and utility types.
- **Discriminated Unions:** Model state machines and mutually exclusive states using discriminated unions (e.g. `{ status: 'success'; data: T } | { status: 'error'; error: Error }`) rather than parallel optional boolean flags.

## 2. React & Component Architecture
- **Functional Components:** All components must be pure functional components with explicit props interfaces (`interface ButtonProps { ... }`).
- **Custom Hooks for Logic:** JSX templates must remain declarative presentation layers. Extract non-trivial business logic, asynchronous state, and side-effects into custom hooks (`use[Feature]`).
- **Component File Budget:** Components should stay focused and ideally under 150 lines. Decompose complex UIs into smaller, single-responsibility sub-components.
- **Pure Render & Side-Effects:** Avoid side-effects during render. All side-effects belong in `useEffect` or event handlers.

## 3. Immutability & State Management
- **Immutability First:** Prefer `const` over `let`. Never mutate props or state objects directly; use shallow copies or immutable updates.
- **Explicit Exports:** Use explicit named exports for components, functions, and types. Avoid `export default` except where required by file-system routing.
- **Readonly Parameters:** Mark parameters as `readonly` when they are not intended to be mutated.

## 4. Error Handling & Async
- **Predictable Async:** Always handle Promise rejections. Avoid unhandled floating promises (`void asyncFn()`).
- **Error Boundaries:** Wrap component sub-trees in Error Boundaries to gracefully catch rendering crashes without bringing down the entire application.

## 5. Documentation & TSDoc Standards
- **TSDoc Documentation Standard:** All exported functions, hooks, interfaces, and component props MUST be documented with TSDoc tags (`@param`, `@returns`, `@throws`, `@example`).
- **Self-Documenting Types:** Do not write comments that merely rephrase type signatures. Document semantic invariants and edge-case behavior.

## 6. Concrete DO / DON'T Examples

### ❌ DON'T (Anti-pattern: `any`, bloated component with inline async side-effects)
```tsx
// ❌ any type, mutable let, unhandled async in render
export default function UserCard(props: any) {
  let [data, setData] = React.useState<any>(null);
  React.useEffect(() => {
    fetch('/api/user/' + props.id).then(r => r.json()).then(d => setData(d));
  }, [props.id]);
  return <div>{data?.name}</div>;
}
```

### ✅ DO (Idiomatic: Typed props interface, custom hook, TSDoc, discriminated union)
```tsx
import React from 'react';

/** State model for asynchronous user profile loading. */
export type UserState =
  | { status: 'idle' | 'loading' }
  | { status: 'success'; profile: UserProfile }
  | { status: 'error'; error: Error };

export interface UserProfile {
  readonly id: string;
  readonly name: string;
  readonly email: string;
}

export interface UserCardProps {
  /** The unique user identifier to display. */
  readonly userId: string;
  /** Optional callback fired when the profile card is clicked. */
  readonly onSelect?: (userId: string) => void;
}

/**
 * Custom hook to manage user profile fetching and lifecycle state.
 *
 * @param userId - Unique identifier for the user.
 * @returns Discriminated union state representing loading, success, or error.
 */
export function useUserProfile(userId: string): UserState {
  const [state, setState] = React.useState<UserState>({ status: 'idle' });

  React.useEffect(() => {
    let isMounted = true;
    setState({ status: 'loading' });

    fetch(`/api/users/${encodeURIComponent(userId)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load user: ${res.statusText}`);
        return res.json();
      })
      .then((profile: UserProfile) => {
        if (isMounted) setState({ status: 'success', profile });
      })
      .catch((error: Error) => {
        if (isMounted) setState({ status: 'error', error });
      });

    return () => {
      isMounted = false;
    };
  }, [userId]);

  return state;
}

/**
 * Presentational component rendering user profile details.
 */
export const UserCard: React.FC<UserCardProps> = ({ userId, onSelect }) => {
  const state = useUserProfile(userId);

  if (state.status === 'loading') return <div>Loading profile...</div>;
  if (state.status === 'error') return <div role="alert">{state.error.message}</div>;
  if (state.status !== 'success') return null;

  return (
    <article onClick={() => onSelect?.(userId)} className="user-card">
      <h3>{state.profile.name}</h3>
      <p>{state.profile.email}</p>
    </article>
  );
};
```
"""

CODING_STANDARDS_RUST = """# Coding Standards: Rust

This repository follows the **Official Rust API Guidelines (C-API-GUIDELINES)** and idiomatic Clean Rust principles.

---

## 1. Naming & Case Conventions (C-CASE)
- **Naming Conventions:**
  - `UpperCamelCase` for types and traits (e.g., `VerificationReport`, `TaskContract`).
  - `snake_case` for functions, methods, and modules (e.g., `execute_verify`, `parse_task_file`).
  - `SCREAMING_SNAKE_CASE` for constants and statics.
- **Constructors:** Use `new()` or `with_capacity()` as standard constructor names.

## 2. Error Handling & Invariants (C-GOOD-ERR)
- **Error Handling:**
  - `unwrap()` and `expect()` are strictly forbidden in production code. Use `?` operator for clean error propagation.
  - Libraries must define structured, strongly-typed errors implementing `std::error::Error` (via `thiserror`). Application binaries may use `anyhow` for top-level context.
  - Panics are acceptable only in test assertions and invariant property tests.

## 3. Ergonomics & Ownership (C-CONV, C-GENERIC)
- **Borrowing over Cloning:** Pass shared references (`&str`, `&[T]`) instead of owned types (`&String`, `&Vec<T>`) in function arguments.
- **Standard Conversions:** Implement standard conversion traits (`From`, `TryFrom`, `AsRef`) where natural conversions exist.
- **Newtype Pattern (C-NEWTYPE):** Wrap primitive types in lightweight domain structs (e.g., `struct UserId(String);`) to prevent *Primitive Obsession*.

## 4. Documentation & Tests (C-DOC)
- **Rustdoc Documentation Standard:** All public items MUST have `///` doc comments detailing purpose, `# Arguments`, `# Returns`, `# Errors`, `# Panics`, and `# Examples`.
- **Clippy Strictness:** Code must pass `cargo clippy -- -D warnings` with zero warnings.

## 5. Concrete DO / DON'T Examples

### ❌ DON'T (Anti-pattern: Production `unwrap()`, excessive cloning, primitive obsession)
```rust
// ❌ unwrap in production, taking &String instead of &str, cloning everywhere
pub fn fetch_user_name(id: &String) -> String {
    let db = open_connection().unwrap(); // ❌ Panic in production
    let user = db.query(id.clone()).unwrap();
    user.name
}
```

### ✅ DO (Idiomatic: Newtype pattern, `thiserror`, borrowing, standard doc comments)
```rust
use std::path::Path;
use thiserror::Error;

/// Structured domain error hierarchy.
#[derive(Debug, Error)]
pub enum UserError {
    #[error("User '{0}' not found")]
    NotFound(String),
    #[error("Database connection failed: {0}")]
    ConnectionFailed(String),
}

/// Strongly-typed User identifier preventing primitive obsession.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(String);

impl UserId {
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}
```
"""

STACK_DISPLAY_NAMES = {
    "python": "Python",
    "typescript": "TypeScript & React",
    "rust": "Rust",
}

STACK_BODIES = {
    "python": ("Google Python Style Guide", STANDARDS_PYTHON_BODY),
    "typescript": ("Google TypeScript Style Guide & React", STANDARDS_TYPESCRIPT_BODY),
    "rust": ("Official Rust API Guidelines", STANDARDS_RUST_BODY),
}


def normalize_stacks(stacks: str | Sequence[str] | None) -> list[str]:
    """Normalizes string or sequence of stack names into a deduplicated list of lowercase strings."""
    if stacks is None:
        return []

    raw_items: list[str] = []
    if isinstance(stacks, str):
        raw_items = [s.strip() for s in stacks.split(",") if s.strip()]
    else:
        for item in stacks:
            if isinstance(item, str):
                for s in item.split(","):
                    if s.strip():
                        raw_items.append(s.strip().lower())

    # Deduplicate preserving order
    deduped: list[str] = []
    for item in raw_items:
        clean = item.lower()
        if clean not in deduped:
            deduped.append(clean)
    return deduped


def generate_coding_standards(stacks: str | Sequence[str] | None) -> str:
    """Generates standalone or composite polyglot CODING_STANDARDS.md markdown."""
    normalized = normalize_stacks(stacks)
    if not normalized:
        normalized = ["python"]

    # Single-stack optimization for standard standalone documents
    if len(normalized) == 1:
        single = normalized[0]
        if single == "python":
            return CODING_STANDARDS_PYTHON
        if single == "typescript":
            return CODING_STANDARDS_TYPESCRIPT
        if single == "rust":
            return CODING_STANDARDS_RUST
        # Fallback for unknown single stack
        return CODING_STANDARDS_PYTHON

    # Polyglot composite document generation
    titles = [STACK_DISPLAY_NAMES.get(s, s.capitalize()) for s in normalized]
    composite_title = " & ".join(titles)

    sections: list[str] = [
        f"# Coding Standards: Polyglot ({composite_title})",
        "",
        "This repository employs a **polyglot multi-stack architecture**. All subsystems adhere to authoritative language style guides harmonized under unified architectural invariants.",
        "",
        "---",
        "",
        UNIVERSAL_PRINCIPLES,
    ]

    sec_idx = 2
    for s in normalized:
        display_name = STACK_DISPLAY_NAMES.get(s, s.capitalize())
        guide_name, body = STACK_BODIES.get(
            s,
            ("Standard Style Guide", f"Follow idiomatic conventions for {display_name}."),
        )
        sections.extend(
            [
                "",
                "---",
                "",
                f"## {sec_idx}. {display_name} Standards",
                f"Subsystems written in {display_name} follow the **{guide_name}**:",
                "",
                body,
            ]
        )
        sec_idx += 1

    sections.extend(
        [
            "",
            "---",
            "",
            f"## {sec_idx}. Cross-Stack Boundary & Interop Invariants",
            CROSS_STACK_INVARIANTS,
            "",
        ]
    )

    return "\n".join(sections)
