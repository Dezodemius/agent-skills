# Copyright 2026 Egor Gladkov (Dezodemius), https://github.com/Dezodemius/agent-skills
# SPDX-License-Identifier: Apache-2.0

"""Проверяет репозиторий скилла по единому стандарту.

Использование: python check.py [корень-репозитория]
Стандарт: ровно один скилл в skills/<имя>/SKILL.md, LICENSE в корне,
.claude-plugin/plugin.json и marketplace.json с тем же именем.
"""

import json
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500
MAX_FILE_BYTES = 30 * 1024 * 1024
# Пути внутри скилла, упомянутые в инструкциях: `references/x.md`, [текст](authors/y.md).
PATH_RE = re.compile(r"`([A-Za-z0-9_.\-]+/[A-Za-z0-9_./\-]+)`|\]\(([A-Za-z0-9_.\-]+/[A-Za-z0-9_./\-]+)\)")
MACHINE_PATH_RE = re.compile(r"(?:\b[A-Za-z]:[\/]|/mnt/[a-z]/|/Users/[^/\s]+/|/home/[^/\s]+/)")

errors, warnings = [], []


def find_skill(root):
    skills = sorted(p for p in (root / "skills").glob("*/SKILL.md"))
    if len(skills) != 1:
        errors.append(f"в skills/ должен быть ровно один скилл, найдено: {len(skills)}")
        return None
    return skills[0].parent


def check_skill(skill):
    text = (skill / "SKILL.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        errors.append("SKILL.md: нет YAML-заголовка между строками ---")
        return None
    meta = yaml.safe_load(match[1]) or {}
    body = match[2]
    name, description = meta.get("name"), meta.get("description")
    if name != skill.name:
        errors.append(f"SKILL.md: name «{name}» не совпадает с папкой «{skill.name}»")
    if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
        errors.append("SKILL.md: name — до 64 символов, строчные латинские буквы, цифры и дефисы")
    elif "claude" in name or "anthropic" in name:
        errors.append("SKILL.md: name не может содержать «claude» или «anthropic»")
    if not isinstance(description, str) or not description.strip():
        errors.append("SKILL.md: пустой description")
    else:
        if len(description) > MAX_DESCRIPTION:
            errors.append(f"SKILL.md: description {len(description)} символов, лимит {MAX_DESCRIPTION}")
        if "<" in description or ">" in description:
            errors.append("SKILL.md: в description нельзя использовать угловые скобки < >")
    extra = set(meta) - ALLOWED_KEYS
    if extra:
        errors.append(f"SKILL.md: неизвестные поля заголовка: {', '.join(sorted(extra))}")
    lines = body.count("\n")
    if lines > MAX_BODY_LINES:
        warnings.append(f"SKILL.md: {lines} строк, рекомендуется до {MAX_BODY_LINES}; вынесите детали в справочники")

    for path in sorted(skill.rglob("*")):
        if path.is_file() and path.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"{path.relative_to(skill)}: файл больше 30 МБ")
    for md in sorted(skill.rglob("*.md")):
        content = md.read_text(encoding="utf-8")
        rel = md.relative_to(skill).as_posix()
        if MACHINE_PATH_RE.search(content):
            errors.append(f"{rel}: путь конкретной машины в инструкциях")
        for found in PATH_RE.finditer(content):
            target = (found[1] or found[2]).rstrip(".")
            first = target.split("/")[0]
            # Проверяем только пути в существующие папки скилла: остальное — имена выходных файлов
            # или файлы репозитория вне скилла (../NOTICE), которые сборка кладёт в архив сама.
            if first in {".", ".."} or not (skill / first).is_dir():
                continue
            if not any((base / target).exists() for base in (skill, md.parent)):
                errors.append(f"{rel}: ссылка на несуществующий файл {target}")
    return name


def check_repo(root, name):
    if not (root / "LICENSE").is_file():
        errors.append("нет LICENSE в корне репозитория")
    if not (root / "README.md").is_file():
        errors.append("нет README.md в корне репозитория")
    for manifest in ("plugin.json", "marketplace.json"):
        path = root / ".claude-plugin" / manifest
        if not path.is_file():
            errors.append(f"нет .claude-plugin/{manifest}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        names = [data.get("name")] if manifest == "plugin.json" else [p.get("name") for p in data.get("plugins", [])]
        if name and name not in names:
            errors.append(f".claude-plugin/{manifest}: нет плагина с именем «{name}»")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skill = find_skill(root)
    name = check_skill(skill) if skill else None
    check_repo(root, name)
    for message in warnings:
        print(f"::warning::{message}")
    for message in errors:
        print(f"::error::{message}")
    if errors:
        sys.exit(f"Проверка не пройдена: ошибок {len(errors)}")
    print(f"OK: {name}")


if __name__ == "__main__":
    main()
