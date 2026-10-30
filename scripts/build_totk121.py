#!/usr/bin/env python3.14
"""重复打包本次已适配的 TOTK 1.2.1 / macOS 15；成品由用户自行打开测试。"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile


def firmware_folder(source, work):
    if source.is_dir():
        return source
    if not zipfile.is_zipfile(source):
        raise ValueError('--firmware 需要固件目录或 ZIP 压缩包')
    identity = f'{source}:{source.stat().st_size}:{source.stat().st_mtime_ns}'
    target = work / ('firmware-' + hashlib.sha256(identity.encode()).hexdigest()[:12])
    if (target / '.complete').is_file():
        return target
    with tempfile.TemporaryDirectory(prefix='firmware-unpack-', dir=work) as temporary:
        temporary = Path(temporary)
        names = set()
        with zipfile.ZipFile(source) as archive:
            for item in archive.infolist():
                name = Path(item.filename).name
                if item.is_dir() or '__MACOSX' in item.filename.split('/') or not name.lower().endswith('.nca'):
                    continue
                if name in names:
                    raise ValueError('固件 ZIP 内存在重复 NCA 文件名，请先人工整理')
                names.add(name)
                with archive.open(item) as src, (temporary / name).open('wb') as dst:
                    shutil.copyfileobj(src, dst)
        if not names:
            raise ValueError('固件 ZIP 内没有 NCA 文件')
        (temporary / '.complete').write_text(identity)
        if target.exists():
            raise ValueError(f'发现未完成的固件缓存，请检查后移走：{target}')
        temporary.rename(target)
    return target


def private_keys(source, target):
    """只传递本次 NCA 工具可用的已派生密钥，保留原文件，不输出密钥内容。"""
    values = {}
    for line in source.read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if '=' not in line:
            continue
        name, value = (part.strip() for part in line.split('=', 1))
        name = name.lower()
        if name != 'header_key' and not re.fullmatch(r'(titlekek|key_area_key_(application|ocean|system))_[0-9a-f]{2}', name):
            continue
        length = 64 if name == 'header_key' else 32
        if len(value) != length or not re.fullmatch('[0-9a-fA-F]+', value):
            raise ValueError(f'构建必需密钥字段 {name} 格式不正确，请检查原文件')
        if name in values and values[name] != value.lower():
            raise ValueError(f'密钥字段 {name} 存在冲突')
        values[name] = value.lower()
    if 'header_key' not in values:
        raise ValueError('密钥文件缺少 header_key')
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(''.join(f'{name} = {value}\n' for name, value in values.items()))


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'update', 'keys', 'firmware'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, default=here.parents[1] / 'build/TOTK_build')
    parser.add_argument('--out', type=Path, default=here.parents[1] / 'apps/Tears of the Kingdom 1.2.1 Sequoia.app')
    parser.add_argument('--dry-run', action='store_true', help='只检查路径并显示计划，不解包、不写入密钥、不启动构建')
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        parser.error('请使用 python3.14 运行此脚本')
    for name in ('game', 'update', 'keys', 'firmware', 'source', 'work', 'out'):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    for name in ('game', 'update', 'keys'):
        if not getattr(args, name).is_file():
            parser.error(f'--{name} 文件不存在：{getattr(args, name)}')
    if not args.firmware.exists():
        parser.error(f'固件路径不存在：{args.firmware}')
    builder = args.source / 'build_app.py'
    if not builder.is_file() or not (args.source / 'games/totk/assets/expected-v1.2.1.json').is_file():
        parser.error('请使用本次保留的已适配源码；原始社区分支不能直接打包 1.2.1')
    if '--skip-launch-check' not in builder.read_text():
        parser.error('源码缺少本次的用户自行测试选项，请先恢复适配补丁')
    for path in (args.work, args.out):
        if path == args.source or args.source in path.parents:
            parser.error('工作目录和成品 App 必须放在源码目录外')
    if args.out.suffix.lower() != '.app':
        parser.error('--out 必须以 .app 结尾')
    command = [sys.executable, str(builder), str(args.game), '--keys', '<私有临时密钥>',
               '--update', str(args.update), '--firmware', str(args.firmware),
               '--work', str(args.work), '-o', str(args.out), '--skip-launch-check']
    print('Metal 3 / macOS 15 / 1.2.1；完成打包和签名校验后，由你自行打开测试。', flush=True)
    if args.dry_run:
        print('TOTK_M3=1 ' + shlex.join(command))
        return 0
    args.work.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    firmware = firmware_folder(args.firmware, args.work)
    environment = dict(os.environ, TOTK_M3='1', PYTHONDONTWRITEBYTECODE='1')
    # TemporaryDirectory is private; the key file is 0600 and removed on exit.
    with tempfile.TemporaryDirectory(prefix='private-keys-', dir=args.work) as temporary:
        keys = Path(temporary) / 'prod.keys'
        private_keys(args.keys, keys)
        command[command.index('<私有临时密钥>')] = str(keys)
        command[command.index('--firmware') + 1] = str(firmware)
        result = subprocess.run(command, env=environment)
    if result.returncode:
        print(f'构建未完成，请查看 {args.work / "logs"}；修正后用相同命令继续。', file=sys.stderr)
        return result.returncode
    print(f'成品：{args.out}\n请自行双击 App 完成成品测试。')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f'错误：{error}', file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print('\n已中断；完成的构建缓存会保留。', file=sys.stderr)
        raise SystemExit(130)
