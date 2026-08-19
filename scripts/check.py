#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import argparse
import os
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRORS = []


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("id") == "paper-meta":
            self.capture = True

    def handle_endtag(self, tag):
        if tag == "script" and self.capture:
            self.capture = False

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        ERRORS.append(f"JSON 無法讀取：{path}: {exc}")
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-missing-sources",
        action="store_true",
        help="公開建置環境沒有本機 PDF 時，只檢查結構化內容與網站。",
    )
    args = parser.parse_args()
    type_data = load(ROOT / "config" / "knowledge-types.json")
    valid_types = {x["id"] for x in type_data.get("types", [])}
    valid_confidence = set(type_data.get("confidence", {}))
    papers = {}
    nodes = {}

    for folder in (ROOT / "papers").iterdir():
        if not folder.is_dir():
            continue
        meta = load(folder / "meta.json")
        claims = load(folder / "claims.json").get("nodes", [])
        pid = meta.get("id")
        if not pid:
            ERRORS.append(f"缺少 paper id：{folder}")
            continue
        if pid in papers:
            ERRORS.append(f"重複 paper id：{pid}")
        papers[pid] = meta
        for field in ["title", "title_zh", "year", "venue", "doi", "learning_order"]:
            if not meta.get(field):
                ERRORS.append(f"{pid} 缺少欄位：{field}")
        if not re.match(r"^10\.\d{4,9}/\S+$", meta.get("doi", "")):
            ERRORS.append(f"{pid} DOI 格式異常：{meta.get('doi')}")
        for node in claims:
            nid = node.get("id")
            if not nid:
                ERRORS.append(f"{pid} 有節點缺少 id")
                continue
            if nid in nodes:
                ERRORS.append(f"重複 node id：{nid}")
            nodes[nid] = node
            if node.get("type") not in valid_types:
                ERRORS.append(f"{nid} 使用未知類型：{node.get('type')}")
            if node.get("confidence") not in valid_confidence:
                ERRORS.append(f"{nid} 使用未知 confidence：{node.get('confidence')}")
            source = node.get("source", {})
            if not source.get("pdf_page") or not source.get("section"):
                ERRORS.append(f"{nid} 缺少 PDF 頁碼或章節定位")

    for pid, meta in papers.items():
        for relation in meta.get("relations", []):
            if relation.get("target") not in papers:
                ERRORS.append(f"{pid} 指向不存在的論文：{relation.get('target')}")
            if not relation.get("type"):
                ERRORS.append(f"{pid} 有未分類的論文關聯")
    for nid, node in nodes.items():
        for dep in node.get("depends_on", []):
            if dep not in nodes:
                ERRORS.append(f"{nid} 指向不存在的依賴節點：{dep}")

    manifest = load(ROOT / "sources" / "manifest.json")
    source_root = Path(os.environ.get("FLYCIRCUIT_PDF_DIR", Path.home() / "Downloads" / "papers"))
    for source in manifest.get("sources", []):
        path = source_root / source["filename"]
        if not path.exists() and not args.allow_missing_sources:
            ERRORS.append(f"找不到原始 PDF：{path}")

    expected = [
        "index.html",
        "papers.html",
        "concepts.html",
        "map.html",
        "tutorials.html",
        "tutorials/neuron-visualization.html",
        "tutorials/assets/TH-F-000020-three-views.png",
        "tutorials/assets/TH-F-000020-spin.webp",
        "tutorials/assets/VGlut-F-300388-three-views.png",
        "tutorials/assets/VGlut-F-300388-spin.webp",
        "tutorials/assets/Gad1-F-400376-three-views.png",
        "assets/style.css",
        "assets/app.js",
    ]
    for relative in expected:
        if not (ROOT / "site" / relative).exists():
            ERRORS.append(f"缺少建置產物：site/{relative}")

    for path in (ROOT / "site" / "papers").glob("*.html"):
        parser = MetadataParser()
        parser.feed(path.read_text(encoding="utf-8"))
        try:
            embedded = json.loads("".join(parser.parts))
            if embedded.get("id") != path.stem:
                ERRORS.append(f"嵌入 metadata id 與檔名不一致：{path.name}")
        except Exception as exc:
            ERRORS.append(f"嵌入 metadata 不是合法 JSON：{path.name}: {exc}")

    if ERRORS:
        print("CHECK FAILED")
        for error in ERRORS:
            print(f"- {error}")
        sys.exit(1)
    print(f"CHECK PASSED: {len(papers)} papers, {len(nodes)} knowledge nodes, all source PDFs present")


if __name__ == "__main__":
    main()
