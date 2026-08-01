#!/bin/bash
# Obsidian の Shell commands プラグイン / Termux ウィジェットから叩く用のラッパー。
# pepstech-site の場所に依存しないよう、このファイル自身の位置から解決する。
set -e
cd "$(dirname "$0")/.."
git pull --ff-only
python3 scripts/publish_journal.py
