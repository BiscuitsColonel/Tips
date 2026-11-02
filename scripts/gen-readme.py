"""README.md を、各カテゴリ配下の .md の1行目（見出し）から生成する。

使い方: python scripts/gen-readme.py
"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
cats = sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name != "scripts")
out = [
    "# Tips",
    "",
    "少しググっただけでは見つけにくい IT の知識をメモする。",
    "",
    "書き方のルールは [.claude/rules/writing.md](.claude/rules/writing.md) にある。",
    "",
]
for c in cats:
    out += [f"## {c}", ""]
    for f in sorted((root / c).rglob("*.md")):
        rel = f.relative_to(root).as_posix()
        title = f.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        sub = f.parent.relative_to(root / c).as_posix()
        label = "" if sub == "." else f"{sub} / "
        out.append(f"- {label}[{title}]({rel})")
    out.append("")
(root / "README.md").write_text("\n".join(out), encoding="utf-8", newline="\n")
