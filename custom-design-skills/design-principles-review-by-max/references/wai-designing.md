# W3C WAI: designing for web accessibility

Author of this reference: max · Part of `design-principles-review-by-max`

The W3C Web Accessibility Initiative publishes ten "Tips for Getting Started" for user interface
and visual design. Each tip links to the WCAG success criteria it supports. They apply to mobile
apps as well as the web; platform specifics are in `mobile.md`, `flutter.md` and
`native-ios-android.md`.

**Scope.** WAI describes the tips as an introduction: "a few of the things you need to consider".
Passing all ten is **not** WCAG conformance. Say so in every report, and recommend a full WCAG audit
when the product has a conformance obligation.

IDs `W1`–`W10` are the ones cited in `rubric.md` and in findings. Criteria numbers are WCAG 2.1/2.2.

## W1. Provide sufficient contrast between foreground and background

Text needs enough contrast against its background. This includes text on images, gradients and
buttons. Logos and incidental text are exempt.

- Thresholds: 4.5:1 for normal text; 3:1 for large text (at least 24px, or 18.66px bold). Also apply
  3:1 to UI component boundaries, icons that carry meaning, and focus indicators (1.4.11).
- Check: compute ratios with `scripts/contrast.py`. Check placeholder text, disabled-looking but
  active controls, text over images, and every theme.
- WCAG: 1.4.3 Contrast (Minimum); related 1.4.11 Non-text Contrast.

## W2. Don't use color alone to convey information

Color may carry meaning, but never as the only signal. Add a second cue that does not depend on
color perception.

- Check: required fields (asterisk or the word "required"); error states (icon and text); status
  badges (label); chart series (labels or patterns); links in body text (underline).
- WAI examples: required fields in red **and** marked with an asterisk; shapes referred to by number
  as well as color.
- WCAG: 1.4.1 Use of Color.

## W3. Ensure that interactive elements are easy to identify

Links and buttons have distinct styles, and their appearance changes on hover, keyboard focus, and
touch or click. Styles and names are used consistently. Keyboard users can reach every interactive
element and see which one has focus.

- Check: tab through the whole screen; every control is reachable, in a logical order, with a
  visible focus indicator; no `outline: none` without a replacement; nothing clickable that looks
  like plain text; controls with the same function share a name.
- WCAG: 2.4.7 Focus Visible; 3.2.4 Consistent Identification; related 2.1.1 Keyboard.

## W4. Provide clear and consistent navigation options

Navigation keeps the same naming, styling and position across pages. There is more than one way to
find content, such as search or a site map. Orientation cues, such as breadcrumbs and clear
headings, show where the user is.

- Check: same nav in the same place on every screen; current item marked; search or an index for
  larger products; page titles and headings that say where you are.
- WCAG: 3.2.3 Consistent Navigation; 2.4.5 Multiple Ways.

## W5. Ensure that form elements include clearly associated labels

Every field has a descriptive label placed next to it. In left-to-right languages labels usually sit
to the left of or above the field, and to the right of checkboxes and radio buttons. Avoid large
gaps between a label and its field.

- Check: a visible label for every input (a placeholder is not a label); the label is
  programmatically tied to the control (`<label for>`, `aria-labelledby`, or the platform
  equivalent); groups have a legend or group label.
- WCAG: 3.3.2 Labels or Instructions; 2.4.6 Headings and Labels; related 1.3.1 Info and
  Relationships, 4.1.2 Name, Role, Value.

## W6. Provide easily identifiable feedback

Give feedback for interactions: confirm a submission, alert the user when something goes wrong,
announce changes on the page. Instructions are easy to find. Feedback that needs action is
prominent.

- Check: errors listed and linked to their fields; each error shown beside its field with text and
  an icon, not color alone; success and status messages exposed to assistive technology (live region
  or the platform's announcement API); focus moved to the error summary or first invalid field.
- WAI example: an error list at the top of a form, each item linking to its field, with icon and
  background color making errors stand out.
- WCAG: 3.3.1 Error Identification; 3.3.2 Labels or Instructions; 3.3.3 Error Suggestion; related
  4.1.3 Status Messages.

## W7. Use headings and spacing to group related content

Whitespace and proximity show which content belongs together. Headings group content, reduce
clutter, and make scanning easier.

- Check: real heading elements in a sensible order with no skipped levels; one main heading per
  screen; related controls grouped by spacing; no long undivided blocks of text.
- WCAG: 2.4.6 Headings and Labels; 2.4.10 Section Headings; related 1.3.1 Info and Relationships.

## W8. Create designs for different viewport sizes

Consider how the page looks on a phone and in a zoomed browser window. Header and navigation may
move to use space well. Text size and line length stay readable.

- Check: 320 CSS px wide with no horizontal scrolling; 200% zoom with no loss of content; text
  resized by the user does not clip or overlap; both orientations work.
- WAI example: multiple columns and visible navigation in a wide window; a single column with
  navigation behind an icon in a narrow one.
- WCAG (not linked from the tip, but the relevant criteria): 1.4.10 Reflow; 1.4.4 Resize Text;
  1.3.4 Orientation.

## W9. Include image and media alternatives in your design

Leave room in the design for alternatives: visible links to transcripts, links to audio-described
versions of video, text alongside icons and graphical buttons, captions and descriptions for tables
and complex graphs.

- Check: meaningful images have text alternatives and decorative ones are hidden from assistive
  technology; icon-only buttons have accessible names; video has captions; audio has a transcript.
- WCAG: 1.1.1 Non-text Content; related 1.2.x Time-based Media.

## W10. Provide controls for content that starts automatically

Provide visible controls to stop animation and auto-playing sound. This covers carousels, image
sliders, background sound and video.

- Check: carousels have pause and slide-selection controls; nothing plays sound on load without a
  way to stop it; motion honors the user's reduced-motion setting; nothing flashes more than three
  times a second.
- WCAG: 1.4.2 Audio Control; 2.2.2 Pause, Stop, Hide; related 2.3.1 Three Flashes, 2.3.3 Animation
  from Interactions.

## Source

W3C Web Accessibility Initiative, "Designing for Web Accessibility – Tips for Getting Started"
(updated 16 July 2024): <https://www.w3.org/WAI/tips/designing/>. Criteria text: "How to Meet WCAG
(Quick Reference)", <https://www.w3.org/WAI/WCAG22/quickref/>.
