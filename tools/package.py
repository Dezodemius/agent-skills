# Copyright 2026 Egor Gladkov (Dezodemius), https://github.com/Dezodemius/agent-skills
# SPDX-License-Identifier: Apache-2.0

"""Собирает релиз скилла во всех форматах.

Использование: python package.py [корень-репозитория] --version 1.2.3.4 [--out dist] [--repo owner/name]

Результат в папке вывода:
  <имя>.zip        — стандарт Agent Skills: claude.ai, Claude Code, Codex, Gemini CLI, Cursor, Copilot…
  <имя>.skill      — тот же архив для установки двойным кликом в Claude Desktop;
  <имя>.prompt.md  — один файл для чатов без поддержки скиллов: ChatGPT, Gemini, DeepSeek, Qwen, Grok…;
  SHA256SUMS       — контрольные суммы;
  RELEASE_NOTES.md — описание релиза с инструкцией по установке.
Архивы детерминированы: одинаковые исходники дают побайтно одинаковый результат.
"""

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".js", ".ts", ".sh", ".html", ".css", ".xml", ".svg"}
PROMPT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}
LEGAL_FILES = ["LICENSE", "NOTICE"]
FIXED_DATE = (2026, 1, 1, 0, 0, 0)
CATALOG = "https://github.com/Dezodemius/agent-skills"


def skill_files(skill):
    for path in sorted(skill.rglob("*")):
        rel = path.relative_to(skill)
        if not path.is_file() or "__pycache__" in rel.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        yield rel.as_posix(), path


def read(path):
    data = path.read_bytes()
    # Текст в архиве всегда с LF, чтобы сборка на Windows и Linux совпадала.
    return data.replace(b"\r\n", b"\n") if path.suffix.lower() in TEXT_SUFFIXES or not path.suffix else data


def frontmatter(text):
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    meta = {}
    for key in ("name", "description"):
        found = re.search(rf"(?ms)^{key}:\s*(?:>-|>|\|)?\s*(.*?)(?=^[\w-]+:|\Z)", match[1])
        meta[key] = " ".join(found[1].split()).strip("\"'") if found else ""
    return meta, match[2]


def build_prompt(name, version, meta, body, files, repo):
    included, skipped = [], []
    for rel, path in files:
        if rel == "SKILL.md":
            continue
        (included if path.suffix.lower() in PROMPT_SUFFIXES else skipped).append((rel, path))
    out = [
        f"<!-- {name} {version} — однофайловая версия скилла для чат-ассистентов без поддержки Agent Skills. -->",
        f"# Скилл «{name}» — инструкция для ИИ-ассистента",
        "",
        "> Это инструкция-скилл. Следуй ей во всём диалоге. Ссылки на файлы вида `references/…` "
        "ведут к разделам «Файл: …» ниже. Если на платформе недоступно что-то из упомянутого "
        "(субагенты, запуск скриптов, другие скиллы) — выполняй работу сам в рамках диалога.",
        "",
        f"**Назначение:** {meta['description']}",
        "",
        "---",
        "",
        body.strip(),
        "",
    ]
    for rel, path in included:
        lang = {".json": "json", ".yaml": "yaml", ".yml": "yaml", ".csv": "csv"}.get(path.suffix.lower(), "")
        content = read(path).decode("utf-8").strip()
        out += ["", "---", "", f"## Файл: {rel}", ""]
        out += [f"```{lang}", content, "```"] if lang else [content]
    if skipped:
        out += ["", "---", "", "## Файлы, не вошедшие в однофайловую версию", ""]
        out += [f"- `{rel}`" for rel, _ in skipped]
        out += ["", f"Полная версия со всеми файлами — архив `{name}.zip` в релизах https://github.com/{repo}/releases."]
    return ("\n".join(out).rstrip() + "\n").encode("utf-8")


def release_notes(name, version, meta, repo):
    base = f"https://github.com/{repo}/releases/download/{version}"
    return f"""## {name} {version}

{meta['description']}

### Какой файл скачать

| Где пользуетесь | Файл | Как подключить |
| --- | --- | --- |
| claude.ai, Claude Desktop | [`{name}.zip`]({base}/{name}.zip) или [`{name}.skill`]({base}/{name}.skill) | Настройки → Возможности (Capabilities) → Skills → загрузить архив |
| Claude Code | — | `/plugin marketplace add Dezodemius/agent-skills`, затем `/plugin install {name}@dezodemius-skills` |
| Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode и др. | — | `npx skills add {repo}` |
| ChatGPT, Gemini, DeepSeek, Qwen, Grok, Алиса, GigaChat и др. | [`{name}.prompt.md`]({base}/{name}.prompt.md) | Приложить файл в начале чата или вставить в инструкции проекта / GPT / Gem |

Подробно о каждой платформе: {CATALOG}#установка
Контрольные суммы — в `SHA256SUMS`.
"""


def package(root, version, out, repo):
    if not VERSION_RE.fullmatch(version):
        raise SystemExit("Версия — ровно четыре числа через точку, например 1.0.0.0 (без префикса v)")
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    if len(skills) != 1:
        raise SystemExit("В skills/ должен быть ровно один скилл")
    skill = skills[0].parent
    name = skill.name
    files = list(skill_files(skill))
    payload = {f"{name}/{rel}": read(path) for rel, path in files}
    for legal in LEGAL_FILES:
        if (root / legal).is_file() and f"{name}/{legal}" not in payload:
            payload[f"{name}/{legal}"] = read(root / legal)
    payload[f"{name}/VERSION"] = (version + "\n").encode()
    manifest = {"name": name, "version": version, "repository": f"https://github.com/{repo}",
                "files": {key: hashlib.sha256(data).hexdigest() for key, data in sorted(payload.items())}}
    payload[f"{name}/MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()

    out.mkdir(parents=True, exist_ok=True)
    archive = out / f"{name}.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for key, data in sorted(payload.items()):
            info = zipfile.ZipInfo(key, FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, data, compresslevel=9)
    (out / f"{name}.skill").write_bytes(archive.read_bytes())

    meta, body = frontmatter(read(skill / "SKILL.md").decode("utf-8"))
    (out / f"{name}.prompt.md").write_bytes(build_prompt(name, version, meta, body, files, repo))
    notes = release_notes(name, version, meta, repo)
    extra = root / ".github" / "release-notes.md"
    if extra.is_file():
        notes += "\n" + extra.read_text(encoding="utf-8").strip() + "\n"
    (out / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8", newline="\n")

    assets = [f"{name}.zip", f"{name}.skill", f"{name}.prompt.md"]
    sums = "".join(f"{hashlib.sha256((out / a).read_bytes()).hexdigest()}  {a}\n" for a in assets)
    (out / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="\n")
    print(f"{name} {version}: {len(payload)} файлов, zip {archive.stat().st_size} байт")
    return name


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--repo", default="Dezodemius/<repo>")
    args = parser.parse_args()
    root = args.root.resolve()
    package(root, args.version, args.out or root / "dist", args.repo)


if __name__ == "__main__":
    main()
