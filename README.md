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

Validated against real prompt and Jira ticket samples. Compression consistently delivers **~37% word reduction** regardless of input length or provider.

Baseline: average Jira ticket = 249 words → 156 words after compression (332 → 208 tokens).

### Claude Sonnet 4.6 — $3/M input tokens

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $1.49 | $0.56 | $0.93 | $6.72 |
| Mid-size (200 devs) | 500 | $14.94 | $5.57 | $9.37 | $66.84 |
| Large (2K devs) | 5,000 | $149 | $55.60 | $93.40 | $667 |
| Large (10K devs) | 25,000 | $747 | $278 | $469 | $3,336 |
| SaaS (1K customers) | 100,000 | $2,988 | $1,115 | $1,873 | $13,380 |
| SaaS (10K customers) | 1,000,000 | $29,880 | $11,148 | $18,732 | **$133,776** |

### GPT-5.4 — $2.50/M input tokens

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $1.24 | $0.46 | $0.78 | $5.52 |
| Mid-size (200 devs) | 500 | $12.45 | $4.64 | $7.81 | $55.68 |
| Large (2K devs) | 5,000 | $124.50 | $46.44 | $78.06 | $557 |
| Large (10K devs) | 25,000 | $622 | $232 | $390 | $2,784 |
| SaaS (1K customers) | 100,000 | $2,490 | $929 | $1,561 | $11,148 |
| SaaS (10K customers) | 1,000,000 | $24,900 | $9,288 | $15,612 | **$111,456** |

### Claude Haiku 4.5 — $1/M input tokens

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $0.50 | $0.19 | $0.31 | $2.28 |
| Mid-size (200 devs) | 500 | $4.98 | $1.86 | $3.12 | $22.32 |
| Large (2K devs) | 5,000 | $49.80 | $18.58 | $31.22 | $222.96 |
| Large (10K devs) | 25,000 | $249 | $92.90 | $156.10 | $1,115 |
| SaaS (1K customers) | 100,000 | $996 | $372 | $624 | $4,464 |
| SaaS (10K customers) | 1,000,000 | $9,960 | $3,716 | $6,244 | **$44,592** |

### GPT-5.4-mini — $0.75/M input tokens

| Scale | Tickets/day | Original/mo | Saved/mo | After/mo | Saved/yr |
|---|---|---|---|---|---|
| Small team (20 devs) | 50 | $0.37 | $0.14 | $0.23 | $1.68 |
| Mid-size (200 devs) | 500 | $3.74 | $1.39 | $2.35 | $16.68 |
| Large (2K devs) | 5,000 | $37.35 | $13.94 | $23.41 | $167.28 |
| Large (10K devs) | 25,000 | $187 | $69.70 | $117.30 | $836.40 |
| SaaS (1K customers) | 100,000 | $747 | $278.70 | $468.30 | $3,344 |
| SaaS (10K customers) | 1,000,000 | $7,470 | $2,786 | $4,684 | **$33,432** |

### Notes

- Savings apply to **input tokens only** — output tokens are unaffected
- The 37% reduction holds consistently across prompt types (tickets, freeform, instructions)
- Compression is provider-agnostic — same gain regardless of which model you use
- For pipelines ingesting comments, changelogs, or sprint context, savings multiply further
- Cursor users on flat subscriptions see no direct cost reduction — the win there is context window efficiency
