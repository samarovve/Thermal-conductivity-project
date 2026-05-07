from ursina import *
from SuperCubeStatic import SuperCubeStatic
from typing import Optional, List
from state_values import should_continue, mode

menu_panel: Optional[Panel] = None
menu_elements: List[Entity] = []
menu_field: Optional[InputField] = None

should_continue.value = False

def temp_to_color(temp: float, min_temp: float = -200.0, max_temp: float = 1000.0) -> color:
    """
    Преобразует температуру в HSV-цвет для визуализации.

    Args:
        temp: Значение температуры.
        min_temp: Минимальная температура диапазона (по умолчанию -200).
        max_temp: Максимальная температура диапазона (по умолчанию 1000).

    Returns:
        Цвет в формате Ursina (HSV).
    """
    t = (temp - min_temp) / (max_temp - min_temp)
    t = max(0.0, min(1.0, t))
    return color.hsv(240 - t * 240, 1, 1)  # синий → красный


class Visualisation:
    """Класс для 3D-визуализации теплового куба."""

    def __init__(self, size: int = 5) -> None:
        """
        Инициализирует визуализацию.

        Args:
            size: Размер сетки куба (по умолчанию 5).
        """
        EditorCamera()
        self.size: int = size
        self.matCube: SuperCubeStatic = SuperCubeStatic(size)
        self.cubes: List[Entity] = []
        self.slice: int = size
        self.create_cube()

    def get_slice(self, z_slice: int) -> None:
        """
        Показывает только кубики с индексами Z < z_slice, остальные скрывает.

        Args:
            z_slice: Количество видимых слоёв по оси Z (от 0 до size).
        """
        for i in range(self.size ** 2 * z_slice):
            self.cubes[i].visible = True
            self.cubes[i].collider = 'box'
        for i in range(self.size ** 2 * z_slice, self.size ** 3):
            self.cubes[i].visible = False
            self.cubes[i].collider = None
        self.slice = z_slice

    def create_cube(self) -> None:
        """Создаёт 3D-кубики на основе текущих температур и применяет слайс."""
        offset = (self.size - 1) * 3.0 / self.size / 2.0
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    cube = Entity(
                        model='cube',
                        position=(x * 3.0 / self.size - offset,
                                  y * 3.0 / self.size - offset,
                                  z * 3.0 / self.size - offset),
                        color=temp_to_color(self.matCube.get_temp_from_number(x, y, z)),
                        scale=3.0 / self.size * 0.9,
                        collider='box'
                    )
                    cube.indices = (x, y, z)
                    cube.temperature = self.matCube.get_temp_from_number(x, y, z)
                    self.cubes.append(cube)
        self.get_slice(self.slice)

    def step(self) -> None:
        """Выполняет один шаг симуляции: решение СЛУ и перерисовку куба."""
        for cube in self.cubes:
            destroy(cube)
        self.cubes.clear()
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
        del self.matCube
        self.size = size
        self.slice = size
        self.matCube = SuperCubeStatic(size)
        self.create_cube()

    def set_color(self, x: int, y: int, z: int, color: color) -> None:
        """
        Устанавливает цвет кубика по его индексам (используется для визуального отклика).

        Args:
            x: Индекс X.
            y: Индекс Y.
            z: Индекс Z.
            color: Новый цвет (Ursina).
        """
        self.cubes[x * self.size * self.size + y * self.size + z].color = color


