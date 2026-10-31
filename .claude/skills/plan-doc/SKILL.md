---
name: plan-doc
description: Create or update a planning doc in docs/ for the Stock Analyzer project, following the numbering, template, and navigation-link conventions. Use when adding a new planning topic or restructuring the docs.
---

# Plan Doc

Follow the conventions in `docs/00-how-to-plan.md`.

## ⚠️ Always: append, never renumber
- A new doc gets **the next number after the highest existing one** (`max(NN) + 1`). It is appended at the end.
- **Never renumber or rename an existing doc.** Renames break links and git history.
- The decision log is **not** numbered: it lives at `docs/decisions/open-questions.md` (stable path).
  New questions are appended to its table with the next `Q` number; numbers are never reused or reordered.
- Exception (only if the user explicitly asks to reorder): use `git mv`, then update every link, link text, title and the README row.

## 📐 Diagrams: always use Mermaid
- Every architecture, data-flow, sequence, deployment or state diagram must be a ` ```mermaid ` code block. Never draw ASCII-art boxes and arrows.
- Choose the type that fits:
  | Diagram | Mermaid type |
  |---|---|
  | System / component architecture | `flowchart LR` with `subgraph` groups |
  | Deployment / containers | `flowchart TB` |
  | Time-ordered jobs, request flows | `sequenceDiagram` |
  | Lifecycles (trades, jobs) | `stateDiagram-v2` |
  | Data model / tables | `erDiagram` |
  | Timelines / roadmap | `gantt` or `timeline` |
- Use `<br/>` for line breaks inside nodes, `[( )]` for databases, and dotted links (`-.->`) for optional parts.
- Keep node names the same as the real module/service names (e.g., `collector`, `worker`).
- Exceptions: folder trees, sample outputs and config files stay as plain code blocks.
- When the architecture changes, update the diagrams in `07-architecture.md` and `14-docker-deployment.md` too.

## Deliverables folder
- `docs/deliverables/` is **not** numbered and not part of the NN sequence. It has its own `README.md` index and nav (Docs index · Deliverables · Previous/Next phase).
- New phase → copy `docs/deliverables/TEMPLATE.md` to `phase-NN-<name>.md` and add a row to `docs/deliverables/README.md`.

## Decisions folder
- `docs/decisions/open-questions.md` is the single decision log. Its nav bar is `[🏠 Docs index](../README.md) · [🎯 Deliverables](../deliverables/README.md) · [🗺️ Roadmap](../09-roadmap.md)`.
- Links from numbered docs use `decisions/open-questions.md`; links inside it use `../` for everything else.

## Steps
1. Take the next number (`max(NN) + 1`) and a lowercase hyphenated name: `docs/NN-short-name.md`.
2. Write the content with the template from section 4 of `00-how-to-plan.md`: `# NN – Title`, a **Purpose** line, then sections built from tables and lists, then a **Related** list.
3. Append a row at the end of the index table in `docs/README.md`.
4. Append any new undecided items to `docs/decisions/open-questions.md` as `_TBD_`. Record decisions as ✅ with the chosen option and update every affected doc.
5. Update the navigation bars: the new doc gets `[← Previous](<old last doc>) · [🏠 Index](README.md)`, and the old last doc gets a `[Next →](<new doc>)` link (top and bottom). Each bar is a line starting with `<!-- nav -->`. No other doc changes.
6. Use relative links only. Check that every link target and `#anchor` exists (numbered docs, `deliverables/`, `decisions/`, `CLAUDE.md`), that every numbered doc is in the README, and that every numbered doc has a Related section.
