"""Tips の機械的な検査。問題があれば一覧を出して終了コード 1 で終わる。

使い方:
  python scripts/check-tips.py           作業ツリーを検査する（README がずれていれば作り直す）
  python scripts/check-tips.py --staged  ステージ済みの内容（次のコミットに入るもの）を検査する。pre-commit hook が使う

- 各 Tip の1行目が `# タイトル` か
- 相対リンク・画像のリンク先が実在するか
- README.md が scripts/gen-readme.py の生成結果と一致するか
- 認証情報や実在の ID らしい文字列が無いか（Tip だけでなく、設定ファイル・.claude も含め、コミットされうる全テキストファイル。scripts/tests/ は除く）
- .claude/sensitive-words.local.txt（git 管理外。1行1語）に書いた語が無いか（同上）
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ.get("TIPS_ROOT") or Path(__file__).resolve().parent.parent)
SKIP_DIRS = {".git", ".claude", "scripts"}
WORDS = Path(".claude") / "sensitive-words.local.txt"

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

# 漏えい検査から外すもの。テストはダミーの認証情報をわざと置いている
SCAN_SKIP_PREFIX = ("scripts/tests/",)


def tips(root):
    for f in sorted(root.rglob("*.md")):
        rel = f.relative_to(root)
        if rel.parts[0] in SKIP_DIRS or rel.name in ("README.md", "CLAUDE.md"):
            continue
        yield f


def git_files(root):
    """コミットされうるファイル（追跡中と、.gitignore されていない未追跡）。語リストのような無視ファイルは入らない。"""
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "-co", "--exclude-standard"],
                         capture_output=True, check=True).stdout
    return sorted(x.decode("utf-8") for x in out.split(b"\0") if x)


def text_files(root, paths):
    """UTF-8 以外のテキスト（Shift_JIS の .bat 等）も、検出パターンは ASCII なので読めるところで検査する。"""
    for posix in paths:
        f = root / posix
        if posix.startswith(SCAN_SKIP_PREFIX) or not f.is_file():
            continue
        data = f.read_bytes()
        if b"\0" in data[:8000]:
            continue  # 画像などのバイナリ
        yield posix, data.decode("utf-8", errors="replace")


def check(root, paths, words):
    problems = []
    for f in list(tips(root)) + [root / "README.md"]:
        rel = f.relative_to(root).as_posix()
        text = f.read_text(encoding="utf-8")
        if f.name != "README.md" and not text.startswith("# "):
            problems.append(f"{rel}: 1行目が `# タイトル` ではない")
        body = re.sub(r"```.*?```", "", text, flags=re.S)
        for url in re.findall(r"\]\(([^)\s]+)\)", body):
            target = url.split("#")[0]
            if target and not target.startswith(("http://", "https://", "mailto:")) and not (f.parent / target).exists():
                problems.append(f"{rel}: リンク切れ {url}")

    for rel, text in text_files(root, paths):
        for no, line in enumerate(text.splitlines(), 1):
            if any(a in line for a in ALLOWED):
                continue
            for name, pat in PATTERNS.items():
                if re.search(pat, line):
                    problems.append(f"{rel}:{no}: {name}の疑い")
            for w in words:
                if w.lower() in line.lower():
                    problems.append(f"{rel}:{no}: 載せない語「{w}」")

    readme = root / "README.md"
    before = readme.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "gen-readme.py"), str(root)], check=True)
    if before != readme.read_text(encoding="utf-8"):
        problems.append("README.md: 生成結果と違っていた（python scripts/gen-readme.py で作り直してコミットに含める）")
    return problems


def main():
    words = []
    local = ROOT / WORDS
    if local.exists():
        words = [w.strip() for w in local.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("#")]

    if "--staged" in sys.argv[1:]:
        # インデックスを一時ディレクトリへ書き出し、そこだけを見る。作業ツリーにしかない変更や未追跡ファイルは影響しない
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "-C", str(ROOT), "checkout-index", "-a", f"--prefix={tmp}/"], check=True)
            out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True).stdout
            paths = sorted(x.decode("utf-8") for x in out.split(b"\0") if x)
            root = Path(tmp)
            problems = check(root, paths, words)
            count = len(list(tips(root)))
    else:
        problems = check(ROOT, git_files(ROOT), words)
        count = len(list(tips(ROOT)))

    for p in problems:
        print(p)
    print(f"{count} 本を検査、問題 {len(problems)} 件")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
