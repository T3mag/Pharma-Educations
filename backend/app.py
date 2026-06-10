"""Главная точка входа CLI для RAG-системы лекарственного справочника.

Файл нужен как тонкий запускающий слой:
1. Пользователь запускает команды через app.py.
2. Основная логика старого CLI хранится в legacy/cli.py для обратной совместимости.
3. В дальнейшем бизнес-логику можно будет спокойно переносить по модулям,
   не меняя пользовательскую команду запуска.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


def _import_main():
    try:
        from .legacy.cli import main
        return main
    except ImportError:
        pass
    spec = importlib.util.spec_from_file_location(
        "legacy_cli",
        str(Path(__file__).resolve().parent / "legacy" / "cli.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


main = _import_main()


if __name__ == "__main__":
    main()
