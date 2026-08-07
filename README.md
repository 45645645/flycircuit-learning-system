# FlyCircuit Connectomics Learning System

這是一個以「層級學習地圖 + Wiki 知識單元 + 原始論文證據」為核心的可維護知識庫。

> 狀態：個人開發中的 pilot。內容仍在持續整理、驗證與調整。

第一版聚焦兩篇 Current Biology 核心論文：

- Chiang et al. (2011)：建立 FlyCircuit、標準腦與腦區連結圖譜。
- Shih et al. (2015)：從 FlyCircuit 影像建立有向加權網路並分析資訊流。

## 建置

```bash
python3 scripts/build.py
python3 scripts/check.py
```

完成後開啟 `site/index.html`。

## 線上發布

公開網站預計由 GitHub Pages 發布；repository 不包含原始論文 PDF。


## 資料原則

- `sources/`：原始 PDF 的唯讀位置資訊，不複製、不修改下載資料夾中的 PDF。
- `papers/*/meta.json`：論文的機器可讀資料。
- `papers/*/content.md`：人類可讀的整理內容。
- `papers/*/claims.json`：可追溯的知識節點及其依賴關係。
- `site/`：完全自動生成，不直接修改。

## 第一版限制

- 目前是兩篇核心論文的 pilot，不是六篇論文的完成版。
- 公開網站只使用 DOI 或合法公開網址，不暴露本機 PDF 路徑。
- 本機檢查預設在 `~/Downloads/papers` 尋找 PDF；可用 `FLYCIRCUIT_PDF_DIR` 指定其他位置。
- 心智圖先採可點擊的層級圖，不依賴外部 JavaScript 套件。
