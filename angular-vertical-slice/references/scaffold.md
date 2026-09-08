# Scaffold reference

Copyable templates for each file kind, plus a fully worked CRUD slice. Read this when writing a slice
by hand or extending one. Placeholders: `<domain>` = kebab plural (`care-settings`), `<singular>` =
kebab singular (`care-setting`), `<Entity>` = PascalCase singular (`CareSetting`).

`scripts/new_slice.py` emits all of these pre-filled; use it and edit the bodies rather than retyping.

## Contents

- [1. Models](#1-models)
- [2. Service](#2-service)
- [3. Error map](#3-error-map)
- [4. Container component](#4-container-component)
- [5. Container template](#5-container-template)
- [6. Editor (presenter) component](#6-editor-presenter-component)
- [7. Route entry](#7-route-entry)
- [8. Nav entry](#8-nav-entry)
- [Worked example: reading an OpenAPI contract into a slice](#worked-example-reading-an-openapi-contract-into-a-slice)

## 1. Models

`core/<domain>/<singular>.models.ts`

```ts
/** Exact word the admin must type (and the API must receive) to delete an unused record. */
export const <ENTITY>_DELETE_CONFIRMATION = 'DELETED';

/** <Entity> DTOs mirroring the backend contract (see /admin/<domain>). */

export interface <Entity>Response {
  id: string;
  name: string;
  /** Null when the author left it blank — distinct from an absent field. */
  description: string | null;
  archived: boolean;
  displayOrder: number;
  /** All-time count of records referencing this one; drives the delete guard. */
  usages: number;
}

export interface Create<Entity>Request {
  name: string;
  description?: string | null;
  /** Create it archived. Omit/false for an active value. */
  archived?: boolean;
}

/** Partial update — omit a field to leave it unchanged. Send `archived` to archive/restore. */
export interface Update<Entity>Request {
  name?: string;
  description?: string | null;
  archived?: boolean;
}
```

Guidance that pays for itself later:

- `T | null` for a value the server sends as null; `field?: T` for a key the client may omit. They are
  different statements. Conflating them produces requests that clear fields the user never touched.
- Document any field whose meaning is not obvious from its name — counts, order fields, and flags that
  gate an action are the usual suspects.
- Contract constants (confirmation words, enum unions, page sizes the API enforces) belong here, next
  to the shapes they constrain, not in the component that happens to use them first.

## 2. Service

`core/<domain>/<domain>.service.ts`

```ts
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Create<Entity>Request, <Entity>Response, Update<Entity>Request } from './<singular>.models';

/**
 * Admin <domain> management (`/admin/<domain>`). Powers the <Domain> screen: the directory, the metric
 * cards, and the side editor's create / edit / archive-restore / delete actions.
 */
@Injectable({ providedIn: 'root' })
export class <Domain>Service {
  private readonly http = inject(HttpClient);
  private static readonly BASE = '/admin/<domain>';

  list(): Observable<<Entity>Response[]> {
    return this.http.get<<Entity>Response[]>(<Domain>Service.BASE);
  }

  get(id: string): Observable<<Entity>Response> {
    return this.http.get<<Entity>Response>(`${<Domain>Service.BASE}/${id}`);
  }

  create(body: Create<Entity>Request): Observable<<Entity>Response> {
    return this.http.post<<Entity>Response>(<Domain>Service.BASE, body);
  }

  update(id: string, body: Update<Entity>Request): Observable<<Entity>Response> {
    return this.http.patch<<Entity>Response>(`${<Domain>Service.BASE}/${id}`, body);
  }

  moveUp(id: string): Observable<<Entity>Response> {
    return this.http.post<<Entity>Response>(`${<Domain>Service.BASE}/${id}/move-up`, {});
  }

  /**
   * Hard-delete. Pass the confirmation word — the server rejects a bare delete with 409
   * `<singular>-delete-confirmation-required`, and an in-use record with 409 `<singular>-in-use`.
   */
  delete(id: string, confirmation?: string): Observable<void> {
    let params = new HttpParams();
    if (confirmation) {
      params = params.set('confirmation', confirmation);
    }
    return this.http.delete<void>(`${<Domain>Service.BASE}/${id}`, { params });
  }
}
```

The class doc is doing real work: it names the endpoint prefix and the screens the service powers, so
a reader arriving from a server log can orient in one line. Note also what is **absent** — no state,
no `subscribe`, no `map` into a view model, no error handling. Each of those would give the service a
second job and make it untestable in isolation.

Comment any endpoint whose response shape is surprising. "Every step call returns the whole module
rather than the step, so the editor re-renders from one payload" is the kind of note that stops the
next person from writing a stitching bug.

## 3. Error map

`features/<domain>/<singular>-errors.ts`

```ts
/**
 * Friendly messages for <domain> errors, keyed on the RFC 9457 problem `type` slug.
 *
 * `<singular>-not-publishable` is deliberately absent: its `detail` names the row that blocked the
 * action, which is the only thing that tells the user where to look, so `problemMessage` falls through
 * to the server sentence rather than replacing it with a generic one.
 */
export const <ENTITY>_ERROR_MESSAGES: Readonly<Record<string, string>> = {
  'duplicate-<singular>': 'A <singular> with that name already exists.',
  '<singular>-in-use': 'This <singular> is in use and cannot be deleted. Archive it instead.',
  '<singular>-already-first': 'This <singular> is already first.',
  '<singular>-already-last': 'This <singular> is already last.',
  '<singular>-delete-confirmation-required': 'Type DELETED to confirm deletion.',
};
```

Write the sentence the way a person would say it, and include the way out: "…cannot be deleted.
Archive it instead" beats "Conflict". Document the omissions, or someone will helpfully fill the gap
and throw away the server's specifics.

## 4. Container component

`features/<domain>/<singular>-list/<singular>-list.ts`

```ts
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable } from 'rxjs';

import { <ENTITY>_DELETE_CONFIRMATION, <Entity>Response } from '../../../core/<domain>/<singular>.models';
import { <Domain>Service } from '../../../core/<domain>/<domain>.service';
import { problemMessage } from '../../../core/http/problem-message';
import { ConfirmDialog } from '../../../shared/confirm-dialog/confirm-dialog';
import { <Entity>Editor } from '../<singular>-editor/<singular>-editor';
import { <ENTITY>_ERROR_MESSAGES } from '../<singular>-errors';

type StatusFilter = 'all' | 'active' | 'archived';

/**
 * <Domain> management. Combines summary metrics, a search/filter directory, and a standing side editor
 * for create / edit / archive-restore / delete. The list and editor stay visible together; deletes are
 * confirmed through the shared dialog.
 */
@Component({
  selector: 'app-<singular>-list',
  imports: [<Entity>Editor, ConfirmDialog],
  templateUrl: './<singular>-list.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class <Entity>List implements OnInit {
  private readonly service = inject(<Domain>Service);
  private readonly destroyRef = inject(DestroyRef);

  readonly items = signal<<Entity>Response[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly query = signal('');
  readonly statusFilter = signal<StatusFilter>('all');
  /** Id of the row whose action is in flight, so only that row's controls disable. */
  readonly actionInFlight = signal<string | null>(null);

  private readonly editor = viewChild.required(<Entity>Editor);
  private readonly deleteDialog = viewChild.required(ConfirmDialog);
  private readonly pendingDelete = signal<<Entity>Response | null>(null);

  /** Owned here rather than read from the editor, so the directory's first render does not touch a
   *  required viewChild that has not been created yet. */
  readonly selectedId = signal<string | null>(null);

  readonly filtered = computed<readonly <Entity>Response[]>(() => {
    const status = this.statusFilter();
    const q = this.query().trim().toLowerCase();
    return this.items().filter((item) => {
      if (status === 'active' && item.archived) return false;
      if (status === 'archived' && !item.archived) return false;
      if (!q) return true;
      return item.name.toLowerCase().includes(q)
        || (item.description?.toLowerCase().includes(q) ?? false);
    });
  });

  /** Reordering a filtered view would move a row past neighbours the user cannot see. */
  readonly reorderDisabled = computed(
    () => this.statusFilter() !== 'all'
      || this.query().trim().length > 0
      || this.actionInFlight() !== null,
  );

  ngOnInit(): void {
    this.load();
  }

  refresh(): void {
    this.load();
  }

  add(): void {
    this.selectedId.set(null);
    this.editor().openForCreate();
  }

  edit(item: <Entity>Response): void {
    this.selectedId.set(item.id);
    this.editor().openForEdit(item);
  }

  /** After a create/save/archive the editor holds the affected record — keep its row highlighted. */
  onEditorSaved(): void {
    this.selectedId.set(this.editor().selectedId());
    this.refresh();
  }

  onEditorClosed(): void {
    this.selectedId.set(null);
  }

  onDeleteRequested(item: <Entity>Response): void {
    this.pendingDelete.set(item);
    this.deleteDialog().open();
  }

  confirmDelete(): void {
    const item = this.pendingDelete();
    if (!item) {
      return;
    }
    this.service
      .delete(item.id, <ENTITY>_DELETE_CONFIRMATION)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.editor().reset();
          this.selectedId.set(null);
          this.pendingDelete.set(null);
          this.refresh();
        },
        error: (err: unknown) =>
          this.error.set(problemMessage(err, 'Failed to delete <singular>.', <ENTITY>_ERROR_MESSAGES)),
      });
  }

  private load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.service
      .list()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (items) => {
          this.items.set(items);
          this.loading.set(false);
        },
        error: (err: unknown) => {
          this.error.set(problemMessage(err, 'Failed to load <domain>.'));
          this.loading.set(false);
        },
      });
  }

  /** One shape for every single-record action, so in-flight state and error handling cannot drift. */
  private runAction(id: string, request$: Observable<unknown>, fallback: string): void {
    this.actionInFlight.set(id);
    this.error.set(null);
    request$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.actionInFlight.set(null);
        this.load();
      },
      error: (err: unknown) => {
        this.actionInFlight.set(null);
        this.error.set(problemMessage(err, fallback, <ENTITY>_ERROR_MESSAGES));
      },
    });
  }
}
```

`runAction` is the pattern to keep: move-up, move-down, set-default, archive and restore all have the
same lifecycle, and writing that lifecycle five times is how one of them ends up leaving the spinner
on after a failure.

Accessible labels for disabled controls deserve a computed helper rather than a static string —
"Clear filters to reorder Ambulatory clinic" tells a screen-reader user *why* the button is dead,
which a bare "Move up" does not.

## 5. Container template

`features/<domain>/<singular>-list/<singular>-list.html`

```html
@if (error(); as message) {
  <div role="alert" class="alert alert-error mb-4">{{ message }}</div>
}

<app-data-view [loading]="loading()" [isEmpty]="filtered().length === 0" loadingLabel="Loading <domain>">
  <div dataViewToolbar class="flex gap-2 p-4">
    <input
      type="search"
      class="input input-bordered"
      placeholder="Search <domain>"
      aria-label="Search <domain>"
      [value]="query()"
      (input)="query.set($any($event.target).value)"
    />
  </div>

  <p dataViewEmpty>No <domain> match your filters.</p>

  <table dataViewTable class="table">
    <thead>
      <tr><th scope="col">Name</th><th scope="col">Status</th><th scope="col">Actions</th></tr>
    </thead>
    <tbody>
      @for (item of filtered(); track item.id) {
        <tr [class.bg-base-200]="selectedId() === item.id">
          <td>{{ item.name }}</td>
          <td>{{ item.archived ? 'Archived' : 'Active' }}</td>
          <td>
            <button type="button" class="btn btn-sm" (click)="edit(item)">
              Edit<span class="sr-only"> {{ item.name }}</span>
            </button>
          </td>
        </tr>
      }
    </tbody>
  </table>
</app-data-view>

<app-<singular>-editor
  (saved)="onEditorSaved()"
  (closed)="onEditorClosed()"
  (deleteRequested)="onDeleteRequested($event)"
/>
```

- `track item.id` on every `@for`. Tracking by index re-renders rows on any reorder and loses focus.
- Repeated controls need a distinguishing accessible name — five buttons all called "Edit" are
  unusable by keyboard and screen reader alike.
- `@if (error(); as message)` reads the signal once and binds it; calling `error()` twice in a
  template is a smell even though signals make it cheap.

## 6. Editor (presenter) component

Key structure only — the full pattern is long, and the shape is what matters.

```ts
type EditorMode = 'idle' | 'create' | 'edit';

/**
 * The standing side editor. Unlike a modal it is always mounted beside the directory and rests on a
 * "Choose an item to edit" prompt. Create and edit are driven imperatively via openForCreate/openForEdit;
 * the container reacts to `saved` to refresh, to `deleteRequested` to confirm, and to `closed` to clear
 * the selected row.
 *
 * Because it is a plain <aside> and not a native <dialog>, it does not get focus management for free,
 * so it moves focus to the first field on open and back to the Add button when it rests.
 */
@Component({
  selector: 'app-<singular>-editor',
  imports: [ReactiveFormsModule],
  templateUrl: './<singular>-editor.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class <Entity>Editor {
  private readonly service = inject(<Domain>Service);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  /** Emitted after a create, save, archive, or restore succeeds — the container reloads the directory. */
  readonly saved = output<void>();
  /** Emitted when the user asks to delete the open record — the container confirms, then deletes. */
  readonly deleteRequested = output<<Entity>Response>();
  /** Emitted when the editor is dismissed back to idle — the container clears its selected row. */
  readonly closed = output<void>();

  private readonly mode = signal<EditorMode>('idle');
  private readonly editing = signal<<Entity>Response | null>(null);

  readonly isIdle = computed(() => this.mode() === 'idle');
  readonly isSubmitting = signal(false);
  readonly errorMessage = signal<string | null>(null);

  readonly form = this.fb.group({
    name: this.fb.control('', Validators.required),
    description: this.fb.control(''),
    active: this.fb.control(true),
  });

  /** The id open for edit, or null in create/idle — lets the container track selection. */
  selectedId(): string | null {
    return this.editing()?.id ?? null;
  }

  submit(): void {
    if (this.isSubmitting()) {
      return;
    }
    this.errorMessage.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { name, description } = this.form.getRawValue();
    const editing = this.editing();
    const request$ = editing
      // Always send description (possibly "") so clearing the field clears the value server-side.
      ? this.service.update(editing.id, { name: name.trim(), description: description.trim() })
      : this.service.create({
          name: name.trim(),
          ...(description.trim() ? { description: description.trim() } : {}),
        });

    this.isSubmitting.set(true);
    request$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (saved) => {
        this.isSubmitting.set(false);
        this.openForEdit(saved);   // a freshly created record opens as EDIT
        this.saved.emit();
      },
      error: (err: unknown) => {
        this.errorMessage.set(problemMessage(err, 'Failed to save.', <ENTITY>_ERROR_MESSAGES));
        this.isSubmitting.set(false);
      },
    });
  }
}
```

Points that generalise:

- **Every `output()` carries a doc comment saying what the container should do.** These are the
  slice's internal API; undocumented outputs get wired to the wrong handler.
- **Guard re-entry** (`if (this.isSubmitting()) return;`). Double-submit is the default behaviour of
  an unguarded button under a slow network.
- **Own the create-vs-update decision in one place** and build the request body inline with spreads,
  so an optional field that should be omitted is visibly omitted.
- **Reset error state at the start of the action**, not at the end of the previous one.
- **Focus is the presenter's job.** A non-`<dialog>` panel gets no focus management from the browser;
  move focus in on open and back to the invoking control on rest.

## 7. Route entry

`app.routes.ts`

```ts
{
  path: 'admin/<domain>',
  title: '<Domain>',
  canActivate: [adminGuard],
  loadComponent: () =>
    import('./features/<domain>/<singular>-list/<singular>-list').then((m) => m.<Entity>List),
},
```

Detail routes sit as siblings with the parameter in the path (`admin/<domain>/:id/steps`), not as
children, unless a parent component actually renders a shared shell around them.

Comment any route whose guarding is not self-evident: a public, unguarded route reached from an
emailed link needs a sentence explaining that the recipient is by definition not signed in, or a
future reader will "secure" it and break the flow.

## 8. Nav entry

```ts
{ label: '<Domain>', icon: '<material-symbol>', path: '/admin/<domain>', group: 'program-setup' },
```

Declare the group on the item rather than inferring it from array position — slicing a nav array by
index silently misclassifies every item after the first reorder.

## Worked example: reading an OpenAPI contract into a slice

When the API is specified (an `openapi.json`, a spec document, or an existing controller):

1. **Find the tag** that groups the endpoints — it usually names the slice. `Admin: Care settings` →
   `core/care-settings/` + `features/care-settings/`.
2. **Transcribe schemas to interfaces verbatim.** Keep the server's names. Mark `nullable: true` as
   `| null` and non-`required` request properties as `?`.
3. **One service method per operation**, named after the operation not the verb: `moveUp`, `publish`,
   `setDefault` — not `postMoveUp`.
4. **Harvest the error slugs** from the documented 4xx responses into the error map. Endpoints that
   return a 409 with a specific `detail` are the ones to deliberately leave unmapped.
5. **Note response shape surprises** in the service doc — an action returning the whole aggregate, or
   the whole collection, changes how the component re-renders and is worth one sentence.
6. **Then** build the UI. The contract, not the mockup, decides what the slice can show.
