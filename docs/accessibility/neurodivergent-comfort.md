# Neurodivergent Comfort

SecuredMe Education treats accessibility as a public learning surface. The Access console supports comfort, attention, predictability, and user agency for neurodivergent readers without adding third-party tracking or medical claims.

The design is grounded in W3C cognitive accessibility guidance: clear purpose, understandable structure, support for focus, reduced memory burden, predictable navigation, and personalization. These controls supplement WCAG work; they do not replace manual accessibility review or user testing.

## Research translation

| Need | Feature | CSS/JS contract | Validation test |
| --- | --- | --- | --- |
| Reduce distraction while keeping controls reachable | Focus Frame | `focusFrame`, `.se-a11y-focus-frame` | Main content receives a visible frame; nav/header remain available. |
| Keep navigation predictable but less visually loud | Quiet Nav | `quietNav`, `.se-a11y-quiet-nav` | Side nav fades until hover or keyboard focus. |
| Reduce sensory overload | Calm Layout | `calmLayout`, `.se-a11y-calm-layout` | Glow, shadow, and decorative intensity are reduced. |
| Reduce aggressive saturation | Stimulus Control | `stimulusControl`, `.se-a11y-stimulus-control` | Main surfaces become calmer without hiding text. |
| Help readers parse long pages | Content Chunking | `contentChunking`, `.se-a11y-content-chunking` | Headings get stronger breaks and content width stays readable. |
| Help users know where they are | Current Section | `currentSection`, `.se-a11y-current-section` | The active heading is highlighted while scrolling. |
| Support dyslexia and attention tracking | Reading Pacer | `readingPacer`, `.se-a11y-pacer-horizontal`, `.se-a11y-pacer-vertical` | Pacer cycles off, horizontal, vertical. |
| Support autism and anxiety through stable UI | Predictable Mode | `predictableMode`, `.se-a11y-predictable-mode` | Transitions and animation are minimized. |
| Avoid metaphor-heavy labeling | Literal Labels | `literalLabels`, `.se-a11y-literal-labels` | Controls keep direct labels and no decorative casing transformation. |
| Help technical vocabulary discovery | Glossary Boost | `glossaryBoost`, `.se-a11y-glossary-boost` | Glossary and anchor links become visually discoverable. |
| Turn reading into visible progress | Checklist Mode | `checklistMode`, `.se-a11y-checklist-mode` | Headings show checklist markers. |
| Preserve progress locally | Done Marker | `doneMarker`, `completedSections` | Current section can be marked done and survives reload. |
| Reduce memory burden | Resume Point | `resumePoint`, `lastSection` | Last active section can be resumed locally. |
| Support ADHD activation | Sprint Timer | `sprintMinutes`, `sprintRunning`, `sprintEndAt` | 5/15/25 minute timer runs locally and updates every second. |
| Support transition out of hyperfocus | Micro Breaks | `microBreaks`, `.se-a11y-break` | Break notice appears after a completed sprint. |
| Reduce pressure for anxious readers | Low Demand Mode | `lowDemandMode`, `.se-a11y-low-demand` | Strong CTAs and warning surfaces become less urgent visually. |
| Support 2e or expert users | High Agency Mode | `highAgencyMode`, `.se-a11y-high-agency` | Dense tables and deep-work mode stay available. |
| Support dyspraxia and motor precision differences | Oversized Targets+ | `oversizedTargets`, `.se-a11y-oversized-targets` | Buttons, links, and nav targets become larger. |

## Profiles

| Profile | Best first use |
| --- | --- |
| Neuro Focus | A reader gets distracted by navigation or decorative surfaces. |
| ADHD Sprint | A reader needs short activation loops, a timer, and a visible next step. |
| Autism Calm | A reader needs predictable labels, fewer stimuli, and low surprise. |
| Sensory Safe | A reader is overloaded by motion, saturation, or high-energy visuals. |
| Deep Work / Hyperfocus | A high-agency reader wants a quieter environment for long technical work. |

## Implementation boundary

The console is self-hosted JavaScript and CSS. It uses browser-local settings only:

- `securedme:a11y:v2` for Access settings.
- Local migration from `securedme:a11y:v1`.
- No SaaS widget.
- No CDN.
- No analytics event.
- No medical inference.
- No personal data collection.

## QA checklist

- Open `Access` with the launcher and `Ctrl+U`.
- Confirm `Escape` closes the panel.
- Apply each neuro profile and verify visible state.
- Start and stop the sprint timer with the button and `Ctrl+Alt+S`.
- Switch pages with MkDocs instant navigation and confirm the widget does not duplicate.
- Reload the page and confirm settings persist.
- Confirm dark/light mode remains separate from Access.
- Confirm mobile layout has no overlap and targets remain usable.
