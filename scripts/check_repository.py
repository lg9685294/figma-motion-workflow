#!/usr/bin/env python3
"""Check portable local links, distributable contents and deterministic examples.

This does not connect to Figma, validate remote URLs or run GitHub Actions.
"""
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import urlparse, unquote
import hashlib
import importlib.util
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'figma-motion-workflow'


def main():
    problems = []
    required = ['README.md', 'LICENSE', 'ATTRIBUTION.md', 'docs/install.md',
                'docs/validation.md', 'docs/assets/workflow.svg', 'docs/assets/timing-demo.gif',
                'examples/timing-spec.json', 'downloads/figma-motion-workflow.zip',
                '.github/workflows/checks.yml']
    for name in required:
        if not (ROOT / name).is_file():
            problems.append('Missing ' + name)
    skill_text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    if not skill_text.startswith('---\nname: figma-motion-workflow\n'):
        problems.append('Unexpected skill name or frontmatter')
    for path in ROOT.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        if path.suffix in ('.md', '.py', '.json', '.yml', '.yaml', '.svg', '.txt'):
            text = path.read_text(encoding='utf-8')
            if re.search(r'/(?:Users|home)/[^/\s]+/', text):
                problems.append('Machine-specific path in ' + str(path.relative_to(ROOT)))
            if re.search(r'chatgpt\.com/s/|figma\.com/(?:design|proto)/[A-Za-z0-9]{10,}', text):
                problems.append('Private project reference in ' + str(path.relative_to(ROOT)))
        if path.suffix == '.md':
            for value in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
                parsed = urlparse(value)
                if parsed.scheme or value.startswith(('#', '//')):
                    continue
                target = (path.parent / unquote(parsed.path)).resolve()
                try:
                    target.relative_to(ROOT)
                except ValueError:
                    problems.append('Nonportable link in ' + str(path.relative_to(ROOT)))
                    continue
                if not target.exists():
                    problems.append('Broken link in {}: {}'.format(path.relative_to(ROOT), value))
    archive = ROOT / 'downloads' / 'figma-motion-workflow.zip'
    if archive.exists():
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        expected = (ROOT / 'downloads' / 'SHA256SUMS.txt').read_text().split()[0]
        if digest != expected:
            problems.append('Archive checksum mismatch')
        originals = {str(Path(SKILL.name) / p.relative_to(SKILL)): p for p in SKILL.rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix != '.pyc' and p.name != '.DS_Store'}
        with ZipFile(archive) as bundle:
            if bundle.testzip():
                problems.append('Archive corruption')
            if set(bundle.namelist()) != set(originals):
                problems.append('Archive file set differs from skill source')
            else:
                for name, source in originals.items():
                    if bundle.read(name) != source.read_bytes():
                        problems.append('Archive differs from ' + name)
    module_spec = importlib.util.spec_from_file_location('timing_check', SKILL / 'scripts' / 'timeline.py')
    module = importlib.util.module_from_spec(module_spec)
    import sys
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    audit = module.audit(json.loads((ROOT / 'examples' / 'timing-spec.json').read_text()))
    if not audit['complete'] or not math.isclose(audit['resolved_total_ms'], 752.1333818409485, abs_tol=1e-7):
        problems.append('Unexpected example timing result')
    if problems:
        print(json.dumps({'status': 'failed', 'problems': problems}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    print(json.dumps({'status': 'passed', 'checks': ['local reference files', 'portable public text',
          'download checksum', 'download equals skill source', 'example dependencies'],
          'figma_verified': False, 'github_published': False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
