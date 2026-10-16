#!/usr/bin/env python3
"""Fetch the pinned upstream corpus and verify every file before use.

No dependencies beyond Python 3.10+. Existing files are verified, never trusted
because they happen to have the right filename. Downloads are written atomically.
"""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=root / '.cache' / 'sblgnt')
    args = parser.parse_args()
    manifest = json.loads((root / 'data' / 'corpus-manifest.json').read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    verified = 0
    for filename, expected in manifest['files'].items():
        path = args.output / filename
        data = path.read_bytes() if path.exists() else None
        if data is None or hashlib.sha256(data).hexdigest() != expected['sha256']:
            url = (f"https://raw.githubusercontent.com/morphgnt/sblgnt/"
                   f"{manifest['commit']}/{filename}")
            request = urllib.request.Request(url, headers={'User-Agent': 'hebrews-research/1.0'})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != expected['sha256']:
                raise RuntimeError(f'Checksum mismatch: {filename}')
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_bytes(data)
            temporary.replace(path)
        if len(data) != expected['bytes']:
            raise RuntimeError(f'Length mismatch: {filename}')
        verified += 1
    print(f'Verified {verified} files at upstream commit {manifest["commit"]}')
    print(args.output.resolve())


if __name__ == '__main__':
    main()
