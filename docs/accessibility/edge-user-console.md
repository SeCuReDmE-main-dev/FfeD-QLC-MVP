# Edge User Console

The SecuredMe Education site includes two public support controls for readers.

## Dark / Light mode

Use the `Dark` / `Light` button in the upper-right header to switch the whole site between the Education light and dark themes.

This button is separate from the accessibility console. It controls the MkDocs Material color palette and keeps the selected mode while users move between pages.

## Access console

Use the `Access` button in the lower-right corner, or press `Ctrl+U`, to open the self-hosted Access console.

The console is designed for edge users, neurodivergent students, hyperactive readers, teachers, older readers, and anyone who needs a calmer first week with the documentation. It stores settings only in the current browser through `localStorage`.

Keyboard controls:

| Shortcut | Action |
| --- | --- |
| `Ctrl+U` | Open or close the Access console. |
| `Escape` | Close the console. |
| `Ctrl+Alt+S` | Start or stop the sprint timer. |

## Profiles

| Profile | Purpose |
| --- | --- |
| Teacher Focus | Stronger link visibility, readable font, reduced motion, and current-section support. |
| Low Vision | Larger text, stronger contrast, smart contrast, and oversized controls. |
| Dyslexia Support | Readable font, wider spacing, horizontal reading pacer, and content chunking. |
| Motion Safe | Reduced motion, predictable transitions, and stronger panel contrast. |
| Neuro Focus | Focus frame, quiet navigation, chunked content, and current-section highlight. |
| ADHD Sprint | Focus frame, sprint rhythm, micro-breaks, low-demand mode, and reading pacer. |
| Autism Calm | Predictable mode, literal labels, calm layout, stimulus control, reduced motion, and quiet navigation. |
| Sensory Safe | Calm layout, stimulus control, reduced motion, smart contrast, and low-demand mode. |
| Deep Work / Hyperfocus | Focus frame, quiet navigation, current section, high-agency density, and 25-minute sprint length. |

## Core adjustments

| Control | Effect |
| --- | --- |
| Bigger Text | Cycles through three text-size levels. |
| Text Spacing | Adds more line, letter, and word spacing in content. |
| Contrast + | Strengthens foreground and background contrast. |
| Smart Contrast | Strengthens key interface panels without inverting the whole page. |
| Highlight Links | Adds strong outlines and underlines to links. |
| Readable Font | Uses a simpler system font stack. |
| Pause Animation | Minimizes page animation and transitions. |
| Oversized Widget | Enlarges the Access launcher and panel. |

## Neurodivergent comfort

| Control | Effect |
| --- | --- |
| Focus Frame | Softly de-emphasizes header, footer, and side navigation while anchoring the main content. |
| Quiet Nav | Keeps navigation available but visually quieter until hover or keyboard focus. |
| Calm Layout | Reduces glow, shadows, and high-energy decorative surfaces. |
| Stimulus Control | Lowers saturation and aggressive contrast without hiding content. |
| Content Chunking | Adds stronger section breaks and readable content width. |
| Current Section | Highlights the heading currently in view. |
| Reading Pacer | Cycles off, horizontal guide, and vertical guide. |
| Predictable Mode | Reduces transitions and keeps interface changes explicit. |
| Literal Labels | Keeps labels direct and avoids decorative casing transformations. |
| Glossary Boost | Highlights glossary and anchor links for technical terms. |

## Focus and hyperactivity

| Control | Effect |
| --- | --- |
| Sprint Timer | Starts or stops a local-only 5, 15, or 25 minute sprint. |
| Sprint Length | Cycles the sprint length between 5, 15, and 25 minutes. |
| Micro Breaks | Shows a calm break notice when a sprint ends. |
| Checklist Mode | Turns page headings into progress landmarks. |
| Done Marker | Marks the current section as done in this browser. |
| Resume Point | Stores the last active section locally. |
| Resume Last | Returns to the locally stored section. |
| Low Demand Mode | Reduces visual urgency on strong calls to action and warning surfaces. |
| High Agency Mode | Gives experienced users a denser reading mode for deep work. |
| Oversized Targets+ | Enlarges links, navigation targets, buttons, and Access controls. |

## Public boundary

This console is a reader-support layer, not a legal compliance certificate, not a medical tool, and not an automated remediation service. It does not send data to a third party, does not load a SaaS widget, and does not track users.

The implementation is static and self-hosted in the SecuredMe Education MkDocs site so future users can inspect, fork, and adapt it.
