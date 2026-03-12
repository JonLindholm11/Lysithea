# lysithea/audit/fix_runner.py
"""
Thin wrapper around fix_agent.run_fix_agent() for the Electron GUI.

Spawned by ipc/fix.js with:
    python fix_runner.py --prompt "..." --path "/some/dir"

Streams human-readable progress to stdout (captured as logs by fix.js),
then emits the JSON result wrapped in sentinel markers so fix.js can
cleanly separate log lines from structured data.

Sentinel format:
    <<<LYSITHEA_FIX_RESULT_START>>>
    { ...json... }
    <<<LYSITHEA_FIX_RESULT_END>>>
"""

import argparse
import json
import sys
import os

# Ensure the lysithea package (parent dir) is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit.fix_agent import run_fix_agent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', required=True, help='Fix prompt or pasted error')
    parser.add_argument('--path',   required=True, help='Project directory to search')
    args = parser.parse_args()

    result = run_fix_agent(args.prompt, args.path)

    if result is None:
        print('<<<LYSITHEA_FIX_RESULT_START>>>')
        print(json.dumps({'ok': False, 'error': 'Agent could not locate the function.'}))
        print('<<<LYSITHEA_FIX_RESULT_END>>>')
        sys.exit(1)

    print('<<<LYSITHEA_FIX_RESULT_START>>>')
    print(json.dumps({'ok': True, **result}))
    print('<<<LYSITHEA_FIX_RESULT_END>>>')
    sys.exit(0)


if __name__ == '__main__':
    main()