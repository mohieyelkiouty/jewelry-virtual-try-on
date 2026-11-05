"""Assemble the deployable static site into ./site.

Copies index.html, catalog.json and every model and thumbnail referenced by the
catalog. Fails if a model exceeds the 25 MiB per-file upload limit.

Usage:
    python build_site.py
"""
import json
import os
import shutil
import sys

LIMIT = 25 * 1024 * 1024
HEAVY = 6 * 1024 * 1024
OUT = "site"

with open("catalog.json", encoding="utf-8") as f:
    data = json.load(f)
items = data if isinstance(data, list) else data.get("items", [])

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)


def copy_asset(path):
    dst = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dst) or OUT, exist_ok=True)
    shutil.copy(path, dst)


for name in ("index.html", "catalog.json"):
    copy_asset(name)

logo = data.get("logo") if isinstance(data, dict) else None
if logo:
    if os.path.exists(logo):
        copy_asset(logo)
    else:
        print(f"missing logo: {logo}")


total = problems = thumbs = 0
for item in items:
    path = item["file"]
    if not os.path.exists(path):
        print(f"missing:    {path}")
        problems += 1
        continue
    size = os.path.getsize(path)
    if size > LIMIT:
        print(f"too large:  {path} ({size / 1e6:.0f} MB)")
        problems += 1
        continue
    copy_asset(path)
    total += size
    print(f"ok          {path}  {size / 1e6:.1f} MB" + ("  (heavy for mobile)" if size > HEAVY else ""))
    thumb = item.get("thumb")
    if thumb and os.path.exists(thumb):
        copy_asset(thumb)
        thumbs += 1

print(f"\nTotal {total / 1e6:.1f} MB, thumbnails {thumbs}/{len(items)}, problems {problems}")
if thumbs < len(items):
    print("Products without a thumbnail fall back to an icon. Generate them with ?thumbs.")
sys.exit(1 if problems else 0)
