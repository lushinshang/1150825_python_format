#!/usr/bin/env python3
"""建置腳本：下載 Pyodide／black／Prism.js 所需檔案，組成單一離線 HTML。
只給維護者（我）用，使用者拿到的是產出的 python_format.html，不需要跑這個。
缺哪個檔案就自動下載到本目錄快取；升級 Pyodide/black 版本時改下面的 URLS 再重跑即可。
"""
import base64
import pathlib
import urllib.request

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "python_format.html"

PYODIDE_BASE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
PRISM_BASE = "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/"

# 檔名 -> 下載網址。black 與其相依套件的 wheel 網址含 PyPI 的雜湊路徑，不是固定樣式，寫死。
URLS = {
    "pyodide.js": PYODIDE_BASE + "pyodide.js",
    "pyodide.asm.js": PYODIDE_BASE + "pyodide.asm.js",
    "pyodide.asm.wasm": PYODIDE_BASE + "pyodide.asm.wasm",
    "pyodide-lock.json": PYODIDE_BASE + "pyodide-lock.json",
    "python_stdlib.zip": PYODIDE_BASE + "python_stdlib.zip",
    "micropip-0.6.0-py3-none-any.whl": PYODIDE_BASE + "micropip-0.6.0-py3-none-any.whl",
    "packaging-23.2-py3-none-any.whl": PYODIDE_BASE + "packaging-23.2-py3-none-any.whl",
    "prism-tomorrow.min.css": PRISM_BASE + "themes/prism-tomorrow.min.css",
    "prism-line-numbers.min.css": PRISM_BASE + "plugins/line-numbers/prism-line-numbers.min.css",
    "prism.min.js": PRISM_BASE + "prism.min.js",
    "prism-python.min.js": PRISM_BASE + "components/prism-python.min.js",
    "prism-line-numbers.min.js": PRISM_BASE + "plugins/line-numbers/prism-line-numbers.min.js",
    "black-26.5.1-py3-none-any.whl": "https://files.pythonhosted.org/packages/94/51/f975cae76d44274cc2868dc9040ac5d58d464784610234455b4e7b19c6ef/black-26.5.1-py3-none-any.whl",
    "click-8.4.2-py3-none-any.whl": "https://files.pythonhosted.org/packages/fb/e2/79c688af8b210d232694e31e59da9f6ec747bae31c3f5946e4e9b98860d5/click-8.4.2-py3-none-any.whl",
    "mypy_extensions-1.1.0-py3-none-any.whl": "https://files.pythonhosted.org/packages/79/7b/2c79738432f5c924bef5071f933bcc9efd0473bac3b4aa584a6f7c1c8df8/mypy_extensions-1.1.0-py3-none-any.whl",
    "pathspec-1.1.1-py3-none-any.whl": "https://files.pythonhosted.org/packages/f1/d9/7fb5aa316bc299258e68c73ba3bddbc499654a07f151cba08f6153988714/pathspec-1.1.1-py3-none-any.whl",
    "platformdirs-4.11.4-py3-none-any.whl": "https://files.pythonhosted.org/packages/28/be/0ff05fcd2938fb58ad9219bd54135968342d214737e012d62d43f06a2dd6/platformdirs-4.11.4-py3-none-any.whl",
    "pytokens-0.4.1-py3-none-any.whl": "https://files.pythonhosted.org/packages/c6/78/397db326746f0a342855b81216ae1f0a32965deccfd7c830a2dbc66d2483/pytokens-0.4.1-py3-none-any.whl",
}

TEXT_INLINE = {
    "%%PRISM_TOMORROW_CSS%%": "prism-tomorrow.min.css",
    "%%PRISM_LINE_NUMBERS_CSS%%": "prism-line-numbers.min.css",
    "%%PRISM_JS%%": "prism.min.js",
    "%%PRISM_PYTHON_JS%%": "prism-python.min.js",
    "%%PRISM_LINE_NUMBERS_JS%%": "prism-line-numbers.min.js",
    "%%PYODIDE_JS%%": "pyodide.js",
    "%%PYODIDE_ASM_JS%%": "pyodide.asm.js",
}

# Pyodide 執行期會用 fetch() 動態抓的二進位檔案，全部 base64 內嵌並透過攔截 fetch 供應
BINARY_EMBED = [
    ("pyodide.asm.wasm", "application/wasm"),
    ("python_stdlib.zip", "application/zip"),
    ("pyodide-lock.json", "application/json"),
    ("micropip-0.6.0-py3-none-any.whl", "application/zip"),
    ("packaging-23.2-py3-none-any.whl", "application/zip"),
    ("black-26.5.1-py3-none-any.whl", "application/zip"),
    ("click-8.4.2-py3-none-any.whl", "application/zip"),
    ("mypy_extensions-1.1.0-py3-none-any.whl", "application/zip"),
    ("pathspec-1.1.1-py3-none-any.whl", "application/zip"),
    ("platformdirs-4.11.4-py3-none-any.whl", "application/zip"),
    ("pytokens-0.4.1-py3-none-any.whl", "application/zip"),
]


def ensure_downloaded(filename):
    path = HERE / filename
    if path.exists():
        return
    url = URLS[filename]
    print(f"downloading {filename} <- {url}")
    urllib.request.urlretrieve(url, path)


def main():
    for filename in TEXT_INLINE.values():
        ensure_downloaded(filename)
    for filename, _ in BINARY_EMBED:
        ensure_downloaded(filename)

    template = (HERE / "template.html").read_text(encoding="utf-8")

    for marker, filename in TEXT_INLINE.items():
        content = (HERE / filename).read_text(encoding="utf-8")
        assert marker in template, f"找不到 marker {marker}"
        template = template.replace(marker, content)

    entries = []
    for filename, mime in BINARY_EMBED:
        raw = (HERE / filename).read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        entries.append(f'  "{filename}": {{data: "{b64}", type: "{mime}"}}')
        print(f"embedded {filename}: {len(raw):,} bytes raw -> {len(b64):,} bytes base64")

    assets_json = ",\n".join(entries)
    assert "%%EMBEDDED_ASSETS_JSON%%" in template
    template = template.replace("%%EMBEDDED_ASSETS_JSON%%", assets_json)

    OUT.write_text(template, encoding="utf-8")
    size = OUT.stat().st_size
    print(f"\n輸出：{OUT}（{size:,} bytes ≈ {size/1024/1024:.1f} MB）")


if __name__ == "__main__":
    main()
