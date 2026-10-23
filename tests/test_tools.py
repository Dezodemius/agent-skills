import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
FIXTURE = Path(__file__).resolve().parent / "fixture"


def run(script, *args):
    return subprocess.run([sys.executable, "-X", "utf8", str(TOOLS / script), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        shutil.copytree(FIXTURE, self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_check_passes(self):
        result = run("check.py", self.repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_rejects_long_description_and_broken_link(self):
        skill = self.repo / "skills" / "demo-skill" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        text = text.replace("Тестовый скилл", "x" * 1100).replace("references/notes.md", "references/missing.md")
        skill.write_text(text, encoding="utf-8")
        result = run("check.py", self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("лимит 1024", result.stdout)
        self.assertIn("references/missing.md", result.stdout)

    def test_package_all_formats_deterministic(self):
        outs = []
        for n in (1, 2):
            out = self.tmp / f"dist{n}"
            result = run("package.py", self.repo, "--version", "1.2.3.4", "--out", out, "--repo", "o/r")
            self.assertEqual(result.returncode, 0, result.stderr)
            outs.append(out)
        for name in ["demo-skill.zip", "demo-skill.skill", "demo-skill.prompt.md", "SHA256SUMS", "RELEASE_NOTES.md"]:
            self.assertEqual((outs[0] / name).read_bytes(), (outs[1] / name).read_bytes(), name)
        with zipfile.ZipFile(outs[0] / "demo-skill.zip") as zf:
            names = zf.namelist()
            self.assertIn("demo-skill/SKILL.md", names)
            self.assertIn("demo-skill/LICENSE", names)
            self.assertEqual(zf.read("demo-skill/VERSION"), b"1.2.3.4\n")
            self.assertNotIn(b"\r\n", zf.read("demo-skill/references/notes.md"))
        prompt = (outs[0] / "demo-skill.prompt.md").read_text(encoding="utf-8")
        self.assertIn("## Файл: references/notes.md", prompt)
        self.assertIn("Тестовый скилл", prompt)

    def test_package_rejects_bad_version(self):
        for version in ["1.0.0", "v1.0.0.0", "1.0.0.0-rc"]:
            result = run("package.py", self.repo, "--version", version, "--out", self.tmp / "x")
            self.assertNotEqual(result.returncode, 0, version)


if __name__ == "__main__":
    unittest.main()
