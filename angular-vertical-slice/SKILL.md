---
name: angular-vertical-slice
description: Vertical-slice architecture for Angular applications — how to lay out, build, and review a feature so its DTOs, HTTP service, components, error map, lazy route, and tests live together as one deletable unit instead of being scattered across type-based folders (services/, models/, components/). Use this whenever you add or extend an Angular screen, page, feature area, or admin CRUD surface; create a service + models + component set; wire a lazy loadComponent route or sidebar entry; decide which folder an Angular file belongs in; or review Angular feature code for structure, layering, and naming. Trigger it even when the ask sounds small — "add a departments page", "build the X admin screen", "where should this service live", "make a component for Y", "refactor this feature" — because slice placement is decided by the first file you write and is expensive to undo later.
---

# Angular vertical-slice architecture

## What a slice is

A slice is one business capability — *care settings*, *training modules*, *campaigns* — that owns
every layer it needs: the DTOs mirroring its API contract, the HTTP service that calls it, the
components that render it, the map from server error codes to sentences a user can act on, its route
entries, and its tests. Files are grouped by **what capability they serve**, not by **what kind of
file they are**. There is no app-wide `services/`, `models/`, or `components/` folder.

Two properties make this worth the discipline:

- A change request lands in one directory tree. "Add an archive toggle to care settings" touches
  `core/care-settings/` and `features/care-settings/` and nothing else.
- A capability is deletable. Removing a feature is two folders, one route entry, one nav entry — not
  an afternoon of grepping for orphaned imports.

The cost is that reuse becomes a deliberate act rather than an accident, which is what the promotion
rules below exist for.

## The shape

```
src/app/
  core/<domain>/                        data layer — never contains a template
    <singular>.models.ts                DTOs mirroring the API contract
    <domain>.service.ts                 root-provided, HttpClient -> Observable
    <domain>.service.spec.ts
  features/<domain>/                    UI layer
    <singular>-errors.ts                RFC 9457 slug -> friendly sentence
    <singular>-validators.ts            form rules shared by this slice's forms
    <domain>-fixtures.spec-helper.ts    test builders for this slice
    <component-name>/
      <component-name>.ts               standalone, OnPush, signals
      <component-name>.html
      <component-name>.spec.ts
  shared/<component>/                   cross-slice UI, promoted deliberately
  core/http/                            cross-cutting HTTP plumbing (interceptors, problem mapping)
  layout/                               shell + nav registry
  app.routes.ts                         every slice's lazy entry
```

`core/<domain>` and `features/<domain>` are **the same slice under two roofs**. They carry the same
name, and they are created, changed, and deleted together. Splitting them is not a retreat to
layer-by-type; it is a lifetime distinction:

- The data layer outlives and out-scopes any one screen. Two feature areas routinely read the same
  domain (a resident-facing library and an admin editor over the same training modules), and guards,
  interceptors, or resolvers may need the service with no component in scope.
- Keeping `core/<domain>` template-free means anything can import it without dragging in a component
  tree, a styling dependency, or a circular import back through `features/`.

**Single-consumer exception.** A service that is genuinely private to one feature area — a dashboard
aggregator, a wizard's draft store — may live beside its components in `features/<domain>/`. Prefer
`core/` when unsure: moving a service outward is a one-line import change, moving it inward after
three importers have appeared is not.

## Choosing where a file goes

Work down this list and stop at the first match:

1. **Does it describe the API contract or call it?** → `core/<domain>/`. Models and services only;
   no Angular component, no template, no CSS.
2. **Is it rendered, and does it belong to exactly one capability?** → `features/<domain>/<component-name>/`.
3. **Is it a pure helper (error map, validator, label formatter, status derivation) used by two or
   more components in the same slice?** → the slice root, `features/<domain>/<thing>.ts`. Slice-root
   helpers are what keep component files about rendering.
4. **Is it rendered and already used by two or more slices?** → `shared/<component>/`. Promote on the
   *second* real consumer, not the first speculative one. A component with a domain type in its
   `input()` signature is not shared — generalise the type first or leave it where it is.
