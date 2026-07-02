# KhetSaathi (खेत साथी) — A Multi-Agent Farming Companion

**Track:** Agents for Good
**Built for:** Kaggle 5-Day AI Agents Intensive Vibe Coding Course — Capstone Project

## Problem

India has over 100 million smallholder farmers, most of whom make three
high-stakes decisions with very little reliable, timely information:

1. **"What's wrong with my crop, and what do I do about it?"** — misdiagnosed
   disease leads to wrong pesticide use, wasted money, and crop loss.
2. **"Should I irrigate today?"** — over- or under-watering wastes a scarce
   resource and hurts yield.
3. **"Where and when should I sell?"** — without visibility into mandi (market)
   prices, farmers often sell too early or to the wrong market.

Agricultural extension officers exist but are stretched thin — one officer
can cover thousands of farmers. An always-available, multilingual AI agent
that gives grounded (not hallucinated) advice can close this gap.

## Why Agents

A single monolithic prompt struggles to reliably handle three very
different domains (plant pathology, meteorology, market economics) with
different data sources and different failure modes. Splitting the problem
into **specialist sub-agents**, each with its own tool and narrow
instructions, means:

- Each specialist can be tested, debugged, and improved independently.
- The orchestrator only needs to solve *routing*, which is a much simpler
  problem than solving everything at once.
- Grounding: each specialist calls a **real tool** (via MCP) instead of the
  LLM guessing a chemical name, a price, or a weather forecast from memory —
  critical when bad advice can financially harm a farmer.

## Architecture

```
                         ┌─────────────────────────┐
                         │   Farmer (CLI / chat)    │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │  khetsaathi_orchestrator   │  (ADK LlmAgent, root_agent)
                         │  routes by intent          │
                         └───┬───────────┬───────────┘
                 ┌───────────┘           │           └────────────┐
                 ▼                       ▼                        ▼
      ┌────────────────────┐ ┌────────────────────┐  ┌────────────────────┐
      │  crop_doctor_agent  │ │  irrigation_agent   │  │   market_agent      │
      │  (disease diagnosis)│ │  (weather advice)    │  │  (mandi prices)      │
      └──────────┬──────────┘ └──────────┬──────────┘  └──────────┬──────────┘
                 │  MCPToolset (stdio)   │  MCPToolset (stdio)     │  MCPToolset (stdio)
                 ▼                       ▼                        ▼
      ┌─────────────────────────────────────────────────────────────────┐
      │                  KhetSaathi MCP Server (FastMCP)                  │
      │  tools: diagnose_crop_disease · get_weather_forecast · get_mandi_price │
      └─────────────────────────────────────────────────────────────────┘
                 │                       │                        │
                 ▼                       ▼                        ▼
        crop_disease_db.json     Open-Meteo API (live)     mandi_prices.json
```

**Design choice:** all three specialist agents connect to *one shared* MCP
server (`mcp_server/server.py`), each using a `tool_filter` so it only sees
the tool relevant to its job. This mirrors a real deployment where a single
"agriculture data service" backs multiple agent products.

## Course Concepts Demonstrated

| Concept | Where | How |
|---|---|---|
| **Multi-agent system (ADK)** | `khetsaathi_agents/` | Root `LlmAgent` with 3 `sub_agents`; ADK handles LLM-driven delegation based on each sub-agent's `description`. |
| **MCP Server** | `mcp_server/server.py` | Custom FastMCP server exposing 3 tools, connected to by every sub-agent via `MCPToolset` + `StdioConnectionParams`. |
| **Agent skills (CLI)** | `cli.py` | A standalone CLI (`khetsaathi ask "..."` / interactive mode) that runs the full multi-agent system via ADK's `Runner`, so a farmer (or an SMS gateway) can use it without a GUI. |

## Project Structure

```
khetsaathi/
├── khetsaathi_agents/
│   ├── agent.py                  # root_agent (orchestrator)
│   └── sub_agents/
│       ├── crop_doctor/agent.py
│       ├── irrigation/agent.py
│       └── market/agent.py
├── mcp_server/
│   └── server.py                 # FastMCP server: 3 tools
├── data/
│   ├── crop_disease_db.json      # sample symptom -> diagnosis data
│   └── mandi_prices.json         # sample mandi price data
├── cli.py                        # Agent Skill: CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Setup & Running

1. **Install dependencies** (Python 3.10+):
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Add your Gemini API key**:
   ```bash
   cp .env.example .env
   # edit .env and paste your key from https://aistudio.google.com/apikey
   ```

3. **Run via the ADK web UI** (visual, recommended for judging/demo):
   ```bash
   adk web
   ```
   Open the printed localhost URL and select `khetsaathi_agents`.

4. **Run via the Agent Skill CLI**:
   ```bash
   # one-shot question
   python cli.py ask "my wheat leaves have yellow stripes and orange powder"

   # interactive chat
   python cli.py
   ```

5. **Test the MCP server standalone** (optional, for debugging tools):
   ```bash
   python mcp_server/server.py
   ```

## Security Notes

- No API keys or secrets are committed to this repository — `.env` is
  gitignored and `.env.example` only contains placeholders.
- The orchestrator's instructions explicitly forbid collecting or storing
  personal data beyond crop name and location.
- All factual claims (disease diagnosis, prices, weather) are **tool-grounded**
  — the LLM is instructed never to fabricate values that didn't come from a
  tool call, reducing the risk of harmful hallucinated agricultural advice.

## Sample Interaction

```
Aap (You)> mere tamatar ke patte peele ho rahe hain aur mud rahe hain

KhetSaathi> Ye lakshan Tomato Leaf Curl Virus (safed makkhi se failta hai) ki
taraf ishara karte hain. Confidence: 90%. Severity: High.

Salaah: Yellow sticky traps aur Imidacloprid ka chidkav karke safed makkhi
ko niyantrit karein. Sankramit paudhon ko hata kar jala dein taaki virus na
faile. Agli fasal ke liye virus-resistant variety chunein.

Kya aap paani dene ya mandi bhaav ke baare mein bhi jaanna chahenge?
```

## Data Sources

- **Weather:** live data from [Open-Meteo](https://open-meteo.com/) (free,
  no API key required).
- **Crop disease DB & mandi prices:** curated sample datasets included in
  `data/` for demo purposes. In production these would be swapped for
  live government data sources (e.g. data.gov.in's Agmarknet mandi price
  API and ICAR crop advisory data).

## Future Work

- Voice input/output for low-literacy farmers.
- SMS/WhatsApp gateway wrapping the CLI for feature-phone access.
- Image-based disease diagnosis (photo of the leaf, not just text description).
- Expand mandi and disease coverage beyond the sample dataset.
