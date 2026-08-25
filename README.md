# Python 排版轉換器

貼上 Python 程式碼，用瀏覽器內建的 [black](https://github.com/psf/black) 排版、[Prism.js](https://prismjs.com/) 語法高亮。單一 HTML 檔案，不依賴任何外部網路資源，線上開啟或下載後完全離線使用皆可。

線上使用：https://lushinshang.github.io/1150825_python_format/

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `index.html` | GitHub Pages 首頁，含使用說明與下載按鈕 |
| `python_format.html` | 實際工具本體（約 19MB），使用者下載離線使用的就是這一個檔案 |
| `build_assets/build.py` | 維護用建置腳本，重新產生 `python_format.html` |
| `build_assets/template.html` | HTML 模板，含 `%%...%%` 佔位標記 |

一般使用者只需要 `python_format.html`；`build_assets/` 只有要維護/升級版本時才會用到。

## 原理

1. **black** 把貼上的程式碼解析成 AST，依固定規則（行寬 88 字元、雙引號優先等）重新印出，決定排版結果
2. **Prism.js** 對排版後的文字做語法高亮上色，不改動任何字元
3. 兩者都在瀏覽器裡執行：透過 [Pyodide](https://pyodide.org/)（WebAssembly 版 CPython）在瀏覽器內跑一份真正的 Python 直譯器，安裝 black 的 wheel 並直接呼叫 `black.format_str()`

## 為什麼能離線使用

`python_format.html` 把 Pyodide 執行環境、black 及其相依套件、Prism.js 全部以 base64 編碼內嵌在檔案裡，並覆寫 `window.fetch`，讓 Pyodide 初始化時原本要對外的請求改成從內嵌資料直接回應。因此不論連網開啟或離線雙擊打開，執行的都是同一套流程，不會因為沒有網路而打不開。

## 重新建置（維護用）

```bash
cd build_assets
python3 build.py
```

首次執行會自動下載所需的 Pyodide／black／Prism.js 檔案到 `build_assets/` 快取，之後只重跑 base64 內嵌組裝。升級版本時修改 `build.py` 裡的 `URLS`，刪除對應快取檔案後重跑即可。

## 已知限制

- 排版規則固定為 black 預設值，不提供自訂選項
- black 只驗證/重排語法，不檢查程式邏輯正確性
- 首次開啟需要幾秒到十幾秒初始化 Pyodide 執行環境
