<!-- nav -->[🏠 Index](README.md) · [Next →](01-overview.md)

# 00 – How to Plan This Project

A guide to the planning process, the documents it needs, and how they are written and linked.

## 1. Planning steps
| Step | Activity | Output doc |
|---|---|---|
| 1 | **Define the goal:** what problem it solves, for whom, what "success" looks like | [01](01-overview.md) |
| 2 | **Split the scope** into major areas (long-term first, short-term later) | [03](03-long-term-analyzer.md), [02](02-short-term-analyzer.md) |
| 3 | **Identify inputs:** what data is needed, where it comes from, how it's configured | [04](04-data-sources.md), [11](11-live-cloud-data.md), [21](21-stock-analysis-datapoints.md), [22](22-provider-configuration-ui.md) |
| 4 | **Choose methods:** models, ML pipeline, AI, and how to measure them | [05](05-models-and-evaluation.md), [18](18-methods-accuracy-references.md), [26](26-ml-pipeline.md), [10](10-ai-llm-integration.md) |
| 5 | **Define actions:** entry, holding period, exit | [12](12-entry-exit-strategy.md), [15](15-trade-journal.md), [16](16-holding-period-screener.md) |
| 6 | **Define what users see:** features, pages, reports | [06](06-app-features.md), [13](13-daily-returns-report.md), [23](23-frontend-react.md) |
| 7 | **Design the structure:** architecture, database, code standards | [07](07-architecture.md), [17](17-database-backend.md), [24](24-coding-standards.md) |
| 8 | **List the quality needs:** reliability, security, users, compliance | [08](08-non-functional.md), [19](19-auth-multi-user.md) |
| 9 | **Plan how it runs:** Docker, environments, 24/7 operation, everything to set up | [14](14-docker-deployment.md), [20](20-environments-dev-test-prod.md), [25](25-infrastructure-services-inventory.md) |
| 10 | **Sequence the work** into phases and **define each deliverable's outcome** | [09](09-roadmap.md), [deliverables/](deliverables/README.md) |
| 11 | **Track open decisions** and resolve them | [28](28-open-questions.md) |
| 12 | **Review and iterate:** update docs as decisions are made | All |

## 2. Requirements checklist
Use this to check that the planning is complete.

- [x] Goal and target users defined (personal + invited users)
- [x] Market chosen (India NSE/BSE now, world later) and stock list chosen (NIFTY 50 → all NSE)
- [x] Build order chosen (long-term first; short-term 1 day – 2 weeks later)
- [x] Long-term method chosen (rule-based score + ML forecast) and holding categories (50D … 3Y)
- [x] Entry/exit rules agreed (combination exit style, Q13; risk per trade custom, default 1%, Q14)
- [x] Data approach chosen (direct-connect APIs, configured in the admin UI); no broker (manual journal); [ ] first market data + fundamentals API picked (Q45)
- [x] Data freshness (hourly + end-of-day) and budget (paid APIs accepted) decided
- [x] LLM decided (OpenAI only if required; local on Apple Silicon / NVIDIA optional)
- [x] Baseline and evaluation metrics defined ([05](05-models-and-evaluation.md), [18](18-methods-accuracy-references.md))
- [x] Stack chosen (FastAPI + PostgreSQL + React) and coding standards defined
- [x] Environments defined (local dev/test in Docker, Linux prod later)
- [x] Roadmap phases agreed
- [ ] Data points researched ([21](21-stock-analysis-datapoints.md#research-tracker), in progress)
- [ ] All [open questions](28-open-questions.md) answered (remaining ones belong to later phases)

## 3. Planning skills
| Skill | What it means here |
|---|---|
| **Decomposition** | Break the big idea into independent parts (data, models, UI) |
| **Prioritization** | Build what is simplest and most valuable first (MVP) |
| **Assumption tracking** | Write down every unknown in Open Questions |
| **Trade-off thinking** | Compare options in tables: pros, cons, cost |
| **Validation mindset** | Decide *how to prove it works* before building |
| **Iteration** | Docs are living documents. Update them, don't freeze them |

## 4. How to create a new doc
1. **Name it** `NN-short-name.md`. `NN` is a two-digit number in reading order; use lowercase words with hyphens.
2. **Start from the template** below.
3. **Add a row** for it in the [README index](README.md).
4. **Add navigation links** (top and bottom) and update the neighbouring docs' Previous/Next links.
5. **Link related docs** inline wherever another doc is mentioned.

### Template
```markdown
[🏠 Index](README.md) · [← Previous](NN-prev.md) · [Next →](NN-next.md)

# NN – Title

**Purpose:** one sentence on what this doc decides or describes.

## Section
Content, preferably as tables and lists.

## Related
- [Other doc](NN-other.md)

---
[← Previous](NN-prev.md) · [🏠 Index](README.md) · [Next →](NN-next.md)
```

## 5. Writing conventions
These are for planning docs. Code, naming and code documentation rules are in [24 – Coding Standards & Clean Architecture 📏](24-coding-standards.md).

- **Headings:** a `#` title with its number, `##` for sections, `###` for subsections
- **Tables** for comparisons and options; **lists** for features
- **Diagrams in Mermaid** (` ```mermaid ` blocks) for architecture, data flows, sequences and state machines. Never use ASCII-art diagrams. Folder trees and output examples stay as plain code blocks.
- **Code blocks** for folder layouts, output examples and config
- **Emoji markers:** 🟢 short-term, 🔵 long-term, ⚠️ warnings
- **Decisions:** mark them as `_TBD_` until decided, then record them in [28](28-open-questions.md)
- Keep each doc focused on **one topic**

## 6. Linking rules (for easy navigation)
- Use **relative links** only, e.g. `[Data Sources](04-data-sources.md)`, so links work in VS Code, GitHub and offline
- To link a section, use its heading anchor: `[Fetching](11-live-cloud-data.md#fetching-strategy)`
- Every doc has a **nav bar at the top and bottom**: Index · Previous · Next
- The [README](README.md) is the **single entry point** and must list every doc
- In VS Code: **Cmd+Click** a link to open it, and **Cmd+Shift+V** to preview the rendered Markdown

---
<!-- nav -->[🏠 Index](README.md) · [Next →](01-overview.md)
