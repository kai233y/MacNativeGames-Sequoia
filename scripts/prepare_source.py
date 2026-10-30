#!/usr/bin/env python3
"""Fetch the exact upstream source and apply a verified Sequoia patch."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)


def main():
    manifest = json.loads((ROOT / 'sources.json').read_text())
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('game', choices=manifest)
    ap.add_argument('destination', type=Path, help='new directory outside this repository')
    args = ap.parse_args()
    target = args.destination.expanduser().resolve()
    if target == ROOT or ROOT in target.parents:
        ap.error('put source checkouts outside this patch repository')
    if target.exists():
        ap.error('destination already exists; choose a new directory')
    entry = manifest[args.game]
    patch = ROOT / entry['patch']
    if hashlib.sha256(patch.read_bytes()).hexdigest() != entry['patch_sha256']:
        ap.error('patch checksum does not match sources.json')
    target.mkdir(parents=True)
    run('git', 'init', str(target))
    run('git', 'remote', 'add', 'origin', entry['repository'], cwd=target)
    run('git', 'config', 'remote.origin.promisor', 'true', cwd=target)
    run('git', 'config', 'remote.origin.partialclonefilter', 'blob:none', cwd=target)
    run('git', '-c', 'http.version=HTTP/1.1', 'fetch', '--depth=1', '--filter=blob:none', 'origin', entry['commit'], cwd=target)
    if args.game == 'botw160':
        run('git', 'sparse-checkout', 'init', '--cone', cwd=target)
        run('git', 'sparse-checkout', 'set', 'games/totk', 'games/botw', 'docs', cwd=target)
    run('git', 'checkout', '--detach', 'FETCH_HEAD', cwd=target)
    run('git', 'apply', '--check', str(patch), cwd=target)
    run('git', 'apply', str(patch), cwd=target)
    run('git', 'diff', '--check', cwd=target)
    print(f'Ready: {target}\nRead {ROOT / "docs" / (args.game + "-build.md")} before building. Gameplay testing is manual.')


if __name__ == '__main__':
    main()