5. **Is it infrastructure with no domain meaning at all** (interceptor, problem-detail mapper, page
   model, auth guard)? → `core/<area>/`.

Two rules that keep the graph acyclic and are worth stating plainly, because violating either is how
vertical slices rot back into a layered ball of mud:

- **`core/` never imports from `features/`.** If a service needs something a component owns, the
  thing is modelled in the wrong place.
- **Slices do not import each other's components.** Sharing UI means promoting to `shared/`. Sharing
  data means importing the other slice's `core/` service, which is fine and expected.

## Build order

Build outside-in from the contract. Each step is checkable before the next, so a mistake in the
contract surfaces before it has been copied into six templates.

1. **Models** — `core/<domain>/<singular>.models.ts`. One interface per request/response shape, named
   after the API's own names (`CareSettingResponse`, `CreateCareSettingRequest`,
   `UpdateCareSettingRequest`). Nullable server fields are `T | null`, optional request fields are
   `field?: T`; these are different statements and conflating them causes real bugs at the boundary.
2. **Service** — `core/<domain>/<domain>.service.ts`. `@Injectable({ providedIn: 'root' })`, one
   private static `BASE` path, `inject(HttpClient)`, one method per endpoint returning `Observable<T>`.
   No state, no caching, no `subscribe` — the service is a typed description of the API surface, and
   keeping it that way is what makes it trivially testable and safely reusable.
3. **Service spec** — assert method, URL, and body for each endpoint. Cheap, and it pins the contract.
4. **Error map** — `features/<domain>/<singular>-errors.ts`. See "Errors" below.
5. **Components** — container first, then the presentational pieces it needs. See "Components".
6. **Component specs** — colocated, driven through the DOM. See `references/testing.md`.
7. **Route** — a lazy `loadComponent` entry in `app.routes.ts`, with the right guard.
8. **Nav** — one entry in the sidebar registry, if the screen is reachable from the menu.

`scripts/new_slice.py` stamps steps 1–6 as compiling skeletons with the right imports, headers, and
spec harnesses, and prints the route/nav snippets for 7–8. Run it first and fill in the bodies rather
than hand-typing boilerplate.

Invoke it from the Angular app's workspace root (the folder holding `src/`), pointing at this skill's own
`scripts/new_slice.py`. Resolve that from the skill directory you are reading this file in - the skill
may be installed personally (`~/.claude/skills/`) or in the project (`.claude/skills/`), so a hardcoded
project path will not resolve everywhere:

```bash
python <skill-dir>/scripts/new_slice.py --domain care-settings --singular care-setting --base-path /admin/care-settings --components care-setting-list,care-setting-editor
```

Pass `--dry-run` to see the file list first. It never overwrites an existing file, and it Prettier-formats
only the files it just created (`--no-format` opts out) — line wrapping depends on how long the generated
identifiers turn out to be, so no fixed template is clean for every domain name.

## Components

Split a slice's UI into a **container** and **presenters**, and let the split follow data ownership
rather than size:

- The **container** is what the route loads. It owns the fetch, the loading/error signals, filters,
  and any dialog it coordinates. It is the only place in the slice that calls the service for reads.
- **Presenters** take `input()`s and emit `output()`s. A presenter may call the service for its own
  write (an editor saving its own form is not worth threading through the container), but it reports
  the outcome upward with `output()` so the container can refetch.

Non-negotiable Angular idioms — these are current-Angular defaults, and mixing eras inside one slice
is what makes a codebase hard to read:

- Standalone components. Never set `standalone: true` (it is the default); never an `NgModule`.
- `changeDetection: ChangeDetectionStrategy.OnPush` on every component.
- `input()` / `output()` / `viewChild()` functions, never the `@Input`/`@Output`/`@ViewChild`
  decorators. No `@HostBinding` / `@HostListener` — use the decorator's `host` object.
- `inject()`, not constructor parameter injection.
- Signals for state, `computed()` for anything derived. Never recompute in the template what a
  `computed()` can hold, and never `mutate` a signal — `set` or `update`.
- Native control flow `@if` / `@for` / `@switch`; `*ngIf`/`*ngFor` and `ngClass`/`ngStyle` are out.
  Use `[class.x]` and `[style.x]` bindings.
