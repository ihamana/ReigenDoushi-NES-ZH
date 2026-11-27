#!/bin/sh
# 用法：./build.sh "Reigen Doushi (Japan).nes" [輸出.nes]
set -e
cd "$(dirname "$0")"
if [ -z "$1" ]; then echo '用法：./build.sh 原版ROM.nes [輸出.nes]'; exit 1; fi
python3 -m pip install -q -r requirements.txt 2>/dev/null || true
python3 build.py "$@"
