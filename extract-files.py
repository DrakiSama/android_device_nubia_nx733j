#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
from pathlib import Path
from extract_utils.main import ExtractUtils, ExtractUtilsModule

if __name__ == '__main__':
    manifest = Path(__file__).with_name('proprietary-files.txt')
    if not manifest.exists():
        raise SystemExit('Review stock/proprietary-files.candidates.txt and create proprietary-files.txt first.')
    module = ExtractUtilsModule('nx733j', 'nubia')
    ExtractUtils.device(module).run()
