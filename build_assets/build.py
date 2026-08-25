#!/usr/bin/env python3
"""建置腳本：下載 Pyodide／black／Prism.js 所需檔案，組成單一離線 HTML。
只給維護者（我）用，使用者拿到的是產出的 python_format.html，不需要跑這個。
缺哪個檔案就自動下載到本目錄快取；升級 Pyodide/black 版本時改下面的 URLS 再重跑即可。
"""
import base64
import hashlib
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

# black 與其相依套件的 sha256（自 PyPI JSON API 查證），下載後核對，避免下載過程被竄改的內容被無聲嵌入
KNOWN_SHA256 = {
    "black-26.5.1-py3-none-any.whl": "4ed7f7da04046d2e488437170797d3b4a4ad83906683bcb7dfc68b673bbce5e2",
    "click-8.4.2-py3-none-any.whl": "e6f9f66136c816745b9d65817da91d61d957fb16e02e4dcd0552553c5a197b76",
    "mypy_extensions-1.1.0-py3-none-any.whl": "1be4cccdb0f2482337c4743e60421de3a356cd97508abadd57d47403e94f5505",
    "pathspec-1.1.1-py3-none-any.whl": "a00ce642f577bf7f473932318056212bc4f8bfdf53128c78bbd5af0b9b20b189",
    "platformdirs-4.11.4-py3-none-any.whl": "e34ff91a24bcddc6d939b878bdf3f5c437c9c46fe9e212b1bf455fdf1ee57586",
    "pytokens-0.4.1-py3-none-any.whl": "26cef14744a8385f35d0e095dc8b3a7583f6c953c2e3d269c7f82484bf5ad2de",
    # Pyodide 核心檔案：雜湊來自 GitHub Releases（pyodide-core-0.26.4.tar.bz2）與 jsDelivr CDN
    # 兩個獨立來源交叉比對後一致，取其一寫死。
    "pyodide.js": "c0069107621d5b942a659e737a12e774cc0451feaa2256f475d72e071d844ec7",
    "pyodide.asm.js": "919560652ed3dad3707cb3a394785da1e046fb13dc0defa162058ff230cb7eed",
    "pyodide.asm.wasm": "b7e66a19427a55010ac3367c1b6c64b893f9826f783412945fdf0c3337f3bc94",
    "pyodide-lock.json": "cd50b49de944c579045e122fe8628b31f9ce446379f032f36c05e273d38766e0",
    "python_stdlib.zip": "72894522b791858b9d613ac786b951d8b5094035dcf376313ea24a466810f336",
    # micropip／packaging：Pyodide 團隊會重新打包純 Python wheel，內容跟 PyPI 原始檔不同（版本號相同但位元組不同，
    # 屬正常現象，不是竄改），因此比對基準用 Pyodide 自己的 pyodide-lock.json 宣告值，不是 PyPI 的雜湊。
    "micropip-0.6.0-py3-none-any.whl": "d97c0c01748ddbc52a19944c6a6788c6a8969ed13158c06bc63c6eb02779cd98",
    "packaging-23.2-py3-none-any.whl": "3c30fe6689a35520f2040f4963eae8dbdf6aaa8e326674a13bca3f11514c674a",
}

# Prism.js 檔案：cdnjs 官方 API（api.cdnjs.com）公開的 SRI 雜湊，格式為 sha512 + base64。
KNOWN_SRI_SHA512 = {
    "prism-tomorrow.min.css": "vswe+cgvic/XBoF1OcM/TeJ2FW0OofqAVdCZiEYkd6dwGXthvkSFWOoGGJgS2CW70VK5dQM5Oh+7ne47s74VTg==",
    "prism-line-numbers.min.css": "cbQXwDFK7lj2Fqfkuxbo5iD1dSbLlJGXGpfTDqbggqjHJeyzx88I3rfwjS38WJag/ihH7lzuGlGHpDBymLirZQ==",
    "prism.min.js": "7Z9J3l1+EYfeaPKcGXu3MS/7T+w19WtKQY/n+xzmw4hZhJ9tyYmcUS+4QqAlzhicE5LAfMQSF3iFTK9bQdTxXg==",
    "prism-python.min.js": "AKaNmg8COK0zEbjTdMHJAPJ0z6VeNqvRvH4/d5M4sHJbQQUToMBtodq4HaV4fa+WV2UTfoperElm66c9/8cKmQ==",
    "prism-line-numbers.min.js": "BttltKXFyWnGZQcRWj6osIg7lbizJchuAMotOkdLxHxwt/Hyo+cl47bZU0QADg+Qt5DJwni3SbYGXeGMB5cBcw==",
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

    data = path.read_bytes()

    if filename in KNOWN_SHA256:
        expected = KNOWN_SHA256[filename]
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            path.unlink()
            raise RuntimeError(
                f"{filename} 的 sha256 不符，下載內容可能被竄改或來源已變更\n"
                f"  預期：{expected}\n"
                f"  實際：{actual}"
            )
        print(f"  sha256 核對通過：{actual}")
    elif filename in KNOWN_SRI_SHA512:
        expected = KNOWN_SRI_SHA512[filename]
        actual = base64.b64encode(hashlib.sha512(data).digest()).decode("ascii")
        if actual != expected:
            path.unlink()
            raise RuntimeError(
                f"{filename} 的 sha512 (SRI) 不符，下載內容可能被竄改或來源已變更\n"
                f"  預期：{expected}\n"
                f"  實際：{actual}"
            )
        print(f"  sha512 (SRI) 核對通過：{actual}")


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
