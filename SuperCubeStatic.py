import numpy as np
import sympy as sp
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
from typing import List


class SuperCubeStatic:
    """
    Класс для решения СЛУ и хранения температур куба.

    Автоматически выбирает метод решения в зависимости от мелкости сетки:
    - size < 7: символьное решение (SymPy + linsolve)
    - size >= 7: численное решение с разреженными матрицами (SciPy sparse)

    Attributes:
        size (int): Размер куба (мелкость разбиения).
        data_float (np.ndarray): Трёхмерный массив температур (float).

        data_symbols (np.ndarray): Трёхмерный массив символьных переменных
            (только для символьного режима, при size<7).
        A (csr_matrix): Разреженная матрица системы (только для численного режима, при size хотя бы 7).
    """

    def __init__(self, size: int) -> None:
        """
        Инициализирует решатель для куба заданного размера.

        Args:
            size (int): Размер куба. Должен быть >= 3.

        Raises:
            ValueError: Если size < 3.
        """
        if size < 3:
            raise ValueError('size must >= 3')

        self.size = size
        self.data_float = np.zeros(
            self.size ** 3, dtype=float
        ).reshape(self.size, self.size, self.size)

        if size < 7:
            symbols = []
            for x in range(size):
                for y in range(size):
                    for z in range(size):
                        symbols.append(sp.symbols(f't_{x}{y}{z}'))
            self.data_symbols = np.array(symbols).reshape(size, size, size)
            self.eqs = []
            self.unknowns = []
            self.params = []
            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        if not (x == 0 or x == self.size - 1 or
                                y == 0 or y == self.size - 1 or
                                z == 0 or z == self.size - 1):
                            eq = (6 * self.data_symbols[x, y, z]
                                  - self.data_symbols[x - 1, y, z]
                                  - self.data_symbols[x, y - 1, z]
                                  - self.data_symbols[x, y, z - 1]
                                  - self.data_symbols[x + 1, y, z]
                                  - self.data_symbols[x, y + 1, z]
                                  - self.data_symbols[x, y, z + 1])
                            self.eqs.append(eq)
                            self.unknowns.append(self.data_symbols[x, y, z])
                        else:
                            self.params.append(self.data_symbols[x, y, z])
            self.solutions = list(sp.linsolve(self.eqs, self.unknowns))[0]

        if size >= 7:
            in_size = self.size - 2
            data: List[float] = []
            rows: List[int] = [0]
            columns: List[int] = []
            for z in range(1, self.size - 1):
                for y in range(1, self.size - 1):
                    for x in range(1, self.size - 1):
                        members = 0
                        if z > 1:
                            data.append(-1.0)
                            members += 1
                            columns.append(
                                (z - 2) * in_size * in_size + (y - 1) * in_size + x - 1
                            )
                        if y > 1:
                            data.append(-1.0)
                            members += 1
                            columns.append(
                                (z - 1) * in_size * in_size + (y - 2) * in_size + x - 1
                            )
                        if x > 1:
                            data.append(-1.0)
                            members += 1
                            columns.append(
                                (z - 1) * in_size * in_size + (y - 1) * in_size + x - 2
                            )
                        data.append(6.0)
                        members += 1
                        columns.append(
                            (z - 1) * in_size * in_size + (y - 1) * in_size + x - 1
                        )
                        if x < self.size - 2:
                            data.append(-1.0)
                            members += 1
                            columns.append(
                                (z - 1) * in_size * in_size + (y - 1) * in_size + x
                            )
                        if y < self.size - 2:
                            data.append(-1.0)
                            members += 1
                            columns.append(
                                (z - 1) * in_size * in_size + y * in_size + x - 1
                            )
                        if z < self.size - 2:
                            data.append(-1.0)
                            members += 1
                            columns.append(
                                z * in_size * in_size + (y - 1) * in_size + x - 1
                            )
                        rows.append(rows[-1] + members)

            n = in_size ** 3
            self.A = csr_matrix(
                (data, columns, rows), shape=(n, n)
            )

    def get_size(self) -> int:
        """
        Возвращает размер куба.

        Returns:
            int: Размер куба (частота разбиения).
        """
        return self.size

    def get_temp_from_number(self, x: int, y: int, z: int) -> float:
        """
        Возвращает температуру в заданной точке по индексу кубика.

        Args:
            x (int): Индекс X.
            y (int): Индекс Y.
            z (int): Индекс Z.

        Returns:
            float: Значение температуры.

        Raises:
            IndexError: Если координаты выходят за границы куба.
        """
        try:
            return self.data_float[x, y, z]
        except IndexError:
            raise IndexError('index out of range')

    def set_temp(self, x: int, y: int, z: int, temp: float) -> None:
        """
        Устанавливает температуру в граничной точке по ее индексам

        Args:
            x (int): Индекс X.
            y (int): Индекс Y.
            z (int): Индекс Z.
            temp (float): Значение температуры.

        Raises:
            IndexError: Если координаты выходят за границы куба.
            ValueError: Если точка не является граничной.
        """
        try:
            if (x == 0 or x == self.size - 1 or
                    y == 0 or y == self.size - 1 or
                    z == 0 or z == self.size - 1):
                self.data_float[x, y, z] = temp
            else:
                raise ValueError('incorrect index: not a boundary point')
        except IndexError:
            raise IndexError('index out of range')

    def solve_in_numbers(self) -> None:
        """
        Вычисляет температуры во внутренних точках куба.

        Для size < 7 используется символьное решение с подстановкой значений.
        Для size >= 7 используется численное решение СЛУ с помощью разреженной матрицы.
        """
        if self.size < 7:
            fast_solver = sp.lambdify(
                self.params, self.solutions, modules='numpy'
            )
            params_float: List[float] = []
            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        if (x == 0 or x == self.size - 1 or
                                y == 0 or y == self.size - 1 or
                                z == 0 or z == self.size - 1):
                            params_float.append(
                                self.get_temp_from_number(x, y, z)
                            )
            unknowns_float = fast_solver(*params_float)
            i = 0
            j = 0
            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        if not (x == 0 or x == self.size - 1 or
                                y == 0 or y == self.size - 1 or
                                z == 0 or z == self.size - 1):
                            self.data_float[x, y, z] = unknowns_float[i]
                            i += 1
                        else:
                            self.data_float[x, y, z] = params_float[j]
                            j += 1
        else:
            b: List[float] = []
            for x in range(1, self.size - 1):
                for y in range(1, self.size - 1):
                    for z in range(1, self.size - 1):
                        summ = 0.0
                        if x == 1:
                            summ += self.data_float[x - 1, y, z]
                        if y == 1:
                            summ += self.data_float[x, y - 1, z]
                        if z == 1:
                            summ += self.data_float[x, y, z - 1]
                        if x == self.size - 2:
                            summ += self.data_float[x + 1, y, z]
                        if y == self.size - 2:
                            summ += self.data_float[x, y + 1, z]
                        if z == self.size - 2:
                            summ += self.data_float[x, y, z + 1]
                        b.append(summ)
            sols = spsolve(self.A, b)
            i = 0
            for x in range(1, self.size - 1):
                for y in range(1, self.size - 1):
                    for z in range(1, self.size - 1):
                        self.data_float[x, y, z] = sols[i]
                        i += 1

    def get_temp_from_cords(self, x: float, y: float, z: float, length: float) -> float:
        """
           Получает температуру точки по заданным координатам.
           Если точка принадлежит нескольким кубам (на границе), возвращается среднее их температур.

           Args:
               x: Координата X.
               y: Координата Y.
               z: Координата Z.
               length: Длина ребра куба.

           Returns:
               Средняя температура в точке.

           Raises:
               ValueError: Если координаты вне куба или длина <= 0.
           """
        if length<=0:
            raise ValueError('length must be positive')
        list_of_cubes = []
        cell_size = length / self.size
        if x < 0 or y < 0 or z < 0 or x > length or y > length or z > length:
            raise ValueError('Coordinates out of range')
        for ix in range(self.size):
            for iy in range(self.size):
                for iz in range(self.size):
                    if (x >= ix * cell_size and
                            y >= iy * cell_size and
                            z >= iz * cell_size and
                            x <= (ix + 1) * cell_size and
                            y <= (iy + 1) * cell_size and
                            z <= (iz + 1) * cell_size):
                        list_of_cubes.append(self.get_temp_from_number(ix, iy, iz))
        return sum(list_of_cubes) / len(list_of_cubes)
