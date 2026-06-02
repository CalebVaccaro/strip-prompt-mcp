#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit hook.
Strips stop words from every prompt before Claude processes it.
Set up automatically via install.sh.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compressor import compress

data = json.load(sys.stdin)
data['prompt'] = compress(data.get('prompt', ''))
print(json.dumps(data))
