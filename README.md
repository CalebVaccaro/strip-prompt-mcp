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
