# Conventions reference

Placement, naming, and the shared helpers a slice leans on. Read this when deciding where a file
belongs, what to call it, or when a helper the templates assume does not exist in the codebase yet.

## Contents

- [File-kind catalog](#file-kind-catalog)
- [Naming](#naming)
- [Layering rules](#layering-rules)
- [Slice-root helpers](#slice-root-helpers)
- [Shared helpers a slice depends on](#shared-helpers-a-slice-depends-on)
- [When to promote to shared/](#when-to-promote-to-shared)
- [Anti-patterns](#anti-patterns)

## File-kind catalog

| File | Location | Contains | Never contains |
|---|---|---|---|
| `<singular>.models.ts` | `core/<domain>/` | Interfaces mirroring API DTOs, contract constants | Classes, logic, Angular imports |
| `<domain>.service.ts` | `core/<domain>/` | `providedIn: 'root'` service, one method per endpoint | State, `subscribe`, caching, mapping to view models |
| `<domain>.service.spec.ts` | `core/<domain>/` | Method/URL/body assertions per endpoint | DOM, `TestBed.createComponent` |
| `<singular>-errors.ts` | `features/<domain>/` | Slug → sentence map | HTTP calls, component references |
| `<singular>-validators.ts` | `features/<domain>/` | `ValidatorFn`s used by this slice's forms | Anything a single form uses once (inline it) |
| `<singular>-<concept>.ts` | `features/<domain>/` | Pure derivations: status labels, filter predicates, draft models | Rendering, injection |
| `<domain>-fixtures.spec-helper.ts` | `features/<domain>/` | Test builders returning DTOs with overrides | Assertions, `describe`/`it` |
| `<component>.ts` | `features/<domain>/<component>/` | Standalone OnPush component | Business rules reusable by siblings (extract to slice root) |
| `<component>.html` | `features/<domain>/<component>/` | Template | Logic beyond signal reads and bindings |
| `<component>.spec.ts` | `features/<domain>/<component>/` | DOM-driven component spec | Assertions on private members |

Non-obvious ones:

- **`*.spec-helper.ts`, not `*.fixtures.ts`.** The `spec-helper` suffix keeps the file out of the test
  runner's `*.spec.ts` glob while still marking it as test-only, so it never ships in the app bundle
  and never gets picked up as an empty test file.
- **A slice-root `*.ts` that has its own `*.spec.ts`** is the normal shape for pure helpers — they are
  the cheapest things in the slice to test and the most reused, so test them directly rather than
  through a component.

## Naming

- **Files and folders**: kebab-case. `care-setting-editor/care-setting-editor.ts`.
- **No type suffix in file names.** `training-list.ts`, not `training-list.component.ts`. Modern
  Angular dropped the suffix; the folder already says what it is.
- **Class names**: PascalCase with no `Component`/`Service` noise for components — `TrainingList`,
  `CareSettingEditor` — but services keep `Service` (`TrainingService`) because the word carries
  meaning at the injection site.
- **Selectors**: `app-<file-name>` — `app-care-setting-editor`.
- **Domain folder is plural, the entity is singular.** `core/care-settings/care-setting.models.ts`.
  The folder is a collection of things about a domain; the model file describes one record. Services
  take the plural (`CareSettingsService`) because they operate over the collection.
- **DTO names mirror the API**, including the `Request`/`Response` suffixes:
  `CareSettingResponse`, `CreateCareSettingRequest`, `UpdateCareSettingRequest`. Renaming them to
  something prettier costs you the ability to grep from a server log line to the client code.
- **Route paths** are kebab-case and match the capability, with admin surfaces under `admin/<domain>`.

## Layering rules

```
layout/  ──▶ features/ ──▶ core/ ──▶ (Angular, RxJS)
              │              ▲
              └──▶ shared/ ──┘
```

- `core/` imports nothing from `features/`, `shared/`, or `layout/`. It is the bottom.
- `features/<a>` never imports from `features/<b>`. Shared UI is promoted to `shared/`; shared data is
  reached through `core/<b>`'s service, which is legitimate — a campaign screen listing roles should
  inject `RolesService`, not reimplement it.
- `shared/` imports from `core/` freely but knows no domain: a shared component parameterised by
  `CareSettingResponse` is a features component in the wrong folder.
- `layout/` may import `shared/` and `core/`, and references features only as lazy route imports.

The practical test for "is this really shared?": could you move it to another Angular app in this
organisation without renaming anything? If not, it is slice-local.

## Slice-root helpers

Pull a helper up to the slice root the moment a **second** component in the slice needs it, and give
it a name that says what it decides rather than what it operates on:

| Helper | Shape | Why it leaves the component |
|---|---|---|
| Error map | `Readonly<Record<string, string>>` | Both the list and the editor surface the same server errors |
| Validators | `(control: AbstractControl) => ValidationErrors \| null` | Create and edit forms must agree on the rule |
| Status derivation | `(dto) => 'draft' \| 'published' \| ...` | The row badge and the detail header must not drift |
| Filter predicates | `(dto, filters) => boolean` | Testable without a fixture, reusable by the export path |
| Draft model | class or interface + pure transitions | A wizard's in-progress state, testable without the DOM |

Each of these is pure, so it gets a direct unit spec — much cheaper than reaching the same branch
through a rendered component.

## Shared helpers a slice depends on

These live in `core/` or `shared/` and are created once for the whole app. If the codebase does not
have them, create them before writing the slice rather than inlining an ad-hoc version.

### `problemMessage` (`core/http/problem-message.ts`)

Turns a failed HTTP call into a sentence, keyed on the RFC 9457 problem `type` slug.

```ts
import { HttpErrorResponse } from '@angular/common/http';

export interface ProblemDetail {
  type?: string;
  title?: string;
  detail?: string;
  errors?: { field: string; message: string }[];
}

/**
 * Resolution order: a matched slug message → the first field error on a 400 → the problem `detail`
 * → an offline hint on status 0 → the fallback. The slug is a stable contract; `detail` is prose and
 * must not be matched on.
 */
export function problemMessage(
  err: unknown,
  fallback: string,
  slugMessages: Record<string, string> = {},
): string {
  if (err instanceof HttpErrorResponse) {
    const problem = err.error as ProblemDetail | null;
    const slug = problem?.type?.split('/').pop();
    if (slug && slugMessages[slug]) {
      return slugMessages[slug];
    }
    if (err.status === 400 && problem?.errors?.length) {
      return problem.errors[0].message;
    }
    if (problem?.detail) {
      return problem.detail;
    }
    if (err.status === 0) {
      return 'Cannot reach the server. Check your connection and try again.';
    }
  }
  return fallback;
}
```

The ordering is the whole design: a slug the slice has an opinion about wins, then the server's own
specific words, and only then a generic fallback. Every step down that ladder loses information, so
never start at the bottom.

### `Page<T>` (`core/http/page.model.ts`)

Paginated endpoints return an envelope, not a bare array. Model it once:

```ts
export interface Page<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  /** Current page index (0-based). */
  number: number;
  size: number;
  first: boolean;
  last: boolean;
  numberOfElements: number;
}
```

### A directory surface (`shared/data-view/`)

Every list screen needs loading, empty, and content states, and every list screen that renders both
cards and a table needs them **once**, above the split — otherwise each state is written twice, and
the table copy carries a `colspan` that has to be kept in step with the column count by hand.

The rules worth copying if you build your own:

- Spinner only on first load (`loading() && isEmpty()`), so a refetch keeps existing rows on screen
  instead of blanking the directory.
- Empty and loading are mutually exclusive — empty is a resting state, not a loading one.
- The toolbar and error banner pin above all three states; pagination pins below. They belong to the
  surface, not to any one state.
- Content projection slots discard unslotted content silently, so document the required attributes.

## When to promote to shared/

Promote when **both** are true:

1. A second slice needs it, concretely and now.
2. Its public API mentions no domain type. `input<CareSettingResponse>()` disqualifies it — generalise
   to a structural type (`{ id: string; name: string }`) or leave it in the slice.

Do not promote for symmetry, for "we'll probably need it", or because it looks generic. A shared
component acquires configuration inputs every time a new consumer has a slightly different need, and
the third or fourth of those turns it into a component with fourteen inputs that nobody can change
safely. Leaving a near-duplicate in two slices is frequently the cheaper trade — duplication is
visible and local, premature coupling is neither.

## Anti-patterns

| Anti-pattern | Why it hurts | Do instead |
|---|---|---|
| `services/`, `models/`, `components/` top-level folders | A one-line feature change touches four trees | Group by capability |
| Barrel `index.ts` per slice | Defeats lazy chunking, hides cycles, breaks tree-shaking | Import the file directly |
| Service holding the list state | Two screens silently share and corrupt a cache | State in the container signal; service stays stateless |
| Component importing another slice's component | Creates a cycle the compiler cannot always catch | Promote to `shared/` |
| `any` on an error callback | Untyped junk reaches the template | `err: unknown` + `problemMessage` |
| Mapping DTOs into view models in the service | Two contracts to keep in step, for no gain | `computed()` in the component |
| Eager `import` of a feature component in the routes file | The whole slice lands in the initial bundle | `loadComponent` |
| One `errors.ts` for the whole app | Every slice's failures in one unreviewable map | One map per slice |
