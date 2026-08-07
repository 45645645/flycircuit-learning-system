# Knowledge-base maintenance rules

1. 使用繁體中文；專有名詞第一次出現時附英文。
2. 不直接修改 `site/`，所有頁面由 `scripts/build.py` 生成。
3. 原始 PDF 只讀，不複製進公開網站。
4. 論文直接陳述、編輯推論與教學說明必須分開標記。
5. 重要數值與研究主張必須附論文頁碼、章節或圖表定位。
6. 新論文先進入 draft，通過檢查後才能標成 reviewed。
7. 關聯使用有方向、有類型的 edge，不使用意義模糊的單一 `related`。
8. 新增或修改內容後必須執行 `scripts/build.py` 及 `scripts/check.py`。

