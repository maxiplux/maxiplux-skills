---
name: spring-boot-vsa
description: Architectural guideline for Spring Boot projects using Vertical Slice Architecture (VSA). Use this skill whenever working on a Spring Boot codebase — creating new features/endpoints, reviewing existing handlers/controllers/services, or refactoring layered code into slices. Trigger on phrases like "vertical slice", "VSA", "feature slice", "new endpoint", "scaffold a feature", "refactor into slices", "where should this code live", "package structure", or when you see a `features/{name}/{api,handlers,model}` layout in the project. Also apply proactively when helping with Spring Boot code organization even if the user doesn't name the architecture — this is the enforcement document for VSA conventions (package layout, naming, injection rules, transactional boundaries, error handling).
---

# Spring Boot Vertical Slice Architecture (VSA)

This skill is a **guideline document** that AI coding agents follow when working on Spring Boot projects organized by vertical slice. It is intentionally tech-stack-agnostic — it has opinions on **structure, naming, and cross-cutting rules**, and stays quiet on choices that legitimately vary between projects (DB migration tool, security stack, frontend framework, ORM cache provider, etc.).

**Core idea:** Code is organized **by feature, not by technical layer**. Everything needed to serve one use case — the controller, DTOs, service logic, entity, repository, exceptions — lives together in one package. Cross-slice code lives in a separate `shared/` package.

---

## When to use this skill

Three workflows are supported:

1. **Scaffold** — generating the full file tree for a new feature slice
2. **Audit** — reviewing existing code for adherence to VSA conventions
3. **Refactor** — converting legacy layered code (`controller/`, `service/`, `repository/` packages) into vertical slices

Figure out which workflow applies from context and jump to the matching section below. When in doubt, ask the user.

---

## Package structure (the contract)

Every project following this skill has two top-level packages under the application's base package:

```
{base-package}/
├── {ApplicationName}Application.java    # Spring Boot entry point
├── shared/                               # Cross-cutting concerns only
│   ├── config/                           # @Configuration beans
│   ├── entity/                           # BaseEntity (id, createdAt, updatedAt) as @MappedSuperclass
│   ├── exception/                        # GlobalExceptionHandler (RFC 7807 ProblemDetail)
│   ├── security/                         # SecurityConfig, UserDetailsService, auth handlers
│   └── util/                             # Generic utilities used across 2+ slices
└── features/                             # All feature slices live here
    └── {feature}/
        ├── api/                          # HTTP layer
        │   ├── {Feature}Controller.java
        │   ├── request/                  # Request DTOs (Java records)
        │   └── response/                 # Response DTOs (Java records)
        ├── handlers/                     # Business logic — one @Service per use case
        ├── model/                        # JPA Entity, Spring Data Repository, Mapper
        ├── enums/                        # Slice-specific enums
        ├── exception/                    # Slice-specific exceptions (optional)
        └── events/                       # Domain events (optional, only when used)
```

**What "slice" means here:** one feature = one subfolder under `features/`. A slice should be cohesive — if you can name it with a single noun (`payment`, `invoice`, `notification`, `auth`), it's probably right-sized. If you find yourself wanting two nouns joined by "and", it's probably two slices.

**Shared package discipline:** the `shared/` package is not a dumping ground. Code only moves there when it's **genuinely used by 2+ slices**. A utility used by one slice stays inside that slice.

---

## Naming conventions

Follow these rigidly — they're what make VSA navigable. If you can't find a file, you can derive its path from the name.

| Component        | Pattern                                            | Example                                                  |
|------------------|----------------------------------------------------|----------------------------------------------------------|
| Controller       | `{Slice}Controller` in `api/`                      | `PaymentController`                                      |
| Request DTO      | `{Action}{Slice}Request` (record) in `api/request/`| `CreatePaymentRequest`, `UpdatePaymentRequest`           |
| Response DTO     | `{Slice}Response` (record) in `api/response/`      | `PaymentResponse`                                        |
| Handler          | `{Action}{Slice}Handler` (@Service) in `handlers/` | `CreatePaymentHandler`, `GetPaymentHandler`              |
| Entity           | `{Slice}` in `model/`                              | `Payment`                                                |
| Repository       | `{Slice}Repository` in `model/`                    | `PaymentRepository`                                      |
| Mapper           | `{Slice}Mapper` in `model/`                        | `PaymentMapper`                                          |
| Exception        | `{Slice}{Type}Exception` in `exception/`           | `PaymentNotFoundException`                               |
| Event            | `{Slice}{Action}Event` in `events/`                | `PaymentCompletedEvent`                                  |
| Listener         | `{Slice}EventListener` in `events/` or `handlers/` | `PaymentEventListener`                                   |

