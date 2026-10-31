---
name: plan-doc
description: Create or update a planning doc in docs/ for the Stock Analyzer project, following the numbering, template, and navigation-link conventions. Use when adding a new planning topic or restructuring the docs.
---

# Plan Doc

Follow the conventions in `docs/00-how-to-plan.md`.

## ⚠️ Always: Open Questions is the last file
`NN-open-questions.md` must **always** have the highest number in `docs/`.
- To add a new doc, give it the number Open Questions has now, then renumber Open Questions to the next number (e.g., if Open Questions is `NN`, the new doc becomes `NN-…` and Open Questions becomes `NN+1`).
- After renumbering, update **every** reference: links in all docs, link text like `[13](13-…)`, the `# NN –` title, the README index row, and this skill file.
- Never add a doc numbered after Open Questions.

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

## Steps
1. Choose the number following the rule above, and a lowercase hyphenated name: `docs/NN-short-name.md`.
2. Write the content with the template from section 4 of `00-how-to-plan.md`: `# NN – Title`, a **Purpose** line, then sections built from tables and lists, then a **Related** list.
3. Add a row to the index table in `docs/README.md`, keeping rows in number order with Open Questions last.
4. Add any new undecided items to the Open Questions doc as `_TBD_`. Record decisions as ✅ with the chosen option.
5. Rebuild the navigation bars on every doc. Each bar is a line starting with `<!-- nav -->`, at both the top and the bottom of the file, in the form `[← Previous](..) · [🏠 Index](README.md) · [Next →](..)`, using files sorted by name. The last file (Open Questions) has no Next link.
6. Use relative links only. Check that every link target and `#anchor` exists, that every doc is in the README, that every doc has a Related section, and that Open Questions is the highest-numbered file.
