"""scripts/check-tips.py のテスト。

使い方: python -m unittest discover -s scripts/tests

一時ディレクトリに小さな Tips を作り、TIPS_ROOT で検査対象をそこへ向けて実行する。
「問題が無い」ことを確かめる検査なので、問題を仕込んだときに落ちることを1つずつ確かめる。
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
CHECK = SCRIPTS / "check-tips.py"
GEN = SCRIPTS / "gen-readme.py"


class CheckTipsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # 漏えい検査は git ls-files で対象を選ぶので、実リポジトリと同じく git 管理下に置く
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".gitignore", ".claude/sensitive-words.local.txt\n*.local\n")
        # 生成される README がリンクするルールファイル
        self.write(".claude/rules/writing.md", "# Tip の書き方\n")
        self.write("Cat/正常.md", "# 正常な Tip\n\n説明。\n")
        self.regen()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def regen(self):
        subprocess.run([sys.executable, str(GEN), str(self.root)], check=True)

    def run_check(self, *args):
        env = dict(os.environ, TIPS_ROOT=str(self.root), PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(CHECK), *args], env=env, capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout

    def stage_all(self):
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)

    def assert_detects(self, body, expected):
        self.write("Cat/問題.md", body)
        self.regen()
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn(expected, out)

    def test_clean_repo_passes(self):
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("問題 0 件", out)

    def test_missing_title(self):
        self.assert_detects("見出しが無い\n", "1行目が `# タイトル` ではない")

    def test_broken_link(self):
        self.assert_detects("# t\n[x](無い.md)\n", "リンク切れ 無い.md")

    def test_link_inside_code_block_is_ignored(self):
        self.write("Cat/コード.md", "# t\n```md\n[x](無い.md)\n```\n")
        self.regen()
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_aws_access_key(self):
        self.assert_detects("# t\nAKIAABCDEFGHIJKLMNOP\n", "AWS アクセスキーの疑い")

    def test_slack_token(self):
        self.assert_detects("# t\nxoxp-1234567890-abcdef\n", "Slack トークンの疑い")

    def test_private_key(self):
        self.assert_detects("# t\n-----BEGIN RSA PRIVATE KEY-----\n", "秘密鍵の疑い")

    def test_twelve_digit_id(self):
        self.assert_detects("# t\naccount 987654321098\n", "12桁の数字")

    def test_plain_password(self):
        self.assert_detects("# t\npassword = hunter22\n", "平文パスワードの疑い")

    def test_placeholders_are_allowed(self):
        self.write("Cat/例.md", "# t\naccount 123456789012\npassword: <password>\npassword = $DB_PASS\n")
        self.regen()
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_sensitive_words_file(self):
        (self.root / ".claude" / "sensitive-words.local.txt").write_text("# comment\nexamplecorp\n", encoding="utf-8")
        self.assert_detects("# t\nExampleCorp の案件\n", "載せない語「examplecorp」")

    def test_sensitive_word_in_non_markdown_file(self):
        # 設定ファイルのメタデータ（プロファイル名など）に名前が紛れ込んだ実例への備え
        (self.root / ".claude" / "sensitive-words.local.txt").write_text("examplecorp\n", encoding="utf-8")
        self.write("IDE/xml/format.xml", '<profile name="Generated ExampleCorpGateway"/>\n')
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("IDE/xml/format.xml:1: 載せない語「examplecorp」", out)

    def test_secret_in_claude_dir(self):
        self.write(".claude/rules/note.md", "# n\nAKIAABCDEFGHIJKLMNOP\n")
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn(".claude/rules/note.md:2: AWS アクセスキーの疑い", out)

    def test_binary_file_is_skipped(self):
        p = self.root / "Cat" / "img" / "a.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        # 画像の中にたまたま12桁の数字に見えるバイト列があっても、誤検出しない
        p.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00987654321098\xff")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_sensitive_words_file_itself_is_not_scanned(self):
        # 語リストが自分自身に当たると、登録した語がログに並んで漏れる
        (self.root / ".claude" / "sensitive-words.local.txt").write_text("examplecorp\n", encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_gitignored_file_is_not_scanned(self):
        self.write("Cat/memo.local", "AKIAABCDEFGHIJKLMNOP\n")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_scripts_tests_dir_is_not_scanned(self):
        self.write("scripts/tests/fixture.py", "AKIAABCDEFGHIJKLMNOP\n")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_shift_jis_file_is_scanned(self):
        (self.root / ".claude" / "sensitive-words.local.txt").write_text("examplecorp\n", encoding="utf-8")
        p = self.root / "Windows" / "run.bat"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes("rem 起動\r\necho ExampleCorp\r\n".encode("cp932"))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("Windows/run.bat:2: 載せない語「examplecorp」", out)

    # --staged（pre-commit hook）は、作業ツリーではなく次のコミットに入る内容を見る

    def test_staged_clean_passes(self):
        self.stage_all()
        code, out = self.run_check("--staged")
        self.assertEqual(code, 0, out)

    def test_staged_leak_is_caught_even_if_working_tree_is_clean(self):
        self.write("Cat/leak.txt", "AKIAABCDEFGHIJKLMNOP\n")
        self.stage_all()
        self.write("Cat/leak.txt", "clean\n")
        code, out = self.run_check("--staged")
        self.assertEqual(code, 1, out)
        self.assertIn("Cat/leak.txt:1: AWS アクセスキーの疑い", out)

    def test_staged_ignores_unstaged_untracked_file(self):
        self.stage_all()
        self.write("Cat/scratch.txt", "AKIAABCDEFGHIJKLMNOP\n")
        code, out = self.run_check("--staged")
        self.assertEqual(code, 0, out)

    def test_staged_uses_local_word_list(self):
        (self.root / ".claude" / "sensitive-words.local.txt").write_text("examplecorp\n", encoding="utf-8")
        self.write("Cat/x.xml", "<p name='ExampleCorp'/>\n")
        self.stage_all()
        code, out = self.run_check("--staged")
        self.assertEqual(code, 1, out)
        self.assertIn("Cat/x.xml:1: 載せない語「examplecorp」", out)

    def test_staged_stale_readme_keeps_failing(self):
        # 作業ツリーの README を作り直しても、ステージした README が古いままなら止め続ける
        self.write("Cat/新規.md", "# 新しい Tip\n")
        self.stage_all()
        self.regen()
        for _ in range(2):
            code, out = self.run_check("--staged")
            self.assertEqual(code, 1, out)
            self.assertIn("README.md: 生成結果と違っていた", out)

    def test_readme_out_of_sync(self):
        self.write("Cat/新規.md", "# 新しい Tip\n")
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("README.md: 生成結果と違っていた", out)


if __name__ == "__main__":
    unittest.main()