**The "one handler per use case" rule matters.** Don't write a `PaymentService` with ten methods. Write `CreatePaymentHandler`, `RefundPaymentHandler`, `GetPaymentHandler` as separate classes. Each handler has one public method (conventionally named `handle(...)`). This keeps slices small, testable, and easy to reason about.

---

## Cross-cutting rules (non-negotiable for this architecture)

These rules apply to every slice. They're the reason the architecture holds together.

### Dependency injection
- **Constructor injection only.** Use Lombok's `@RequiredArgsConstructor` and declare dependencies as `private final`.
- **Never use field `@Autowired`.** It hides dependencies, breaks testability, and makes cyclic dependencies silent.
- **Never use `@Autowired` on constructors either** — Spring infers it on a single public constructor.

### DTOs
- **Use Java records** for all request/response DTOs. They're immutable, have generated equals/hashCode/toString, and compose cleanly with validation.
- **Never leak entities across the HTTP boundary.** Entities are for persistence; records are for serialization. A `{Slice}Mapper` translates between them.
- **Validation annotations on record components** (`@NotNull`, `@Size`, `@Email`, etc.), with `@Valid` on the controller parameter.

### Transactions
- **`@Transactional` on handlers, not on controllers or repositories.** The handler owns the unit of work.
- **`@Transactional(readOnly = true)` on query handlers.** Gives the JDBC driver and JPA a hint to optimize.
- **Never wrap multiple handlers in a single transaction via the controller.** If two actions must be atomic, write a third handler that orchestrates them.

### JPA / queries
- **`FetchType.LAZY` on every `@ManyToOne`, `@OneToMany`, `@ManyToMany`.** Eager fetching kills performance silently.
- **Use `JOIN FETCH` in JPQL** (or entity graphs) when you know you need the associations — avoids the N+1 problem.
- **Bounded queries only.** Return `Page<T>`, `Slice<T>`, or use `findTopN` / `findFirstBy...`. Never return an unbounded `List<T>` from a repository method that could grow.
- **`@Enumerated(EnumType.STRING)`** always. `ORDINAL` breaks when enum values are reordered.

### Error handling
- **One `GlobalExceptionHandler` in `shared/exception/`**, using `@RestControllerAdvice`.
- **RFC 7807 `ProblemDetail`** as the response body for every error.
- **Slice-specific exceptions extend a common base** (e.g. `EntityNotFoundException`) and live in `{slice}/exception/`. The global handler maps them to HTTP status codes.
- **Never let `RuntimeException` propagate unmapped.** It should hit the handler and return a well-formed ProblemDetail with a stable `type` URI.

### Logging
- **`@Slf4j` on every class that catches exceptions or performs a side effect worth tracing.**
- **Parameterized messages only**: `log.info("User {} created payment {}", userId, paymentId)`. Never string-concatenate.
- **Log at the boundary** (handler entry for warn/error, DEBUG for detail). Don't log the same event at multiple layers.

### OpenAPI
- Controllers carry `@Tag(name = "...", description = "...")` at the class level.
- Each endpoint has `@Operation(summary = ..., description = ...)` and `@ApiResponses({...})`.
- Request/response DTOs use `@Schema(description = ...)` on non-obvious fields.

### Async / events (when applicable)
- **Domain events** go in `{slice}/events/` and extend `ApplicationEvent` (or are plain records used with `ApplicationEventPublisher`).
- **Listeners use `@EventListener` + `@Async("taskExecutor")`** when the work shouldn't block the publishing thread. Configure a named `taskExecutor` bean in `shared/config/AsyncConfig.java`.
- **Events are fire-and-forget.** Don't use them for request/response flow — use a direct handler call.

### External calls (when applicable)
- **Wrap with `@Retryable(maxAttempts = 3, backoff = @Backoff(delay = 1000, multiplier = 2))`** on the method that makes the call.
- **Implement a fallback** using `@Recover` for graceful degradation.
- **Treat the external client as part of the slice** if only one slice uses it; move to `shared/` only when 2+ slices need it.

---

## Workflow 1 — Scaffold a new slice

When the user asks to create a new feature, use this flow:

### Step 1 — gather inputs

