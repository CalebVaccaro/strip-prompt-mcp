# strip-prompt-mcp

MCP server that strips stop words and filler from English text to reduce token count. Built for compressing AI-generated Jira tickets and verbose prompts before passing them to an agent.

## Install

```bash
git clone https://github.com/CalebVaccaro/strip-prompt-mcp
cd strip-prompt-mcp
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python3 -c "import nltk; nltk.download('stopwords')"
```

Quick local smoke test:

```bash
python server.py --compress "Please summarize the existing implementation and identify risks."
```

## Option A — Auto-strip every prompt (hook)

Runs the compressor locally before Claude ever sees your prompt. Zero inference cost on the filler.

```bash
bash install.sh
```

That's it. `install.sh` adds a `UserPromptSubmit` hook to `~/.claude/settings.json`. Every prompt is stripped on your machine before it's sent.

To remove it, delete the hook entry from `~/.claude/settings.json`.

## Option B — MCP tool (explicit, on demand)

Add the server to your Claude workspace and call `compress_text` manually or let the agent call it when it needs to compress content.

```bash
claude mcp add strip-prompt -- /absolute/path/to/strip-prompt-mcp/.venv/bin/python /absolute/path/to/strip-prompt-mcp/server.py
```

For this local checkout, the command would look like:

```bash
claude mcp add strip-prompt -- "$PWD/.venv/bin/python" "$PWD/server.py"
```

Or add manually to a repo or workspace MCP config:

```json
{
  "mcpServers": {
    "strip-prompt": {
      "command": "/absolute/path/to/strip-prompt-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/strip-prompt-mcp/server.py"]
    }
  }
}
```

The MCP server can live outside the repo where it is used. The only requirement is that the `command` points to a Python environment with `requirements.txt` installed, and `args[0]` points to this repository's `server.py`.

Both options can be active at the same time.

## Tool: `compress_text`

Removes NLTK English stop words and common filler words from any text. Preserves semantic content — nouns, verbs, technical terms, numbers, and negations are kept.

**Input:** `text` (string)

**Output:** compressed text + token reduction stats

**Example:**

Input (33 words):
> As part of our ongoing initiative to improve operational efficiency across the platform, we would like to explore opportunities to enhance the user onboarding experience.

Output (20 words, 39% reduction):
> part ongoing initiative improve operational efficiency across platform, like explore opportunities enhance user onboarding experience.
>
> [33 → 20 words, 39% reduction]

## What gets stripped

- NLTK's 198 English stop words (articles, prepositions, auxiliary verbs, pronouns)
- Filler: `basically`, `essentially`, `literally`, `potentially`, `possibly`, `hi`, `thanks`, `please`

## What's kept

Negations (`not`, `no`, `never`), question words (`what`, `how`, `why`, `which`), comparatives (`more`, `less`, `most`), and all domain-specific nouns, verbs, and technical terms.

## Cost savings at scale

> **These numbers are estimates, not guarantees.** Reduction varies by input type, writing style, and domain vocabulary. Run `python test_compression.py` to benchmark against your own scenarios and get a validated average for your workload.

The figures below use the **validated average from `test_compression.py`** across 10 representative scenarios (short prompts, Jira tickets, PM stories, support requests, docs, meeting notes):

```
Scenario                               Word reduction   Char reduction
─────────────────────────────────────────────────────────────────────
Short casual prompt                         42.9%           27.1%
Developer freeform question                 45.8%           30.2%
Jira bug report                             37.3%           22.6%
Jira feature request                        51.4%           35.7%
Jira task / technical ticket                43.0%           28.3%
Agile / PM style story                      52.9%           37.6%
Customer support request                    51.6%           40.0%
Technical documentation excerpt             40.0%           24.2%
Meeting notes / async update                51.4%           36.7%
Slack-style developer message               53.3%           40.3%
─────────────────────────────────────────────────────────────────────
Average                                     47.0%           32.3%
```

Baseline for tables: 332 input tokens/ticket, **47% word reduction → 156 tokens saved per call**.

Pricing sourced June 2026. Check provider pages for current rates before relying on these figures.

### Claude Sonnet 4.6 — $3/M input tokens *(as of June 2026)*

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $1.49 | $0.70 | $0.79 | $8.40 |
| Mid-size (200 devs) | 500 | $14.94 | $7.02 | $7.92 | $84.24 |
| Large (2K devs) | 5,000 | $149 | $70.20 | $79 | $842 |
| Large (10K devs) | 25,000 | $747 | $351 | $396 | $4,212 |
| SaaS (1K customers) | 100,000 | $2,988 | $1,404 | $1,584 | $16,848 |
| SaaS (10K customers) | 1,000,000 | $29,880 | $14,040 | $15,840 | **$168,480** |

### GPT-5.4 — $2.50/M input tokens *(as of June 2026)*

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $1.24 | $0.59 | $0.65 | $7.02 |
| Mid-size (200 devs) | 500 | $12.45 | $5.85 | $6.60 | $70.20 |
| Large (2K devs) | 5,000 | $124 | $58.50 | $66 | $702 |
| Large (10K devs) | 25,000 | $622 | $292 | $330 | $3,510 |
| SaaS (1K customers) | 100,000 | $2,490 | $1,170 | $1,320 | $14,040 |
| SaaS (10K customers) | 1,000,000 | $24,900 | $11,700 | $13,200 | **$140,400** |

### Claude Haiku 4.5 — $1/M input tokens *(as of June 2026)*

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $0.50 | $0.23 | $0.27 | $2.81 |
| Mid-size (200 devs) | 500 | $4.98 | $2.34 | $2.64 | $28.08 |
| Large (2K devs) | 5,000 | $49.80 | $23.40 | $26.40 | $280.80 |
| Large (10K devs) | 25,000 | $249 | $117 | $132 | $1,404 |
| SaaS (1K customers) | 100,000 | $996 | $468 | $528 | $5,616 |
| SaaS (10K customers) | 1,000,000 | $9,960 | $4,680 | $5,280 | **$56,160** |

### GPT-5.4-mini — $0.75/M input tokens *(as of June 2026)*

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $0.37 | $0.18 | $0.19 | $2.11 |
| Mid-size (200 devs) | 500 | $3.74 | $1.76 | $1.98 | $21.06 |
| Large (2K devs) | 5,000 | $37.35 | $17.55 | $19.80 | $210.60 |
| Large (10K devs) | 25,000 | $187 | $87.75 | $99.25 | $1,053 |
| SaaS (1K customers) | 100,000 | $747 | $351 | $396 | $4,212 |
| SaaS (10K customers) | 1,000,000 | $7,470 | $3,510 | $3,960 | **$42,120** |

### Notes

- Savings apply to **input tokens only** — output tokens are unaffected
- Reduction varies: formal/verbose text (PM stories, support tickets) compresses ~50%+; technical docs and bug reports compress ~37–43%
- Compression is provider-agnostic — same gain regardless of which model you use
- For pipelines ingesting comments, changelogs, or sprint context alongside tickets, savings multiply further
- Cursor users on flat subscriptions see no direct cost reduction — the win there is context window efficiency
- Run `python test_compression.py` to validate against your own workload before sizing the savings
