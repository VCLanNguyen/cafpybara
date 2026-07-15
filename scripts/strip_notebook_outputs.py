#!/usr/bin/env python3
"""Git clean-filter: strip notebook outputs/execution counts before staging.

Self-contained (stdlib only) equivalent of `nbstripout` for environments
where that package isn't installed. Reads a notebook on stdin, writes the
stripped version to stdout -- the shape a git filter.<name>.clean command
needs. See .gitattributes / README for how this is wired up.

If the real `nbstripout` package *is* available, prefer it (run
`nbstripout --install`, which overwrites the git config this script sets up
with its own, more complete implementation) -- this script is a
no-dependency fallback, not a replacement.
"""
import json
import sys


def strip(nb: dict) -> dict:
    for cell in nb.get('cells', []):
        if cell.get('cell_type') != 'code':
            continue
        if cell.get('outputs'):
            cell['outputs'] = []
        if cell.get('execution_count') is not None:
            cell['execution_count'] = None
        metadata = cell.get('metadata')
        if isinstance(metadata, dict):
            for key in ('execution', 'ExecuteTime'):
                metadata.pop(key, None)
    nb.get('metadata', {}).pop('widgets', None)
    return nb


def main() -> None:
    raw = sys.stdin.read()
    try:
        nb = json.loads(raw)
    except json.JSONDecodeError:
        # Not valid JSON (e.g. git probing a non-notebook path) -- pass through.
        sys.stdout.write(raw)
        return
    if 'cells' not in nb:
        sys.stdout.write(raw)
        return
    json.dump(strip(nb), sys.stdout, indent=1)


if __name__ == '__main__':
    main()