Ask for (or infer from context):
- **Feature name** — a single noun, lowercase (e.g. `notification`, `payment`, `invoice`)
- **Actions** — which use cases to scaffold. Common set: `create`, `list`, `get`, `update`, `delete`. Pick only what's needed.
- **Base package** — e.g. `com.acme.billing`. Read from an existing file in the repo if available.

### Step 2 — run the scaffolding script

The skill ships with `scripts/create_slice.py` which generates the full tree:

```bash
python scripts/create_slice.py \
    --feature payment \
    --actions create,list,get,update,delete \
    --base-package com.acme.billing \
    --output-dir src/main/java
```

This creates all files under `src/main/java/com/acme/billing/features/payment/`, populated from the templates in `assets/`. Placeholders (`{{Feature}}`, `{{FEATURE}}`, `{{feature}}`, `{{BasePackage}}`, `{{Action}}`) are substituted automatically.

### Step 3 — fill in real logic

The scaffold produces a compiling but hollow slice — entity has only `id`, handler method is empty, mapper returns `null`. Walk through each file and fill in:
1. **Entity fields** based on the domain model the user described
2. **Request/response record components** based on what the API should accept/return
3. **Repository queries** specific to the feature
4. **Handler business logic** — the actual use case
5. **Mapper** — entity ↔ response conversion
6. **OpenAPI descriptions** on controller endpoints

### Step 4 — verify it fits the project

- Confirm imports resolve (base package, shared exception base class)
- Confirm the entity's `@Table(name = "...")` matches the project's naming convention (snake_case? plural?)
- Confirm the controller's `@RequestMapping` prefix matches the project's API convention (`/api/v1/...`? `/...`?)

### Reference files for complex slices

- **Basic CRUD** — see `references/basic-crud-slice.md` for a complete worked example
- **Event-driven** — see `references/event-driven-slice.md` when the slice publishes or listens for domain events
- **External API calls** — see `references/external-api-slice.md` when the slice calls a third-party service and needs retry/fallback

---

## Workflow 2 — Audit existing code for VSA violations

When the user asks you to review a file/slice/codebase, walk this checklist. Report violations as a categorized list with file:line references and a suggested fix. Don't rewrite the code unless the user asks.

### Structural violations
- Code outside `features/` or `shared/` (e.g. a top-level `service/` or `controller/` package) → **not VSA, needs refactor**
- A slice importing from another slice's internal packages (`features/payment/handlers` importing `features/invoice/model/Invoice`) → **cross-slice coupling; extract to `shared/` or call via an event/handler interface**
- Generic utilities living inside one slice but used by multiple → **move to `shared/util/`**
- "God" services named `{Slice}Service` with many methods → **split into `{Action}{Slice}Handler` classes**

### Naming violations
- Controller not named `{Slice}Controller`
- Handler not named `{Action}{Slice}Handler`
- DTOs not using the record keyword, or not ending in `Request`/`Response`
- Repository not named `{Slice}Repository`
- Exceptions not named `{Slice}{Type}Exception`

### Dependency injection violations
- `@Autowired` on a field — **always a violation**
- `@Autowired` on a constructor of a class with a single public constructor — **unnecessary, remove**
- Setter injection — **violation, convert to constructor**
- Missing `@RequiredArgsConstructor` on a class with `private final` dependencies — cosmetic, but flag it

### Data/query violations
- Repository method returning unbounded `List<T>` where the table can grow — **replace with `Page<T>` or `findTopN`**
- `@ManyToOne`/`@OneToMany` without `fetch = FetchType.LAZY` — **violation** (note: `@ManyToOne` defaults to EAGER, which is the wrong default)
- `@Enumerated` without `EnumType.STRING`, or missing `@Enumerated` entirely — **violation**
- N+1 risk: repository query returning entities with lazy associations that the caller will dereference in a loop — flag and suggest `JOIN FETCH`
- Entities exposed directly as controller return types — **violation, introduce a response record + mapper**

### Transaction violations
- `@Transactional` on a controller method — **violation, move to the handler**
- `@Transactional` on a repository interface — **violation, remove; handlers own the transaction**
- Query handler without `readOnly = true` — flag as a missed optimization
- Multiple handlers called from a single controller method that must be atomic — **violation, introduce an orchestrating handler**

