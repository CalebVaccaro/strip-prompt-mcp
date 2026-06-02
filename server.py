#!/usr/bin/env python3
"""
strip-prompt MCP server
Exposes a compress_text tool that removes stop words and filler
from any English text — designed for AI-generated Jira tickets and verbose prompts.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compressor import compress

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

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


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