- Reactive forms with `NonNullableFormBuilder`. Template-driven forms are out.
- Templates hold no logic beyond a signal call and a binding.

## Data fetching

Unless the codebase has already standardised on `resource()`/`httpResource()`, fetch with signals plus
an explicit subscription torn down by `takeUntilDestroyed(this.destroyRef)`:

```ts
readonly items = signal<CareSettingResponse[]>([]);
readonly loading = signal(false);
readonly error = signal<string | null>(null);

private load(): void {
  this.loading.set(true);
  this.error.set(null);
  this.service.list()
    .pipe(takeUntilDestroyed(this.destroyRef))
    .subscribe({
      next: (items) => { this.items.set(items); this.loading.set(false); },
      error: (err: unknown) => {
        this.error.set(problemMessage(err, 'Failed to load care settings.'));
        this.loading.set(false);
      },
    });
}
```

Three details that matter more than they look:

- `error: (err: unknown)` — typing it `any` is how untyped error objects leak into templates.
- Reset `error` at the *start* of every request, or a stale banner outlives the failure it described.
- Set `loading` to false on **both** paths. A spinner that survives an error is the single most
  common bug in hand-rolled fetch code.

Check the codebase before choosing: if slices already use `httpResource()` or `rxResource()`, follow
that instead of introducing a second convention. Consistency inside the app beats novelty.

## Errors

Server errors arrive as RFC 9457 problem details. Map them once per slice, keyed on the **slug** —
the last path segment of `type` — because the slug is a stable contract while `detail` is prose that
changes without warning:

```ts
/** Friendly messages for care-settings errors, keyed on the RFC 9457 problem `type` slug. */
export const CARE_SETTING_ERROR_MESSAGES: Readonly<Record<string, string>> = {
  'duplicate-care-setting': 'A care setting with that name already exists.',
  'care-setting-in-use': 'This care setting is used by feedback entries and cannot be deleted. Archive it instead.',
};
```

Then `problemMessage(err, 'Failed to save care setting.', CARE_SETTING_ERROR_MESSAGES)` at each call
site. Deliberately **omit** a slug whose server `detail` is more useful than any generic sentence you
could write — an error that names the specific step or file that blocked the operation is the only
thing that tells the user where to look, and overriding it with "Could not publish" destroys
information. Leave a comment saying so, or someone will "fix" the gap later.

If the app has no `problemMessage` helper yet, create one in `core/http/` — see
`references/conventions.md` for the implementation.

## Routing and nav

Every slice entry is lazy: `loadComponent: () => import('./features/<domain>/<c>/<c>').then((m) => m.C)`.
Eagerly importing a feature component into `app.routes.ts` silently pulls the whole slice into the
initial bundle. Attach the guard at the route, and comment any route whose public/guarded status is
surprising — an unguarded route reached from an emailed link needs a sentence explaining why, or a
future reader will "secure" it and break the flow.

Sidebar entries live in one registry (`layout/nav-items.ts` here) rather than being discovered from
routes, so ordering and grouping are explicit and reviewable.

## Reviewing a slice

When asked to review, audit, or clean up feature code, work through
`references/review-checklist.md` — it is ordered from structural violations (which force a move) down
to idiom violations (which are local edits). Report findings as file:line with the rule they break
and the fix, and do not flag a deviation that carries a comment explaining itself; a documented
exception is a decision, not a defect.

## References

Read these when the task calls for them; they are not needed for every invocation.

- `references/conventions.md` — the complete file-kind catalog, naming rules, layering rules, and the
  shared helpers a slice depends on (`problemMessage`, `Page<T>`, data-view). Read when deciding
  placement or naming, or when a helper the templates assume does not exist yet.
- `references/scaffold.md` — annotated, copyable templates for each file kind, with a fully worked
  CRUD slice. Read when writing a slice by hand or extending one.
- `references/testing.md` — service specs, component specs through the DOM, and fixture builders.
  Read before writing any spec.
- `references/review-checklist.md` — the ordered conformance checklist. Read when reviewing.
