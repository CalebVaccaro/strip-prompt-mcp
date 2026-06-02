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

Optional flags (not active by default):

```bash
# Show the compressed context that will be sent to the model
echo "your prompt here" | strip-prompt --context

# Show word reduction percentage
echo "your prompt here" | strip-prompt --reduction

# Show both
echo "your prompt here" | strip-prompt --context --reduction
```

These flags are informational — useful for inspecting what gets sent to the model before inference.

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

**CONTEXT** — simply strip fluff and keep core context.

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

### gpt-5.3-codex — $1.75/M input tokens *(as of June 2026)*

Standard pricing. Batch pricing is 50% off ($0.875/M) for async pipelines.

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $0.87 | $0.41 | $0.46 | $4.92 |
| Mid-size (200 devs) | 500 | $8.72 | $4.10 | $4.62 | $49.20 |
| Large (2K devs) | 5,000 | $87.15 | $40.95 | $46.20 | $491 |
| Large (10K devs) | 25,000 | $435.75 | $204.75 | $231 | $2,457 |
| SaaS (1K customers) | 100,000 | $1,743 | $819 | $924 | $9,828 |
| SaaS (10K customers) | 1,000,000 | $17,430 | $8,190 | $9,240 | **$98,280** |

### GPT-5.5 — $5/M input tokens *(as of June 2026)*

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $2.49 | $1.17 | $1.32 | $14.04 |
| Mid-size (200 devs) | 500 | $24.90 | $11.70 | $13.20 | $140.40 |
| Large (2K devs) | 5,000 | $249 | $117 | $132 | $1,404 |
| Large (10K devs) | 25,000 | $1,245 | $585 | $660 | $7,020 |
| SaaS (1K customers) | 100,000 | $4,980 | $2,340 | $2,640 | $28,080 |
| SaaS (10K customers) | 1,000,000 | $49,800 | $23,400 | $26,400 | **$280,800** |

### Claude Haiku 4.5 — $1/M input tokens *(as of June 2026)*

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $0.50 | $0.23 | $0.27 | $2.81 |
| Mid-size (200 devs) | 500 | $4.98 | $2.34 | $2.64 | $28.08 |
| Large (2K devs) | 5,000 | $49.80 | $23.40 | $26.40 | $280.80 |
| Large (10K devs) | 25,000 | $249 | $117 | $132 | $1,404 |
| SaaS (1K customers) | 100,000 | $996 | $468 | $528 | $5,616 |
| SaaS (10K customers) | 1,000,000 | $9,960 | $4,680 | $5,280 | **$56,160** |

### Notes

- Savings apply to **input tokens only** — output tokens are unaffected
- Reduction varies: formal/verbose text (PM stories, support tickets) compresses ~50%+; technical docs and bug reports compress ~37–43%
- Compression is provider-agnostic — same gain regardless of which model you use
- For pipelines ingesting comments, changelogs, or sprint context alongside tickets, savings multiply further
- Cursor users on flat subscriptions see no direct cost reduction — the win there is context window efficiency
- Run `python test_compression.py` to validate against your own workload before sizing the savings
