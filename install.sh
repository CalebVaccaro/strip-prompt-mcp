#!/usr/bin/env bash
# install.sh: wire strip-prompt as a Claude Code UserPromptSubmit hook
# Runs before every prompt — strips stop words locally before inference.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_SCRIPT="$REPO_DIR/hook.py"
SETTINGS="$HOME/.claude/settings.json"

if [[ ! -f "$HOOK_SCRIPT" ]]; then
    echo "Error: hook.py not found at $HOOK_SCRIPT" >&2
    exit 1
fi

python3 - "$SETTINGS" "$HOOK_SCRIPT" <<'EOF'
import json, sys, os

settings_path = sys.argv[1]
hook_script = sys.argv[2]
hook_cmd = f"python3 {hook_script}"

if os.path.exists(settings_path):
    with open(settings_path) as f:
        settings = json.load(f)
else:
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    settings = {}

settings.setdefault('hooks', {})

# Check if hook already registered
existing = settings['hooks'].get('UserPromptSubmit', [])
for entry in existing:
    for h in entry.get('hooks', []):
        if h.get('command') == hook_cmd:
            print(f"Hook already registered in {settings_path}")
            sys.exit(0)

settings['hooks']['UserPromptSubmit'] = existing + [
    {
        "hooks": [
            {
                "type": "command",
                "command": hook_cmd
            }
        ]
    }
]

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')

print(f"Hook registered in {settings_path}")
print(f"Every prompt will now be stripped before Claude processes it.")
EOF
