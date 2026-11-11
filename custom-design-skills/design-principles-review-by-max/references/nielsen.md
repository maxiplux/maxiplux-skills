# Jakob Nielsen: ten usability heuristics

Author of this reference: max · Part of `design-principles-review-by-max`

Developed by Jakob Nielsen with Rolf Molich in 1990 and refined by Nielsen in 1994. They are rules
of thumb, not specifications, and they are the standard basis for a **heuristic evaluation**: an
inspector walks the interface and records every place a heuristic is broken. This skill's evaluate
mode is that method, extended with the other three sources.

IDs `N1`–`N10` are the ones cited in `rubric.md` and in findings.

## N1. Visibility of system status

The design keeps people informed about what is going on, through appropriate feedback within a
reasonable time.

- Check: pressed and busy states on buttons; progress for anything slower than about a second;
  current location shown in navigation; saved/unsaved state visible; results of an action shown
  where the user is looking.
- Violations: a click with no visible response; a spinner with no end and no message; a silent
  failure; a background save with no indication.

## N2. Match between the system and the real world

The design speaks the users' language, with words and concepts familiar to them, in a natural and
logical order.

- Check: labels and messages use the user's terms; dates, numbers and currency are in the user's
  format; information follows the order of the real task.
- Violations: internal names, database fields or status codes on screen ("ERR_422", "entity",
  "null"); steps ordered by how the system stores data instead of how people work.

## N3. User control and freedom

People often act by mistake. They need a clearly marked "emergency exit" to leave the unwanted
state without an extended process.

- Check: undo and redo; cancel on every dialog and long operation; a working back button; closing a
  modal with Escape or a visible close control; leaving a flow without losing work.
- Violations: a wizard with no back step; a modal that can only be closed by completing it;
  irreversible actions with no warning; browser back that breaks the app's state.

## N4. Consistency and standards

People should not have to wonder whether different words, situations or actions mean the same
thing. Follow platform and industry conventions.

- Check: one name per concept; the same component for the same job; controls placed where the
  platform puts them; standard icons used with their standard meaning.
- Violations: "Delete", "Remove" and "Discard" used for one action; primary button on the left on
  one screen and the right on another; a custom control that behaves unlike the native one.

## N5. Error prevention

Good error messages matter, but the best designs stop the problem from happening.

- Check: constrained inputs (pickers, input types, masks); sensible defaults; confirmation before
  destructive actions; destructive controls kept apart from frequent ones; inline validation before
  submit.
- Violations: free text where a choice would do; "Delete" beside "Save" with the same style; a
  form that accepts input it will reject later; targets too small or too close to tap reliably.

## N6. Recognition rather than recall

Make elements, actions and options visible. People should not have to remember information from
one part of the interface to another.

- Check: visible labels (not placeholders alone); recent and suggested items; context carried
  across steps; examples of the expected format shown beside the field.
- Violations: codes the user must remember and retype; a hidden gesture as the only way to reach
  an action; a summary step that omits what was entered earlier.

## N7. Flexibility and efficiency of use

Shortcuts, hidden from novices, speed up the interaction for experts, so the design serves both.

- Check: keyboard shortcuts; bulk actions; saved filters and templates; remembered preferences;
  autofill and sensible input types.
- Violations: a repeated task that takes the same many clicks every time; no keyboard path
  through a data-entry form; no way to act on several items at once.

## N8. Aesthetic and minimalist design

Interfaces should not contain information that is irrelevant or rarely needed. Every extra unit of
information competes with the relevant ones.

- Check: one clear primary action; secondary detail behind progressive disclosure; visual weight
  matching importance.
- Violations: dense screens where everything is emphasized; decorative graphics crowding the
  content; long instructions nobody needs.

## N9. Help users recognize, diagnose, and recover from errors

Error messages are in plain language, state the problem precisely, and suggest a solution.

- Check: message beside the field or cause; what went wrong and how to fix it; input preserved;
  a retry or alternative offered; no blame.
- Violations: "Something went wrong"; a raw code or stack trace; a form cleared after a failed
  submit; a red border with no text.

## N10. Help and documentation

It is best if the system needs no explanation. When help is needed, it is easy to search, focused
on the user's task, concrete, and short.

- Check: contextual hints at the point of need; searchable help; onboarding that can be skipped
  and reopened; empty states that explain the first step.
- Violations: help only as a separate PDF; tooltips as the only place essential information
  lives; onboarding that cannot be dismissed.

## Severity scale

Nielsen's 0–4 rating is the severity scale used for **all** findings in this skill, whichever
framework they come from. It is defined once, in `rubric.md`.

## Source

Jakob Nielsen, "10 Usability Heuristics for User Interface Design", Nielsen Norman Group:
<https://www.nngroup.com/articles/ten-usability-heuristics/>
