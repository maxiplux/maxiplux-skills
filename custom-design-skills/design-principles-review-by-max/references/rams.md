# Dieter Rams: ten principles of good design

Author of this reference: max · Part of `design-principles-review-by-max`

Dieter Rams led design at Braun from 1961 to 1995. He wrote these principles to answer his own
question, "Is my design good design?" They were written for physical products, so each one is
translated here into something you can observe in a screen or a flow. Rams judges the **product as a
whole**: whether it deserves to exist in this form. Use him for the questions the usability lists do
not ask: honesty, restraint, longevity, care, and resource use.

IDs `R1`–`R10` are the ones cited in `rubric.md` and in findings.

| ID | Good design… | In a digital product this means | Signs of a violation |
| --- | --- | --- | --- |
| R1 | is innovative | New technology or interaction is used because it makes the task easier, never for its own sake. | A novel control replaces a standard one and is slower to use; a feature exists to look modern (chat widget, AI button, 3D scene) with no task behind it. |
| R2 | makes a product useful | The screen serves a real task, completely. Functional, psychological and aesthetic needs are met, and anything that detracts is left out. | The main task takes more steps than it needs; required information is missing from the screen where the decision is made; features nobody asked for crowd the ones people use. |
| R3 | is aesthetic | Visual quality is part of usefulness: clear hierarchy, considered typography, consistent spacing, calm color. | No clear focal point; many type sizes and weights; uneven spacing; clashing or arbitrary colors; misaligned elements. |
| R4 | makes a product understandable | The interface explains itself. Structure is visible, and controls say what they do. | A first-time user cannot tell what the screen is for or what to do next; icon-only controls with no label; a tutorial is needed for a basic task. |
| R5 | is unobtrusive | The product is a tool. It leaves room for the user's content and intent and does not ask for attention. | Modals or prompts on load; chrome larger than content; animation, badges or banners that pull attention away from the task. |
| R6 | is honest | It does not make the product seem more capable or valuable than it is, and does not manipulate. | Dark patterns (confirmshaming, pre-ticked consent, fake urgency or scarcity, hidden costs, hard-to-find cancel); progress bars that are not tied to real progress; "Saved" shown before the save succeeds. |
| R7 | is long-lasting | It avoids fashion, so it does not look dated, and it is built on a system that can be maintained. | Trend effects that reduce legibility (low-contrast text on blur, extreme rounding, novelty fonts); one-off styles instead of tokens and shared components. |
| R8 | is thorough down to the last detail | Nothing is left to chance. Every state and edge case is designed. | Missing empty, loading, error, disabled or focus states; text truncated without a way to read it; broken layouts with long names, zero items, or large numbers. |
| R9 | is environmentally friendly | It conserves resources over its life: bytes, energy, battery, the user's time and attention. | Multi-megabyte images or video for decoration; autoplay media; heavy scripts for small effects; constant animation; no dark theme where the platform supports one. |
| R10 | is as little design as possible | Less, but better. Only the essential remains, so the essential is clear. | Several competing primary actions; decorative elements with no function; repeated information; options shown that most users never need. |

## How to judge these

- **Ask "what would be lost if this were removed?"** for each element (R10, R5). If the answer is
  "nothing the user needs", it is a finding.
- **Check claims against behavior** (R6). Read the copy, then confirm the product does what the
  copy says. Check consent, pricing, cancellation and deletion flows first, because that is where
  manipulation usually lives.
- **Stress the layout** (R8). Try long text, no data, many items, an error, a slow network.
- **Look at the build, not only the screen** (R7, R9). Token use, shared components, asset sizes and
  motion settings are visible in code and in the network panel, not in a screenshot.

## Limits

R1, R3 and R7 involve taste. Report them only with a concrete observation and its effect on the
user's task ("three type sizes within 2px of each other make the hierarchy unreadable"), never as a
preference ("looks dated"). R9 has no pass mark; report what is clearly wasteful.

## Source

Dieter Rams, "Ten principles for good design", published by Vitsœ:
<https://www.vitsoe.com/gb/about/good-design>
