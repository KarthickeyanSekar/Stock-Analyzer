<!-- nav -->[← Previous](09-roadmap.md) · [🏠 Index](README.md) · [Next →](11-live-cloud-data.md)

# 10 – AI / LLM Integration (OpenAI or Local Models)

> ⚙️ **Decision:**
> - All predictions, scores, ranges and probabilities use **pure statistics / ML**. The LLM never produces a number.
> - **Provider: OpenAI, used only if required** (e.g., explaining a result or summarizing an earnings report).
> - Disabled by default (`LLM_PROVIDER=none`); set `LLM_PROVIDER=openai` to enable it. A local model may be added later, on both Apple Silicon and NVIDIA GPUs (see below).

LLMs are **optional** and used where they are strong: understanding text and explaining results.
They should **not** be the source of prices or the numeric price predictor.

## Golden rule
> All actual values (prices, volumes, financials) come from **live cloud data APIs**.
> The LLM only receives those values as input. It never invents or "remembers" them.

## Where LLMs help
| Use case | Mode | Example |
|---|---|---|
| News sentiment scoring | Short-term | Headline → positive / negative / neutral + score |
| Earnings report / filing summary | Long-term | 10-K / annual report → key risks, growth drivers |
| Earnings call analysis | Long-term | Management tone, guidance changes |
| Plain-language explanation | Both | "Why is the signal Buy?" based on the model's computed features |
| Natural-language queries | Both | "Show IT stocks with P/E < 25 and ROE > 20%" → filter |
| Report generation | Both | Weekly watchlist summary |

## Where LLMs should NOT be used
- Producing the current price or historical values (they may be outdated or hallucinated)
- Producing the final % prediction alone. Use the ML/statistical models (doc 05); the LLM
  output can feed in as one feature (e.g., the sentiment score).

## Provider options
| Option | Examples | Pros | Cons |
|---|---|---|---|
| Cloud (OpenAI) | GPT models via the `openai` SDK | Best quality, no hardware needed | Cost per call, data leaves your machine, needs internet |
| Local | Ollama, LM Studio, llama.cpp (Llama, Mistral, Qwen, Phi) | Free per call, private, works offline | Needs RAM/GPU, lower quality on complex tasks |
| Finance-specific (local) | FinBERT (`transformers`) | Fast, accurate for sentiment, small | Sentiment only |

## Design: provider-agnostic layer
Switch between OpenAI and local models through config, without changing code.
```
application/ports/llm.py              # LanguageModelProvider port: complete(), classify(), summarize()
infrastructure/providers/llm/
├── openai/provider.py                # OpenAiLanguageModelProvider
├── ollama/provider.py                # OllamaLanguageModelProvider (OpenAI-compatible endpoint)
└── prompts/                          # versioned prompt templates
```
```
# .env
LLM_PROVIDER=openai        # or: local
OPENAI_API_KEY=...
LOCAL_LLM_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3
```
Ollama and LM Studio expose OpenAI-compatible APIs, so one client can serve both.

## Local LLM hardware: Apple Silicon + NVIDIA
✅ Decision: support **both**.

| | Apple Silicon (dev, macOS) | NVIDIA GPU (prod, Linux) |
|---|---|---|
| Runtime | **Ollama installed natively on macOS** (uses the Metal GPU) | **Ollama container** with GPU access |
| In Docker? | ❌ No. Docker on macOS can't use the Apple GPU, so a containerized model would run on the CPU only (slow) | ✅ Yes, via the **NVIDIA Container Toolkit** (`deploy.resources.reservations.devices: [{driver: nvidia, capabilities: [gpu]}]`) |
| App connects to | `http://host.docker.internal:11434/v1` | `http://ollama:11434/v1` (compose service) |
| Memory guide | 16 GB unified memory → ~7–8B models; 32 GB+ → ~14B | 8–12 GB VRAM → ~7–8B; 24 GB → ~14–32B (quantized) |
| Host setup | `brew install ollama` | NVIDIA driver + NVIDIA Container Toolkit on the Linux host |

Only `LOCAL_LLM_URL` changes per environment. The app code is identical
(Ollama exposes an OpenAI-compatible API). The `ollama` service lives in the **prod** compose override only; see
[20 – Environments: Dev, Test & Prod 🧪](20-environments-dev-test-prod.md).

## Cost & performance controls
- Cache LLM results (the same news article is never scored twice)
- Use FinBERT/local models for high-volume work, and OpenAI for deep summaries
- Batch requests, and set daily budget limits
- Log tokens and cost for every call

## Risks
- Hallucination → always ground prompts in fetched data and show the sources
- Prompt injection from news text → treat news as data, and validate outputs against a schema (JSON)
- Model changes over time → pin model versions and re-check sentiment accuracy

## Related
- [02 – Short-Term Analyzer 🟢](02-short-term-analyzer.md)
- [05 – Models & Evaluation](05-models-and-evaluation.md)
- [07 – Architecture & Tech Stack](07-architecture.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](09-roadmap.md) · [🏠 Index](README.md) · [Next →](11-live-cloud-data.md)
