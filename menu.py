"""
Меню выбора режима визуализации.
Запускается лаунчером, устанавливает режим через JSON-файл state.json.
"""

from ursina import *
from mode_static.SuperCubeStatic import SuperCubeStatic
from typing import List
import json
from pathlib import Path

STATE_FILE = Path(__file__).parent / 'state.json'


def temp_to_color(temp: float, min_temp: float = -200.0, max_temp: float = 1000.0) -> color:
    """
    Преобразует температуру в цвет для визуализации (HSV).

    Args:
        temp: Значение температуры.
        min_temp: Минимальная температура диапазона.
        max_temp: Максимальная температура диапазона.

    Returns:
        Цвет в формате Ursina.

    Эта функция - рудимент. Она просто осталась от забагованного куба, который нам понравился, поэтому мы решили добавить его в меню
    """
    t = (temp - min_temp) / (max_temp - min_temp)
    t = max(0.0, min(1.0, t))

    if t < 0.25:
        r = 0
        g = t * 4 * 255
        b = 255
    elif t < 0.5:
        r = 0
        g = 255
        b = 255 - (t - 0.25) * 4 * 255
    elif t < 0.75:
        r = (t - 0.5) * 4 * 255
        g = 255
        b = 0
    else:
        r = 255
        g = 255 - (t - 0.75) * 4 * 255
        b = 0

    return color.rgb(int(r), int(g), int(b))


class Visualisation:
    """Класс для 3D-визуализации теплового куба (используется в режимах статики и динамики).

    Этот класс очевидно не оптимален. Он просто осталась от забагованного куба, который нам понравился, поэтому мы решили добавить его в меню"""

    def __init__(self, size: int = 5) -> None:
        """
        Инициализирует визуализацию.

        Args:
            size: Размер сетки куба.
        """
        EditorCamera()
        self.size: int = size
        self.matCube: SuperCubeStatic = SuperCubeStatic(size)
        self.cubes: List[Entity] = []
        self.wires: List[Entity] = []
        self.create_cube()

    def create_cube(self) -> None:
        """Создаёт 3D-кубики и их проволочные обводки (оторые удачно забаговались) на основе температур."""
        offset = (self.size - 1) * 3.0 / self.size / 2.0
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    pos = (
                        x * 3.0 / self.size - offset,
                        y * 3.0 / self.size - offset,
                        z * 3.0 / self.size - offset,
                    )
                    temperature = self.matCube.get_temp_from_number(x, y, z)

                    cube = Entity(
                        model='cube',
                        position=pos,
                        color=temp_to_color(temperature),
                        scale=3.0 / self.size,
                        collider='box',
                    )
                    wire = Entity(
                        model='cube',
                        position=pos,
                        color=color.black,
                        scale=3.0 / self.size,
                    )

                    cube.indices = (x, y, z)
                    cube.temperature = temperature
                    self.cubes.append(cube)
                    self.wires.append(wire)

    def step(self) -> None:
        """
        Выполняет один шаг симуляции: решает СЛУ и перерисовывает куб.
        Эта функция - рудимент. Она просто осталась от забагованного куба, который нам понравился, поэтому мы решили добавить его в меню
        """
        for cube in self.cubes:
            destroy(cube)
        self.cubes.clear()
        for wire in self.wires:
            destroy(wire)
        self.wires.clear()

        self.matCube.solve_in_numbers()
        self.create_cube()

    def set_size(self, size: int) -> None:
        """
        Изменяет размер куба.

        Args:
            size: Новый размер сетки.
        """
        for cube in self.cubes:
            destroy(cube)
        self.cubes.clear()
        for wire in self.wires:
            destroy(wire)
        self.wires.clear()

        del self.matCube
        self.size = size
        self.matCube = SuperCubeStatic(size)
        self.create_cube()


def set_state_and_quit(mode_value: int) -> None:
    """Записывает выбранный режим в файл и закрывает меню."""
    state = {'mode': mode_value, 'should_continue': True}
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f)
    application.quit()


# === Запуск меню ===
app = Ursina()
window.title = 'Визуализация дискретного уравнения теплопроводности'

viz = Visualisation()

slider = Slider(min=3, max=15, default=5, step=1, position=(-0.5, -0.3))

Button(
    text='Изменение размера',
    scale=(0.25, 0.07),
    position=(-0.5, 0.15),
    on_click=lambda: viz.set_size(int(slider.value)),
)

Text(
    'Визуализация избранных моделей теплопередачи в кубе',
    position=(-0.7, 0.4),
    scale=2,
    color=color.green,
    z=-1,
)

Button(
    text='Режим 1: статический',
    scale=(0.4, 0.07),
    position=(-0.5, -0.4),
    on_click=lambda: set_state_and_quit(1),
)

Button(
    text='Режим 2: динамический',
    scale=(0.4, 0.07),
    position=(0.5, -0.4),
    on_click=lambda: set_state_and_quit(2),
)

Button(
    text='Режим 3: Hyperbolic',
    scale=(0.4, 0.07),
    position=(0.0, -0.55),
    on_click=lambda: set_state_and_quit(3),
)

app.run()