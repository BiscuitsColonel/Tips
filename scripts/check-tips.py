"""Tips の機械的な検査。問題があれば一覧を出して終了コード 1 で終わる。

使い方: python scripts/check-tips.py

- 各 Tip の1行目が `# タイトル` か
- 相対リンク・画像のリンク先が実在するか
- README.md が scripts/gen-readme.py の生成結果と一致するか
- 認証情報や実在の ID らしい文字列が無いか（Tip だけでなく、設定ファイル・.claude も含む全テキストファイル）
- .claude/sensitive-words.local.txt（git 管理外。1行1語）に書いた語が無いか（同上）
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("TIPS_ROOT") or Path(__file__).resolve().parent.parent)
SKIP_DIRS = {".git", ".claude", "scripts"}

# 実在の値でないことが明らかな例示値。これに当たる行は検出から外す
ALLOWED = ["123456789012", "example.com", "example-bucket", "<password>", "<api-key>", "xxxxxxxx"]

PATTERNS = {
    "AWS アクセスキー": r"\b(AKIA|ASIA)[0-9A-Z]{16}\b",
    "Slack トークン": r"\bxox[abprs]-[0-9A-Za-z-]{10,}",
    "秘密鍵": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "SSH 公開鍵": r"\bssh-(rsa|ed25519) AAAA",
    "12桁の数字（AWS アカウント ID の可能性）": r"(?<![0-9.])[0-9]{12}(?![0-9])",
    "平文パスワード": r"(?i)\b(password|passwd|pass|pwd)\s*[:=]\s*['\"]?(?![<$%{])[^\s'\"<>]{4,}",
}


def tips():
    for f in sorted(ROOT.rglob("*.md")):
        rel = f.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or rel.name in ("README.md", "CLAUDE.md"):
            continue
        yield f


# 漏えい検査から外すもの。テストはダミーの認証情報をわざと置いている
SCAN_SKIP = {".git", "__pycache__"}
SCAN_SKIP_FILES = {".claude/sensitive-words.local.txt"}
SCAN_SKIP_PREFIX = ("scripts/tests/",)


def text_files():
    for f in sorted(ROOT.rglob("*")):
        rel = f.relative_to(ROOT)
        if not f.is_file() or SCAN_SKIP & set(rel.parts):
            continue
        posix = rel.as_posix()
        if posix in SCAN_SKIP_FILES or posix.startswith(SCAN_SKIP_PREFIX):
            continue
        try:
            yield posix, f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # 画像などのバイナリ


def main():
    problems = []
    words = []
    local = ROOT / ".claude" / "sensitive-words.local.txt"
    if local.exists():
        words = [w.strip() for w in local.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("#")]

    for f in list(tips()) + [ROOT / "README.md"]:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        if f.name != "README.md" and not text.startswith("# "):
            problems.append(f"{rel}: 1行目が `# タイトル` ではない")
        body = re.sub(r"```.*?```", "", text, flags=re.S)
        for url in re.findall(r"\]\(([^)\s]+)\)", body):
            target = url.split("#")[0]
            if target and not target.startswith(("http://", "https://", "mailto:")) and not (f.parent / target).exists():
                problems.append(f"{rel}: リンク切れ {url}")

    for rel, text in text_files():
        for no, line in enumerate(text.splitlines(), 1):
            if any(a in line for a in ALLOWED):
                continue
            for name, pat in PATTERNS.items():
                if re.search(pat, line):
                    problems.append(f"{rel}:{no}: {name}の疑い")
            for w in words:
                if w.lower() in line.lower():
                    problems.append(f"{rel}:{no}: 載せない語「{w}」")

    readme = ROOT / "README.md"
    before = readme.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "gen-readme.py"), str(ROOT)], check=True)
    after = readme.read_text(encoding="utf-8")
    if before != after:
        problems.append("README.md: 生成結果と違っていた（作り直したのでコミットに含める）")

    for p in problems:
        print(p)
    print(f"{len(list(tips()))} 本を検査、問題 {len(problems)} 件")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
