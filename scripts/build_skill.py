#!/usr/bin/env python3
"""Build the standalone skill archive deterministically (standard library only)."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'figma-motion-workflow'
OUT = ROOT / 'downloads'


def main():
    OUT.mkdir(exist_ok=True)
    archive = OUT / 'figma-motion-workflow.zip'
    files = sorted(p for p in SKILL.rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts
                   and p.suffix != '.pyc' and p.name != '.DS_Store')
    with ZipFile(archive, 'w', ZIP_DEFLATED) as bundle:
        for path in files:
            if path.is_symlink():
                raise ValueError('Do not package symlinks: ' + str(path.relative_to(ROOT)))
            info = ZipInfo(str(Path(SKILL.name) / path.relative_to(SKILL)), (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (OUT / 'SHA256SUMS.txt').write_text(digest + '  ' + archive.name + '\n', encoding='utf-8')
    print('Built {} ({} files)'.format(archive.name, len(files)))


if __name__ == '__main__':
    main()
