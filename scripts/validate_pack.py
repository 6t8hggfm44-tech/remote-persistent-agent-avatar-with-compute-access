"""Validate this handoff pack's structure; does not test the planned application."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote

root = Path(__file__).resolve().parents[1]
errors = []
def public_file(path):
    relative = path.relative_to(root)
    return not any(part in {'.git', '__pycache__', 'runtime-data', 'private', 'private-evidence', '.test-data'} for part in relative.parts)

json_files = sorted(p for p in root.rglob('*.json') if public_file(p))
for path in json_files:
    try:
        json.loads(path.read_text())
    except Exception as exc:
        errors.append(f'{path.relative_to(root)}: {exc}')

project = json.loads((root / 'project.json').read_text())
for ref in project['read_order'] + project['contracts']:
    if not (root / ref).is_file():
        errors.append(f'Missing entry-point file: {ref}')

tasks = json.loads((root / 'agent/tasks.json').read_text())['tasks']
by_id = {task['id']: task for task in tasks}
if len(by_id) != len(tasks):
    errors.append('Duplicate task IDs')
for task in tasks:
    if not (root / task['workflow']).is_file():
        errors.append(f"Missing workflow for {task['id']}")
    for dep in task['depends_on']:
        if dep not in by_id:
            errors.append(f"Unknown dependency {dep} for {task['id']}")
    if task['status'] == 'verified' and not task['evidence']:
        errors.append(f"Verified task without evidence: {task['id']}")

done, active = set(), set()
def visit(task_id):
    if task_id in active:
        errors.append(f'Cycle at {task_id}')
        return
    if task_id in done or task_id not in by_id:
        return
    active.add(task_id)
    for dep in by_id[task_id]['depends_on']:
        visit(dep)
    active.remove(task_id)
    done.add(task_id)
for task_id in by_id:
    visit(task_id)

for path in sorted(p for p in root.rglob('*.md') if public_file(p)):
    content = path.read_text()
    if content.count('```') % 2:
        errors.append(f'Unbalanced fenced block: {path.relative_to(root)}')
    for target in re.findall(r'\]\(([^)]+)\)', content):
        if target.startswith(('http:', 'https:', '#', 'mailto:')):
            continue
        target = unquote(target.split('#')[0].strip('<>'))
        if target and not (path.parent / target).exists():
            errors.append(f'Broken local link: {path.relative_to(root)} -> {target}')

manifest = root / 'checksums.sha256'
if manifest.exists():
    listed = set()
    for line in manifest.read_text().splitlines():
        expected, relative = line.split('  ', 1)
        listed.add(relative)
        path = root / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f'Checksum mismatch: {relative}')
    actual = {str(p.relative_to(root)) for p in root.rglob('*')
              if p.is_file() and p != manifest and '.git' not in p.parts
              and public_file(p)}
    if actual != listed:
        errors.append('Checksum manifest does not match pack file inventory')
else:
    errors.append('Missing checksums.sha256')

if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(json_files)} JSON files, {len(tasks)} acyclic tasks, '
      'entry points, Markdown local links/fences and all file hashes.')
print('Pack checks do not run application tests. See docs/10-live-text-connection.md for runtime verification.')
