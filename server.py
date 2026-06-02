#!/usr/bin/env python3
"""
strip-prompt MCP server
Exposes a compress_text tool that removes stop words and filler
from any English text — designed for AI-generated Jira tickets and verbose prompts.
"""
import asyncio
import re
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# -- stop word setup ----------------------------------------------------------
try:
    import nltk
    try:
        from nltk.corpus import stopwords
        STOP = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords', quiet=True)
        from nltk.corpus import stopwords
        STOP = set(stopwords.words('english'))
except ImportError:
    print("nltk not installed. Run: pip install nltk", file=sys.stderr)
    sys.exit(1)

EXTRA_STOP = {
    'hi', 'hey', 'hello', 'thanks', 'thank', 'please', 'okay', 'ok',
    'basically', 'essentially', 'literally', 'potentially', 'possibly',
    'certainly', 'definitely', 'absolutely', 'obviously', 'clearly',
}

KEEP = {
    'not', 'no', 'never', 'neither', 'nor', 'none', 'without',
    'more', 'most', 'less', 'least', 'also', 'both', 'each',
    'few', 'other', 'some', 'such', 'only', 'same', 'than',
    'why', 'how', 'what', 'when', 'where', 'which', 'who',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
}

STOP = (STOP | EXTRA_STOP) - KEEP

# -- compression --------------------------------------------------------------
def compress(text: str) -> str:
    tokens = text.split()
    result = []
    for token in tokens:
        key = re.sub(r"[^a-z']", '', token.lower())
        if not key or key not in STOP:
            result.append(token)
    return re.sub(r'  +', ' ', ' '.join(result)).strip()

# -- MCP server ---------------------------------------------------------------
server = Server("strip-prompt")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="compress_text",
            description=(
                "Remove stop words and filler from English text to reduce token count. "
                "Useful for compressing AI-generated Jira tickets, verbose requirements, "
                "or any long-form English before passing to an agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to compress"
                    }
                },
                "required": ["text"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name != "compress_text":
        raise ValueError(f"Unknown tool: {name}")
    text = (arguments or {}).get("text", "")
    compressed = compress(text)
    original_tokens = len(text.split())
    compressed_tokens = len(compressed.split())
    reduction = round((1 - compressed_tokens / original_tokens) * 100) if original_tokens else 0
    return [
        types.TextContent(
            type="text",
            text=f"{compressed}\n\n[{original_tokens} → {compressed_tokens} words, {reduction}% reduction]"
        )
    ]

# -- entrypoint ---------------------------------------------------------------
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
