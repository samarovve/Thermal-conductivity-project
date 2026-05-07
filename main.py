"""
main.py — лаунчер проекта.
Запускает меню и переключается между режимами визуализации.
"""

import subprocess
import sys
from state_values import should_continue, mode

def run_script(script_name: str) -> None:
    """Запускает скрипт и ждёт его завершения."""
    subprocess.run([sys.executable, script_name])

def main() -> None:
    """Главный цикл лаунчера."""
    while should_continue.value:
        # Запускаем меню
        if mode.value==0:
            run_script('menu.py')
        elif mode.value==1:
            run_script('project_visualisation_static_as_file.py')
        elif mode.value==2:
            run_script('project_visualisation_dynamic_as_file.py')
    print('Программа завершена')