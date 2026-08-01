#!/bin/bash
# Obsidian の Shell commands プラグインから叩く用のラッパー。
# pepstech-site の場所に依存しないよう、このファイル自身の位置から解決する。
set -e
cd "$(dirname "$0")/.."
python3 scripts/publish_journal.py