### Error handling violations
- `try/catch` swallowing an exception without logging or rethrowing
- Controller returning `ResponseEntity<String>` for errors instead of ProblemDetail
- Slice without a `GlobalExceptionHandler` entry for its custom exceptions (either the global handler handles it generically, or a specific mapping is missing)
- `throw new RuntimeException(...)` instead of a typed slice exception

### Logging violations
- String concatenation in log messages: `log.info("user " + id + " did x")` — **violation, use `{}`**
- Missing `@Slf4j` on a class that catches exceptions
- `e.printStackTrace()` anywhere — **violation**
- Sensitive data (password, token, PII) in log messages

### OpenAPI violations
- Controller without `@Tag`
- Endpoint without `@Operation`
- Public API without `@ApiResponses` documenting error codes

**Audit report format:** group by severity (**Blocker / Major / Minor**) and by file. For each, give one-line description + fix hint. Keep it terse — the user doesn't want an essay per finding.

---

## Workflow 3 — Refactor legacy layered code into VSA

When the user has a layered project (`controller/`, `service/`, `repository/`, `dto/`) and wants to convert it to VSA, follow this sequence. Go one feature at a time — never refactor everything at once.

### Step 1 — identify the slices

Ask: "What features does this codebase have?" or infer from the controllers. Each controller is usually one slice. List them explicitly and confirm with the user before touching files.

### Step 2 — for each feature, do this in order

1. **Create the slice package** — `features/{feature}/` with subfolders `api/`, `api/request/`, `api/response/`, `handlers/`, `model/`, `exception/`
2. **Move the entity and repository** from the old `model/` and `repository/` packages into `features/{feature}/model/`
3. **Move the controller** into `features/{feature}/api/` and rename to `{Feature}Controller` if needed
4. **Move DTOs** from the old `dto/` package into `api/request/` and `api/response/`, splitting into separate record files if they were in one big class
5. **Split the `{Feature}Service` into per-action handlers.** Each public method on the old service becomes its own `{Action}{Feature}Handler` class with a single `handle(...)` method
6. **Move slice-specific exceptions** into `features/{feature}/exception/`
7. **Update package imports** project-wide — an IDE refactor does this safely
8. **Run tests.** If they pass, commit. Then move on to the next feature.

### Step 3 — promote cross-cutting code

After 2+ slices are converted, look at what's still in `shared/` or in an old generic package. Anything used by ≥2 slices stays in `shared/`; anything used by only one slice moves into that slice.

### Step 4 — delete the old packages

Once every controller and service has been moved, delete the old `controller/`, `service/`, `repository/`, `dto/` top-level packages. The codebase should now have only `{base}/{ApplicationName}Application.java`, `{base}/shared/`, and `{base}/features/`.

### Refactor hazards to watch for

- **Circular dependencies between slices.** If `PaymentHandler` needs data from `Invoice`, resolve via a domain event or a thin shared interface, not by importing across slices.
- **Transactional boundaries changing.** Moving `@Transactional` from a fat service method to a handler can split what was one transaction into many. Review each refactor for this.
- **Tests breaking because of package moves.** Test classes mirror the production structure — move them in the same commit.

---

## What this skill deliberately stays silent on

These vary legitimately between Spring Boot projects. Do not impose an opinion unless the user asks:

- **DB migrations** — Flyway, Liquibase, or `ddl-auto: update`
- **Security stack** — Spring Security with JWT, sessions, OTT, MFA, OAuth2, or basic auth
- **Frontend** — Thymeleaf, React, Next.js, Vue, or API-only
- **Caching** — Redis, Caffeine, Hazelcast, or none
- **Messaging** — Kafka, RabbitMQ, Spring ApplicationEvents, or none
- **Cloud/deploy** — Railway, AWS, GCP, bare metal
- **Build tool** — Gradle or Maven
- **Spring Boot major version** — 2.x, 3.x, 4.x
- **WebMVC vs WebFlux** — whichever the project uses

If a user's project has an opinion on these (check their `build.gradle`, `pom.xml`, `CLAUDE.md`, or an existing slice), follow it. If they ask you to choose, ask them first.

---

## Reference files

- `references/basic-crud-slice.md` — worked example: complete `payment` slice with CRUD operations
- `references/event-driven-slice.md` — worked example: slice that publishes a domain event + async listener
- `references/external-api-slice.md` — worked example: slice with `@Retryable` external API call + `@Recover` fallback

## Scaffolding assets

- `scripts/create_slice.py` — CLI that generates a new slice directory from templates
- `assets/*.tmpl` — Java file templates used by the script (also readable as standalone examples)