def show_menu(x: int, y: int, z: int, temp: float, is_boundary: bool) -> None:
    """
    Отображает панель информации о кубике с возможностью изменения температуры (если граничный).

    Args:
        x: Индекс X кубика.
        y: Индекс Y кубика.
        z: Индекс Z кубика.
        temp: Текущая температура.
        is_boundary: Индикатор граничного кубика.
    """
    global menu_elements, menu_panel, menu_field

    hide_menu()
    menu_elements = []
    menu_panel = Panel(
        scale=(0.4, 0.3),
        position=(0, 0),
        color=color.red
    )
    menu_elements.append(menu_panel)
    t1 = Text(f'Координаты - [{x}, {y}, {z}]', position=(-0.2, 0.08), scale=0.6,
              color=color.black, z=-1)
    menu_elements.append(t1)
    t2 = Text(f'Температура - {temp:.2f}°C', position=(-0.2, 0.04), scale=0.6,
              color=color.black, z=-1)
    menu_elements.append(t2)
    if is_boundary:
        t3 = Text('Кубик граничный - можно изменить температуру', position=(-0.2, 0.00),
                  scale=0.6, color=color.black, z=-1)
        menu_elements.append(t3)
        menu_field = InputField(
            default_value=str(temp),
            max_lines=1,
            scale=(0.2, 0.07),
            position=(-0.01, -0.06),
            z=-1,
            character_limit=7,
            restrict='-0123456789.'
        )
        menu_elements.append(menu_field)
        set_temp_btn = Button(
            'Изменить температуру',
            position=(0, -0.12),
            scale=(0.4, 0.04),
            color=color.green,
            z=-1,
            on_click=lambda x=x, y=y, z=z: (
                viz.matCube.set_temp(x, y, z,
                                     max(-200.0, min(float(menu_field.text), 1000.0))),
                viz.set_color(x, y, z, color.black),
                setattr(t2, 'text',
                        f'Температура - {max(-200.0, min(float(menu_field.text), 1000.0)):.2f}°C'),
                setattr(menu_field, 'text',
                        str(max(-200.0, min(float(menu_field.text), 1000.0))))
            )
        )
        menu_elements.append(set_temp_btn)
    else:
        t3 = Text('Кубик не граничный - нельзя изменить температуру',
                  position=(-0.2, 0.00), scale=0.6, color=color.black, z=-1)
        menu_elements.append(t3)
    close_btn = Button('X', scale=(0.05, 0.05), position=(0.15, 0.1),
                       color=color.red, z=-1, on_click=hide_menu)
    menu_elements.append(close_btn)


def hide_menu() -> None:
    """Закрывает меню кубика."""
    global menu_elements, menu_panel, menu_field
    for el in menu_elements:
        destroy(el)
    menu_elements.clear()
    menu_panel = None
    menu_field = None


def input(key: str) -> None:
    """
    Обработчик событий ввода Ursina.

    Args:
        key: Нажатая клавиша или событие мыши.
    """
    global menu_panel, menu_panel_cord

    if key == 'left mouse down':
        hovered = mouse.hovered_entity

        if menu_panel or menu_panel_cord:
            return

        if hovered and hasattr(hovered, 'indices'):
            x, y, z = hovered.indices
            temp = hovered.temperature
            boundary = (x == 0 or y == 0 or z == 0 or
                        x == viz.size - 1 or y == viz.size - 1 or z == viz.size - 1)
            show_menu(x, y, z, temp, boundary)


app = Ursina()
window.title = 'Визуализация дискретного уравнения теплопроводности'

viz = Visualisation()

text_slider = Text('Изменение размера', position=(-0.5, -0.25), scale=1.5, color=color.black)

slider = Slider(min=3, max=15, default=5, step=1, position=(-0.5, -0.33))

text_slicer = Text('Изменение слайса', position=(-0.5, -0.37), scale=1.5, color=color.black)

slicer_field = InputField(default_value=str(viz.size), max_lines=1, scale=(0.15, 0.04),
                          position=(-0.43, -0.45), character_limit=2, restrict='0123456789')

Button(
    text='Изменение размера',
    scale=(0.25, 0.07),
    position=(-0.5, 0.15),
    on_click=lambda: (viz.set_size(int(slider.value)),
                      viz.get_slice(int(slider.value)),
                      setattr(slicer_field, 'text', str(slider.value)))
)

Button(
    text='Обновление кубика',
    scale=(0.25, 0.07),
    position=(-0.5, -0.15),
    on_click=lambda: viz.step()
)

Button(
    text='Сделать слайс',
    scale=(0.25, 0.07),
    position=(-0.5, -0.00),
    on_click=lambda: (
        viz.get_slice(min(viz.size, max(1, int(slicer_field.text)))),
        setattr(slicer_field, 'text', str(min(viz.size, max(1, int(slicer_field.text)))))
    )
)

Entity(
    model='quad',
    position=(0, -1.5, -1.5),
    scale=(3.5, 0.05, 0.05),
    color=color.black
)

x_label = Entity(position=(2, -1.5, -1.5))
Text(parent=x_label, text='X', scale=10, color=color.black)

Entity(
    model='quad',
    position=(-1.5, 0, -1.5),
    scale=(3.5, 0.05, 0.05),
    rotation=(0, 0, 90),
    color=color.black
)

y_label = Entity(position=(-1.5, 2, -1.5))
Text(parent=y_label, text='Y', scale=10, color=color.black)

Entity(
    model='quad',
    position=(-1.5, -1.5, 0),
    scale=(3.5, 0.05, 0.05),
    rotation=(0, 90, 0),
    color=color.black
)

