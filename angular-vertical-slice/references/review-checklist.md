# Slice conformance checklist

Use when reviewing, auditing, or cleaning up Angular feature code. Ordered from **structural**
violations (which force files to move and are worth blocking on) down to **idiom** violations (local
edits, usually a one-line fix). Report findings as `file:line`, the rule broken, and the fix.

Two things before you start:

- **A documented exception is a decision, not a defect.** If a deviation carries a comment explaining
  why, do not flag it — flag it only if the reasoning is actually wrong, and say why.
- **Do not report what a linter or the compiler already catches.** Unused imports and missing types
  are not review findings.

## A. Structure — blocking

- [ ] The slice exists as `core/<domain>/` + `features/<domain>/` (or wholly under `features/<domain>/`
      for a genuinely single-consumer capability), not spread across type-based folders.
- [ ] `core/<domain>/` contains no template, no CSS, no component.
- [ ] Nothing in `core/` imports from `features/`, `shared/`, or `layout/`.
- [ ] No `features/<a>` file imports from `features/<b>`.
- [ ] Shared UI lives in `shared/` and its public API mentions no domain type.
- [ ] No barrel `index.ts` re-exporting the slice.
- [ ] Cross-slice helpers that ended up duplicated in two slices are either promoted or deliberately
      left duplicated with a note — not silently diverging.

## B. Data layer

- [ ] Service is `@Injectable({ providedIn: 'root' })` and holds **no** state, cache, or subscription.
- [ ] One method per endpoint, returning `Observable<T>`; named for the operation (`publish`,
      `moveUp`), not the verb (`postPublish`).
- [ ] Base path is one private static constant, not repeated string literals.
- [ ] DTO names mirror the API's own names, `Request`/`Response` suffixes intact.
- [ ] Nullable server fields are `T | null`; optional request fields are `field?: T`. These are not
      interchangeable.
- [ ] No `any` anywhere in the models or service.
- [ ] Contract constants (confirmation words, enum unions) live in the models file.
- [ ] Endpoints with a surprising response shape carry a comment saying so.

## C. Components

- [ ] Standalone; `standalone: true` is **not** written out (it is the default).
- [ ] `changeDetection: ChangeDetectionStrategy.OnPush` on every component.
- [ ] `input()` / `output()` / `viewChild()` functions — no `@Input`, `@Output`, `@ViewChild`,
      `@HostBinding`, `@HostListener`.
- [ ] `inject()` rather than constructor parameter injection.
- [ ] State in `signal()`, everything derived in `computed()` — no derived value recomputed in the
      template or stored in a plain field.
- [ ] No `mutate` on a signal.
- [ ] Native `@if` / `@for` / `@switch`; every `@for` has `track` on a stable id, not index.
- [ ] `[class.x]` / `[style.x]` bindings — no `ngClass`, no `ngStyle`.
- [ ] Reactive forms via `NonNullableFormBuilder` — no template-driven forms.
- [ ] The container owns reads; presenters take `input()`s and report via `output()`.
- [ ] Every `output()` has a doc comment saying what the container should do in response.
- [ ] Business rules used by two components in the slice have been lifted to a slice-root helper.
- [ ] Component file has a class-level doc comment saying what screen it is and how it is driven.

## D. Async and error handling

- [ ] Every subscription is torn down — `takeUntilDestroyed(this.destroyRef)` or an equivalent.
- [ ] `loading` is set false on **both** the success and error paths.
- [ ] `error` is cleared at the **start** of each request, not only on success.
- [ ] Error callbacks are typed `(err: unknown)`, never `any`.
- [ ] Server errors go through `problemMessage(err, fallback, SLICE_ERROR_MESSAGES)` — no raw
      `err.message`, no `JSON.stringify(err)` in a template.
- [ ] The slice has its own `<singular>-errors.ts` keyed on RFC 9457 slugs, not on `detail` prose,
      not on HTTP status alone.
- [ ] Slugs deliberately omitted from the map (because the server `detail` is more specific) are
      documented as such.
- [ ] Repeated single-record actions share one `runAction`-style helper rather than five copies of
      the same lifecycle.
- [ ] Actions guard against re-entry while in flight.

## E. Routing and nav

- [ ] Route uses `loadComponent` with a dynamic `import` — no eager import of a feature component in
      the routes file.
- [ ] The correct guard is attached, and any surprising public/guarded status is commented.
- [ ] `title` is set on the route.
- [ ] Sidebar entry declares its group explicitly rather than relying on array position.

## F. Accessibility

- [ ] Interactive elements are real `<button>` / `<a>` — no `(click)` on a `<div>`.
- [ ] Every form control has an associated `<label>` or `aria-label`.
- [ ] Repeated row controls have distinguishing accessible names ("Edit Ambulatory clinic", not five
      buttons all called "Edit").
- [ ] A disabled control's accessible name explains **why** it is disabled when the reason is not
      visible on screen.
- [ ] Error banners are `role="alert"`; busy indicators have an accessible label.
- [ ] Non-`<dialog>` panels manage focus themselves — in on open, back to the invoking control on close.
- [ ] Tables use `<th scope="col">`; icon-only buttons carry text for screen readers.

## G. Tests

- [ ] Service spec asserts method, URL, and body for each endpoint.
- [ ] `afterEach(() => httpMock.verify())` is present in every spec that mocks HTTP.
- [ ] Component specs query by role, accessible name, or visible text — not by CSS class, not by
      private member.
- [ ] There is a spec for at least one **mapped server error** surfacing in the UI.
- [ ] Fixtures use fixed ISO timestamps, never `new Date()`.
- [ ] Pure slice-root helpers are tested directly, not exclusively through a rendered component.
- [ ] No placeholder or skipped tests, no `// add assertions here`.

## Reporting

Order findings by section (A first), and for each give:

```
features/care-settings/care-setting-list/care-setting-list.ts:88
  D — `loading` stays true when the list request fails, so the spinner survives the error.
  Fix: set `this.loading.set(false)` in the error callback alongside the message.
```

If the slice is clean, say so plainly and name the two or three things it does well — a review that
only ever produces defects trains people to route around it.
