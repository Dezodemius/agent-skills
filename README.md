# Скиллы Dezodemius для ИИ-агентов

Каталог моих скиллов в формате [Agent Skills](https://agentskills.io) и общий CD, по которому собирается каждый из них.
Каждый скилл живёт в своём репозитории, релизы выходят по тегу из четырёх чисел (`1.0.0.0`).

## Каталог

### D&D 5e: сюжет → механика → книга

| Скилл | Что делает | Репозиторий |
| --- | --- | --- |
| `folklore-myth` | Сюжеты из фольклора, мифов и священных текстов, адаптированные под вашу тему | [folklore-myth](https://github.com/Dezodemius/folklore-myth) |
| `writers-council` | Консилиум писателей (Толкин, Мартин, Лавкрафт…) разворачивает тему в сюжет с аркой | [writers-council](https://github.com/Dezodemius/writers-council) |
| `pantheons` | Скандинавские, славянские и греческие боги: домены жрецов, культы, зацепки | [pantheons](https://github.com/Dezodemius/pantheons) |
| `dnd-master` | Ваншоты, NPC, фракции, локации и сбалансированные энкаунтеры (редакции 2014 и 2024) | [dnd-master](https://github.com/Dezodemius/dnd-master) |
| `dnd-module` | Приключение-книга как официальный модуль, наполнение карты по картинке | [dnd-module](https://github.com/Dezodemius/dnd-module) |

### D&D 5e: персонажи

| Скилл | Что делает | Репозиторий |
| --- | --- | --- |
| `lss-character` | Лист персонажа для импорта в Long Story Short | [dnd-lss-character-generator](https://github.com/Dezodemius/dnd-lss-character-generator) |
| `pchk-character` | Лист персонажа в стиле «Подземелий Чикен Карри»: PPTX и PDF | [dnd-pchk-character-generator](https://github.com/Dezodemius/dnd-pchk-character-generator) |
| `dnd-character-art` | Портреты персонажей в стиле ПЧК | [dnd-character-art](https://github.com/Dezodemius/dnd-character-art) |

### Общие

| Скилл | Что делает | Репозиторий |
| --- | --- | --- |
| `consul` | Совет из нескольких «личностей» взвешивает решение и выносит вердикт | [consul](https://github.com/Dezodemius/consul) |

## Установка

В каждом релизе три формата одного и того же скилла:

| Файл | Для чего |
| --- | --- |
| `<скилл>.zip` | Стандартный архив Agent Skills: claude.ai и любые агенты с поддержкой скиллов |
| `<скилл>.skill` | Тот же архив для Claude Desktop (открывается двойным кликом) |
| `<скилл>.prompt.md` | Один текстовый файл со всеми справочниками — для чатов без поддержки скиллов |

Ссылка на последний файл: `https://github.com/Dezodemius/<репозиторий>/releases/latest/download/<файл>`.

### Claude

- **claude.ai и Claude Desktop.** Скачайте `.zip`, откройте Настройки → Возможности (Capabilities) → Skills → загрузите архив. Нужен включённый инструмент выполнения кода. В Desktop можно просто открыть `.skill`.
- **Claude Code.** Подключите каталог один раз и ставьте любые скиллы:
  ```
  /plugin marketplace add Dezodemius/agent-skills
  /plugin install dnd-master@dezodemius-skills
  ```
  Либо `npx skills add Dezodemius/<репозиторий>`, либо распакуйте `.zip` в `~/.claude/skills/`.

### Агенты для кода

Универсальный установщик [skills](https://skills.sh) сам знает, куда класть скиллы для Codex, Gemini CLI, Cursor, GitHub Copilot, Windsurf, OpenCode, Cline, Kiro и других:

```
npx skills add Dezodemius/<репозиторий>
```

Вручную — распакуйте `.zip` в папку скиллов агента: для Codex это `~/.agents/skills/` (в старых версиях `~/.codex/skills/`), для проекта обычно `.agents/skills/` или `.claude/skills/` в корне репозитория.

### Чат-ассистенты без поддержки скиллов

Используйте `.prompt.md`: в нём инструкция и все справочники одним файлом.

| Сервис | Как подключить |
| --- | --- |
| **ChatGPT** | В проекте (Projects) или своём GPT: приложите файл и напишите в инструкциях «Следуй инструкции из файла <скилл>.prompt.md». Если в вашем тарифе есть раздел Skills — загрузите туда `.zip` |
| **Gemini** | Создайте Gem, приложите файл в «Знания» и сошлитесь на него в инструкции |
| **Grok** | Проект (Projects) с файлом, либо приложите файл в начале чата |
| **DeepSeek, Qwen, Kimi, GLM** | Приложите файл первым сообщением: «Работай по этой инструкции», дальше пишите запрос |
| **Mistral Le Chat, Perplexity, Microsoft Copilot** | Агент / Space / приложенный файл с той же фразой |
| **Алиса AI, GigaChat** | Приложите файл в начале чата |

В чатах недоступны субагенты, скрипты и картинки из архива — скиллы это учитывают и работают в упрощённом режиме. Скиллам со скриптами (`lss-character`, `pchk-character`) для полноценной работы нужен агент с запуском кода.

## Единый стандарт репозитория скилла

```
skills/<имя>/SKILL.md        # сам скилл и его файлы (references/, assets/, scripts/…)
.claude-plugin/plugin.json   # плагин Claude Code
.claude-plugin/marketplace.json
.github/workflows/ci.yml     # вызывает skill-ci.yml отсюда
.github/workflows/release.yml  # вызывает skill-release.yml отсюда
evals/prompts.md             # эталонные запросы для ручной проверки (по желанию)
README.md, LICENSE, NOTICE
```

**CI** (`skill-ci.yml`) на каждый push и PR: проверка стандарта (`tools/check.py` — заголовок SKILL.md, лимит description 1024 символа, битые ссылки на файлы, манифесты), собственные проверки репозитория (`extra-check`), сборка всех форматов (`tools/package.py`).

**CD** (`skill-release.yml`) по тегу `X.X.X.X`: тег из четырёх чисел и коммит из `main` → те же проверки → релиз с `.zip`, `.skill`, `.prompt.md`, `SHA256SUMS` и инструкцией по установке. Уже опубликованный релиз не перезаписывается.

Выпустить релиз:

```bash
git tag 1.0.0.0 && git push origin 1.0.0.0
```

Параметры для `ci.yml` / `release.yml` репозитория скилла:

| Параметр | По умолчанию | Назначение |
| --- | --- | --- |
| `extra-check` | — | Своя команда проверки, например `python -X utf8 tools/check.py` |
| `os` | `["ubuntu-latest"]` | ОС для проверок; `ubuntu-latest` обязателен |
| `python` | `3.12` | Версия Python |

Зависимости для `extra-check` ставятся из `requirements-dev.txt` в корне репозитория.

## Лицензия

Apache License 2.0 — см. [LICENSE](LICENSE).
