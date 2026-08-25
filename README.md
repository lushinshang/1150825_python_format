# Python 排版轉換器

貼上 Python 程式碼，用瀏覽器內建的 [black](https://github.com/psf/black) 排版、[Prism.js](https://prismjs.com/) 語法高亮。單一 HTML 檔案，不依賴任何外部網路資源，線上開啟或下載後完全離線使用皆可。

線上使用：https://lushinshang.github.io/1150825_python_format/

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `index.html` | GitHub Pages 首頁，含使用說明與下載按鈕 |
| `python_format.html` | 實際工具本體（約 19MB），使用者下載離線使用的就是這一個檔案 |
| `python_format.html.sha256` | 上面那個檔案的 sha256，`build.py` 每次建置自動產生，供下載後核對完整性 |
| `verify.html` | 獨立的雜湊驗證工具，瀏覽器內建 Web Crypto API 在本機算 sha256，不用終端機也能核對 |
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

下載完的 18 個檔案都會核對雜湊（black 系列比對 PyPI 官方雜湊、Pyodide 核心檔案比對 GitHub Releases 與 jsDelivr CDN 交叉驗證後的值、Prism.js 比對 cdnjs 官方 SRI），不符就中止建置。這層驗證只在建置當下執行一次，`python_format.html` 本身不含這段邏輯。

建置完成後會自動產生 `python_format.html.sha256`，跟成品一起 commit。使用者下載後可自行核對：

```bash
shasum -a 256 -c python_format.html.sha256
```

不想用終端機的話，開啟 [`verify.html`](https://lushinshang.github.io/1150825_python_format/verify.html) 選檔案即可，頁面會自動帶入官方雜湊值做比對，全程在瀏覽器本機執行、不上傳檔案內容。

sha256 而非 md5：md5 已有實際可行的碰撞攻擊（能構造出雜湊值相同但內容不同的檔案），不適合用在防竄改的完整性驗證；sha256 目前沒有已知的實際可行碰撞攻擊，是業界現行標準。

這只能防下載損毀或第三方轉貼被動手腳；`.sha256` 檔案跟 `python_format.html` 放在同一個 repo，如果 repo 本身被入侵，兩者可能被一起改掉，不在這個核對的防護範圍內。

## 已知限制

- 排版規則固定為 black 預設值，不提供自訂選項
- black 只驗證/重排語法，不檢查程式邏輯正確性
- 首次開啟需要幾秒到十幾秒初始化 Pyodide 執行環境
