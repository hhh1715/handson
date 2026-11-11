#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""把各專案的 HACKMD.md 發布到 HackMD 的「實作筆記」資料夾（私人筆記）。

用法：
  ./publish.py            預覽（dry-run），不送出任何寫入
  ./publish.py --push     必要時建立資料夾，再建立或更新 HackMD 筆記

- 資料夾：先以 GET /folders 查詢 FOLDER；不存在時以 POST /folders 建立
  （HackMD API v1，見 https://api.hackmd.io/v1/docs 的 User Folders）。dry-run 只做 GET。
- 筆記：第一次發布用 `hackmd-db create`，之後用 `hackmd-db update`；shortId 記在 .hackmd_ids.json。
- 文件中的本機圖片 `![](xxx.png)` 會改寫成 GitHub raw 網址（IMAGE_BASE），發布前要先把 repo push 到 GitHub。
- API token 與 hackmd-db 相同：環境變數 HACKMD_API_TOKEN，或 ~/hackmd-db/config.toml 的 [auth].token。
  token 只放在 Authorization 標頭，不會印出。
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FOLDER = "實作筆記"
IMAGE_BASE = "https://raw.githubusercontent.com/hhh1715/handson/main"
IDS = ROOT / ".hackmd_ids.json"
API = "https://api.hackmd.io/v1"
HACKMD_DB_CONFIG = Path.home() / "hackmd-db" / "config.toml"


def load_token() -> str:
    token = os.environ.get("HACKMD_API_TOKEN", "")
    if not token and HACKMD_DB_CONFIG.exists():
        token = tomllib.loads(HACKMD_DB_CONFIG.read_text(encoding="utf-8")).get("auth", {}).get("token", "")
    if not token:
        sys.exit("[fail] 找不到 HackMD token：設定 HACKMD_API_TOKEN 或 ~/hackmd-db/config.toml")
    return token


def api(method: str, path: str, token: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}/{path}", data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, None


def ensure_folder(name: str, push: bool) -> bool:
    """確認個人工作區有名為 name 的資料夾；push 時不存在就建立。回傳是否可以繼續。"""
    token = load_token()
    status, folders = api("GET", "folders", token)
    if status != 200:
        print(f"[fail] GET /folders -> HTTP {status}")
        return False
    matches = [f for f in folders if f.get("name") == name]
    if len(matches) > 1:
        print(f"[fail] 有 {len(matches)} 個名為「{name}」的資料夾，請先在 HackMD 上改名")
        return False
    if matches:
        print(f"[ok] 資料夾「{name}」已存在 (id {matches[0]['id']})")
        return True
    if not push:
        print(f"[pending] 資料夾「{name}」不存在；--push 時會呼叫 POST /folders {{\"name\": \"{name}\"}}")
        return True
    status, folder = api("POST", "folders", token, {"name": name})
    if status != 201 or not folder:
        print(f"[fail] POST /folders -> HTTP {status}")
        return False
    print(f"[done] 已建立資料夾「{name}」(id {folder['id']})")
    return True


def rewrite_images(text: str, project: str) -> str:
    # 支援 HackMD 的尺寸語法，例如 ![](a.png =90%x)
    def repl(m):
        alt, path, size = m.group(1), m.group(2), m.group(3) or ""
        if re.match(r"https?://", path):
            return m.group(0)
        return f"![{alt}]({IMAGE_BASE}/{project}/{path}{size})"
    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(\s+=[^)]*)?\)", repl, text)


def main() -> int:
    push = "--push" in sys.argv
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    docs = sorted(ROOT.glob("[0-9][0-9]_*/HACKMD.md"))
    if any(d.parent.name not in ids for d in docs) and not ensure_folder(FOLDER, push):
        return 1
    for doc in docs:
        project = doc.parent.name
        text = rewrite_images(doc.read_text(encoding="utf-8"), project)
        local = [p for p in re.findall(r"!\[[^\]]*\]\(([^)\s]+)", text) if not p.startswith("http")]
        if local:
            print(f"[fail] {project}: 仍有未改寫的本機圖片 {local}")
            return 1
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(text)
            tmp = f.name
        if project in ids:
            cmd = ["hackmd-db", "update", ids[project], tmp]
        else:
            cmd = ["hackmd-db", "create", tmp, "--folder", FOLDER]
        if push:
            cmd.append("--push")
        out = subprocess.run(cmd, capture_output=True, text=True)
        print(f"== {project}: {' '.join(cmd[:3])} -> exit {out.returncode}")
        if not push:
            imgs = re.findall(r"!\[[^\]]*\]\((\S+?)\)", text)
            print(f"   (dry-run) 標題：{text.splitlines()[0][2:]}")
            for u in imgs:
                print(f"   圖片 {u}")
        elif out.returncode == 0 and project not in ids:
            m = re.search(r"created (\S+)", out.stdout)
            if m:
                ids[project] = m.group(1)
                IDS.write_text(json.dumps(ids, indent=2))
            print("  ", out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "")
        else:
            print("  ", (out.stdout + out.stderr).strip()[-300:])
        Path(tmp).unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
