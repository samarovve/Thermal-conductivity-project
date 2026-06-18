"""
main.py — лаунчер проекта.
Запускает меню и переключается между режимами визуализации.
Использует state.json для получения выбранного режима.
"""

import subprocess
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / 'state.json'


def get_state():
    """Читает состояние из JSON-файла.
    Возвращает (mode, should_continue). Если файла нет или он повреждён,
    возвращает (0, True).
    """
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('mode', 0), data.get('should_continue', True)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0, True


def clear_state():
    """Удаляет файл состояния, чтобы следующее меню начиналось с чистого листа."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def run_script(script_path: str) -> None:
    """Запускает указанный скрипт (абсолютный или относительный путь) и ждёт его завершения."""
    subprocess.run([sys.executable, script_path])


def main() -> None:
    """Главный цикл лаунчера."""
    while True:
        run_script(str(BASE_DIR / 'menu.py'))

        if not STATE_FILE.exists():
            break

        mode_val, should_cont = get_state()
        clear_state()

        if not should_cont:
            break

        if mode_val == 0:
            continue
        elif mode_val == 1:
            run_script(str(BASE_DIR / 'mode_static' / 'project_visualisation_static_as_file.py'))
        elif mode_val == 2:
            run_script(str(BASE_DIR / 'run_hyperbolic.py'))
        else:
            continue

    print('Программа завершена')


if __name__ == '__main__':
    main()