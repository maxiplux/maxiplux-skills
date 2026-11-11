# Ben Shneiderman: eight golden rules of interface design

Author of this reference: max · Part of `design-principles-review-by-max`

Ben Shneiderman, a computer scientist at the University of Maryland Human-Computer Interaction Lab,
set these out in *Designing the User Interface: Strategies for Effective Human-Computer
Interaction*. Where Nielsen's list is an inspection checklist, Shneiderman's rules read as build
guidance for **interaction and dialog design**: how a sequence of actions should start, respond,
finish, fail and reverse.

The wording below follows the Interaction Design Foundation article listed under Sources. Later
editions of the book reword three rules; both wordings are given so that either can be cited.

IDs `S1`–`S8` are the ones cited in `rubric.md` and in findings.

## S1. Strive for consistency

Use the same icons, colors, menu hierarchy, calls to action and user flows for similar situations.
People can then apply what they learned in one part of the product to another.

- Check: one design language across screens; identical action sequences for similar tasks; the same
  terminology in menus, prompts and help.
- Article example: the Mac OS menu bar, which has kept the same graphic elements across decades of
  releases.
- Violations: each screen with its own button style; different flows for "add" in two modules.

## S2. Enable frequent users to use shortcuts

As people gain experience they want faster ways to finish tasks.

- Later wording: **Seek universal usability**: design for novices and experts, different ages,
  disabilities and devices. Shortcuts for experts are one part of it.
- Check: keyboard shortcuts, accelerators, command palettes, gestures with a visible alternative,
  defaults and recent values.
- Article example: copy and paste with Command-C and Command-V, and Command-Shift-3 for a
  screenshot, in place of mouse clicks.
- Violations: mouse-only data entry; no way to repeat or batch a frequent action.

## S3. Offer informative feedback

People should know where they are and what is happening at all times. Every action gets
appropriate, human-readable feedback within a reasonable time. Frequent, minor actions get a modest
response; rare, major actions get a substantial one.

- Check: response to every click, tap and submit; position shown in multi-step flows; selected and
  dragged states.
- Article examples: showing which page of a multi-page questionnaire the user is on (good); a file
  highlighting when clicked and a folder following the pointer while dragged (good); an error dialog
  that shows only an error code (bad).
- Violations: no selected state; a submit with no visible result; feedback written for developers.

## S4. Design dialogue to yield closure

Do not leave people guessing. Sequences of actions have a beginning, a middle and an end, and the
end tells them what their action led to.

- Check: a confirmation screen or message after every completed flow; a reference (order number,
  receipt, link) where one exists; a clear next step.
- Article examples: a "Thank you" message and receipt after an online purchase; an installer that
  shows the current step.
- Violations: a form that resets with no message; a payment flow that returns to the home screen
  with no confirmation.

## S5. Offer simple error handling

Design the system so that people cannot make serious errors. Where errors still happen, give
simple, step-by-step instructions to recover. Messages are gentle and never punish the user.

- Later wording: **Prevent errors**.
- Check: invalid choices disabled or absent; the field in error marked, with the reason and the fix;
  calm wording.
- Article examples: flagging the fields left blank in a form (good); a message that explains what
  happened and why, and makes clear the user is in control (good); a message using "fatal" and
  "terminated" (bad).
- Violations: alarming or blaming language; an error with no path forward.

## S6. Permit easy reversal of actions

Offer obvious ways to undo, whether for a single action, a data entry, or a whole sequence. Knowing
that errors can be undone relieves anxiety and encourages people to explore.

- Check: undo for edits and deletes; back in multi-step flows without losing entries; restore from
  trash or archive; edit after submit where the domain allows it.
- Article example: an installer that lets the user step back to correct wrong information instead of
  starting again.
- Violations: permanent delete with no recovery; a back step that clears the form.

## S7. Support internal locus of control

People should be the ones who start actions and should feel in charge of what happens. The system
behaves as they expect.

- Later wording: **Keep users in control**.
- Check: no surprise navigation, focus changes or auto-submits; the user can stop, quit or skip; no
  tedious forced sequences; settings are respected.
- Article examples: force-quitting an unresponsive program from Activity Monitor; an installer that
  lets the user choose to continue or exit.
- Violations: content that moves or reloads on its own; a forced tour; auto-playing media with no
  controls.

## S8. Reduce short-term memory load

Human attention is limited and people hold only about five items in short-term memory. Keep displays
simple, use a clear information hierarchy, and prefer recognition to recall.

- Check: information needed for a decision is on the same screen; lists are chunked; choices per
  view are limited; nothing has to be memorized between screens.
- Article example: the iPhone's main bottom bar holding only four app icons, unchanged across iOS
  versions.
- Violations: a code shown on one screen and typed on another; long ungrouped menus; multi-page
  forms that never show what was entered.

## Sources

- Euphemia Wong, "Shneiderman's Eight Golden Rules Will Help You Design Better Interfaces",
  Interaction Design Foundation:
  <https://ixdf.org/literature/article/shneiderman-s-eight-golden-rules-will-help-you-design-better-interfaces>
- Ben Shneiderman, "The Eight Golden Rules of Interface Design":
  <https://www.cs.umd.edu/users/ben/goldenrules.html>
