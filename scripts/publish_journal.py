#!/usr/bin/env python3
"""
Obsidian の日報 (Daily/*.md) のうち publish: true が付いたものを
pepstech-site の notes/ 以下と index.html の「書きもの」一覧に反映する。

使い方:
    python3 scripts/publish_journal.py

git add / commit / push はしない。生成結果を確認してから自分で行うこと。
"""

import re
import subprocess
import sys
from pathlib import Path

if "com.termux" in str(Path.home()):
    # Android (Termux): Syncthing 経由で ~/storage/shared/Documents 配下に同期している
    VAULT_DAILY = Path.home() / "storage" / "shared" / "Documents" / "Pepstech-Journal" / "Daily"
else:
    VAULT_DAILY = Path.home() / "Documents" / "Pepstech-Journal" / "Daily"

SITE_DIR = Path(__file__).resolve().parent.parent
NOTES_DIR = SITE_DIR / "notes"
INDEX_HTML = SITE_DIR / "index.html"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    meta = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def md_to_html(body: str) -> str:
    result = subprocess.run(
        ["pandoc", "--from=markdown", "--to=html"],
        input=body,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("pandoc failed")
    return result.stdout.strip()


def make_excerpt(body: str, limit: int = 60) -> str:
    for line in body.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return (line[:limit] + "…") if len(line) > limit else line
    return ""


def note_page_html(title: str, date: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Pepstech</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>

<header class="masthead">
  <div class="wrap masthead-in">
    <a href="../index.html#top" class="wordmark">Pepstech</a>
    <nav>
      <a href="../index.html#about">はじめに</a>
      <a href="../index.html#notes">書きもの</a>
      <a href="../index.html#making">つくったもの</a>
      <a href="../index.html#contact">連絡先</a>
    </nav>
  </div>
</header>

<main>
  <section class="block">
    <div class="wrap two-col">
      <h2 class="block-title">{date}</h2>
      <div class="block-body">
        <h1 style="font-size:1.6rem;font-weight:500;margin:0 0 1.8rem;">{title}</h1>
        {body_html}
        <p style="margin-top:3rem;"><a class="quiet-link" href="../index.html#notes">← 書きもの一覧へ</a></p>
      </div>
    </div>
  </section>
</main>

<footer class="colophon">
  <div class="wrap">
    <p>Pepstech — <span id="year"></span></p>
  </div>
</footer>

<script>
  document.getElementById('year').textContent = new Date().getFullYear();
</script>

</body>
</html>
"""


def main():
    if not VAULT_DAILY.exists():
        print(f"Vault の Daily フォルダが見つかりません: {VAULT_DAILY}", file=sys.stderr)
        sys.exit(1)

    NOTES_DIR.mkdir(exist_ok=True)

    entries = []
    for md_path in sorted(VAULT_DAILY.glob("*.md")):
        if md_path.stem.startswith("_"):
            continue  # テンプレート除外

        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        if meta.get("publish", "").lower() != "true":
            continue

        date = meta.get("date", "").strip()
        if not DATE_RE.match(date):
            date = md_path.stem if DATE_RE.match(md_path.stem) else ""
        if not date:
            print(f"[skip] 日付が特定できません: {md_path.name}", file=sys.stderr)
            continue

        title = meta.get("title") or date
        excerpt = meta.get("excerpt") or make_excerpt(body)
        slug = date

        body_html = md_to_html(body)
        note_html = note_page_html(title, date, body_html)
        out_path = NOTES_DIR / f"{slug}.html"
        out_path.write_text(note_html, encoding="utf-8")

        entries.append({
            "slug": slug,
            "date": date,
            "title": title,
            "excerpt": excerpt,
        })
        print(f"[write] notes/{slug}.html  ({title})")

    entries.sort(key=lambda e: e["date"], reverse=True)

    items = []
    for e in entries:
        display_date = e["date"].replace("-", ".")
        items.append(
            "          <li>\n"
            f'            <a href="notes/{e["slug"]}.html">\n'
            f'              <span class="entry-date">{display_date}</span>\n'
            f'              <span class="entry-title">{e["title"]}</span>\n'
            f'              <span class="entry-excerpt">{e["excerpt"]}</span>\n'
            "            </a>\n"
            "          </li>"
        )
    block = "\n".join(items)

    index_text = INDEX_HTML.read_text(encoding="utf-8")
    new_index_text = re.sub(
        r"<!-- ENTRIES:START -->.*?<!-- ENTRIES:END -->",
        "<!-- ENTRIES:START -->\n" + block + "\n<!-- ENTRIES:END -->",
        index_text,
        flags=re.DOTALL,
    )

    if new_index_text == index_text and entries:
        print("[info] index.html の一覧に変更なし")
    INDEX_HTML.write_text(new_index_text, encoding="utf-8")

    print(f"\n{len(entries)} 件を反映しました。内容を確認してから git add / commit / push してください。")


if __name__ == "__main__":
    main()
