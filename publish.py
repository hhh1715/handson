#!/usr/bin/env python3
"""把各專案的 HACKMD.md 發布到 HackMD 的「實作筆記」資料夾（私人筆記）。

用法：
  ./publish.py            預覽（dry-run），不送出
  ./publish.py --push     建立或更新 HackMD 筆記

- 第一次發布用 `hackmd-db create`，之後用 `hackmd-db update`；對應的 shortId 記在 .hackmd_ids.json。
- 文件中的本機圖片 `![](xxx.png)` 會改寫成 GitHub raw 網址（IMAGE_BASE），所以發布前要先把 repo push 到 GitHub。
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FOLDER = "實作筆記"
IMAGE_BASE = "https://raw.githubusercontent.com/hhh1715/handson/main"
IDS = ROOT / ".hackmd_ids.json"


def rewrite_images(text: str, project: str) -> str:
    def repl(m):
        alt, path = m.group(1), m.group(2)
        if re.match(r"https?://", path):
            return m.group(0)
        return f"![{alt}]({IMAGE_BASE}/{project}/{path})"
    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", repl, text)


def main() -> int:
    push = "--push" in sys.argv
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    for doc in sorted(ROOT.glob("[0-9][0-9]_*/HACKMD.md")):
        project = doc.parent.name
        text = rewrite_images(doc.read_text(encoding="utf-8"), project)
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
            print("   (dry-run)")
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