z_label = Entity(position=(-1.5, -1.5, 2), rotation=(0, 90, 0))
Text(parent=z_label, text='Z', scale=10, color=color.black)

menu_panel_cord: Optional[Panel] = None
menu_elements_cord: List[Entity] = []


def show_cord_menu() -> None:
    """Открывает меню расчёта температуры по координатам."""
    global menu_panel_cord, menu_elements_cord, text_res
    hide_menu()
    menu_elements_cord = []
    menu_panel_cord = Panel(
        scale=(1, 1),
        position=(0, 0),
        color=color.green,
        z=-2
    )
    menu_elements_cord.append(menu_panel_cord)
    close_btn = Button('X', scale=(0.05, 0.05), position=(0.4, 0.4),
                       color=color.red, z=-3, on_click=hide_cord_menu)
    menu_elements_cord.append(close_btn)

    text_ann = Text('Расчёт температуры по координате', position=(-0.3, 0.35),
                    scale=1.5, color=color.black, z=-3)
    menu_elements_cord.append(text_ann)

    text_length = Text('Длина ребра кубика', position=(-0.3, 0.23),
                       scale=1, color=color.black, z=-3)
    menu_elements_cord.append(text_length)

    field_length = InputField(default_value='1.0', max_lines=1, scale=(0.7, 0.06),
                              position=(0.05, 0.17), character_limit=10,
                              restrict='0123456789.', z=-3)
    menu_elements_cord.append(field_length)

    text_x = Text('Координата x', position=(-0.3, 0.11), scale=1, color=color.black, z=-3)
    menu_elements_cord.append(text_x)

    field_x = InputField(default_value='0', max_lines=1, scale=(0.7, 0.06),
                         position=(0.05, 0.05), character_limit=10,
                         restrict='0123456789.', z=-3)
    menu_elements_cord.append(field_x)

    text_y = Text('Координата y', position=(-0.3, -0.01), scale=1, color=color.black, z=-3)
    menu_elements_cord.append(text_y)

    field_y = InputField(default_value='0', max_lines=1, scale=(0.7, 0.06),
                         position=(0.05, -0.07), character_limit=10,
                         restrict='0123456789.', z=-3)
    menu_elements_cord.append(field_y)

    text_z = Text('Координата z', position=(-0.3, -0.13), scale=1, color=color.black, z=-3)
    menu_elements_cord.append(text_z)

    field_z = InputField(default_value='0', max_lines=1, scale=(0.7, 0.06),
                         position=(0.05, -0.19), character_limit=10,
                         restrict='0123456789.', z=-3)
    menu_elements_cord.append(field_z)

    text_res_ann = Text('Результат расчёта:', position=(-0.3, -0.24),
                        scale=1.5, color=color.red, z=-3)
    menu_elements_cord.append(text_res_ann)

    text_res = Text('', position=(-0.3, -0.29), scale=1.5, color=color.red, z=-3)
    menu_elements_cord.append(text_res)

    def calc_temp_from_coords() -> None:
        """
        Рассчитывает температуру по координатам и выводит результат.

        В случае ошибки ввода выводится сообщение 'Некорректные данные ввода'.
        """
        try:
            temp = viz.matCube.get_temp_from_cords(
                float(field_x.text),
                float(field_y.text),
                float(field_z.text),
                float(field_length.text)
            )
            text_res.text = f'{temp:.2f}°C'
            text_res.color = color.red
        except (ValueError, IndexError):
            text_res.text = 'Некорректные данные ввода'
            text_res.color = color.red

    button_calc = Button(text='Выполнить расчёт',
                         scale=(0.6, 0.07),
                         position=(0.05, -0.4),
                         z=-3,
                         on_click=lambda: calc_temp_from_coords())
    menu_elements_cord.append(button_calc)


def hide_cord_menu() -> None:
    """Закрывает меню расчёта по координатам."""
    global menu_panel_cord, menu_elements_cord
    for el in menu_elements_cord:
        destroy(el)
    menu_elements_cord.clear()
    menu_panel_cord = None


Button(
    text='Найти температуру по координате',
    scale=(0.6, 0.07),
    position=(0.4, 0.4),
    z=2,
    on_click=lambda: show_cord_menu()
)

def close_app_static() -> None:
    """"Закрывает приложение и переводит в режим меню"""
    global should_continue, mode
    should_continue.value = True
    mode.value = 0
    application.quit()

Button(
    text='Перейти в меню',
    scale=(0.6, 0.07),
    position=(0.4, -0.4),
    z=2,
    on_click=lambda: close_app_static()
)


app.run()
