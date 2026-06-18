import numpy as np
from mode_hyperbolic.RK4 import RK4


class SolverFourierTherm:
    """
    Численный решатель 3D уравнения теплопроводности (параболическое/Фурье):
        ∂T/∂t = a·∇²T + S(x,y,z) - h·(T - T_air)

    Граничные условия:
        - Нижняя грань (z=0): T = 0 (лёд)
        - Верхняя грань (z=L): адиабатическая (∂T/∂z = 0)
        - Боковые грани: адиабатические + объёмный теплообмен с воздухом

    Начальное условие:
        Линейный профиль по z: T(z) = (z/L) * T0,
        где T0 — начальная температура на верхней грани.
        Если T_top задана, температура верхней грани в начальный момент = T_top.
    """

    def __init__(self, N: int, T0: float, a: float, h: float,
                 P: float, T_air: float, dt: float,
                 L: float, rho_cp: float, T_top: float = None):
        """
        Параметры:
        -----------
        N : int
            Число узлов по каждому направлению (кубическая сетка N×N×N).
            Должно быть >= 3.
        T0 : float
            Начальная температура на верхней грани (z = L).
            Внутри куба температура линейно меняется от 0 (дно) до T0 (верх).
        a : float
            Температуропроводность материала (м²/с).
        h : float
            Коэффициент объёмного теплообмена с воздухом (1/с).
        P : float
            Мощность источника (паяльника), Вт.
        T_air : float
            Температура воздуха.
        dt : float
            Шаг по времени.
        L : float
            Физический размер куба (м).
        rho_cp : float
            Объёмная теплоёмкость (Дж/(м³·К)).
        T_top : float или None
            Если задано, температура верхней грани в начальный момент будет равна T_top.
            На дальнейшую эволюцию не влияет (грань адиабатическая).

        Raises:
            ValueError: если N < 3.
        """
        if N < 3:
            raise ValueError(
                f"Число узлов N должно быть >= 3. Получено N={N}"
            )

        self.L = L
        self.delta = L / (N - 1)
        self.a = a
        self.h = h
        self.P = P
        self.T_air = T_air
        self.dt = dt
        self.N = N

        z_ratio = np.linspace(0, 1, N).reshape(1, 1, N)
        self.arr_T = np.tile(z_ratio * T0, (N, N, 1))
        self.arr_T[:, :, 0] = 0.0
        if T_top is not None:
            self.arr_T[:, :, -1] = T_top

        self.S = np.zeros_like(self.arr_T)
        iy = N // 2
        iz = N // 2
        vol_src = 27 * (self.delta ** 3)
        self.S[0, iy-1:iy+2, iz-1:iz+2] = self.P / (vol_src * rho_cp)

        self.rho_cp = rho_cp
        self.a_dimless = a

        self.state = [self.arr_T.copy(), 0.0]
        self.funcs_rk4 = [self.dT_dt, self.dt_dt]
        self.step = 0


    def laplacian_vectorized(self, T: np.ndarray) -> np.ndarray:
        h2 = self.delta ** 2


        d2x = np.zeros_like(T)
        d2x[1:-1, :, :] = (T[2:, :, :] - 2*T[1:-1, :, :] + T[:-2, :, :]) / h2
        d2x[0, :, :] = 2.0 * (T[1, :, :] - T[0, :, :]) / h2
        d2x[-1, :, :] = 2.0 * (T[-2, :, :] - T[-1, :, :]) / h2


        d2y = np.zeros_like(T)
        d2y[:, 1:-1, :] = (T[:, 2:, :] - 2*T[:, 1:-1, :] + T[:, :-2, :]) / h2
        d2y[:, 0, :] = 2.0 * (T[:, 1, :] - T[:, 0, :]) / h2
        d2y[:, -1, :] = 2.0 * (T[:, -2, :] - T[:, -1, :]) / h2


        d2z = np.zeros_like(T)
        d2z[:, :, 1:-1] = (T[:, :, 2:] - 2*T[:, :, 1:-1] + T[:, :, :-2]) / h2
        d2z[:, :, 0] = (T[:, :, 1] - 2*T[:, :, 0]) / h2                # дно: фиксированный 0°C
        d2z[:, :, -1] = 2.0 * (T[:, :, -2] - T[:, :, -1]) / h2

        return d2x + d2y + d2z


    def dT_dt(self, T: np.ndarray, t: float) -> np.ndarray:
        lap = self.laplacian_vectorized(T)
        return self.a_dimless * lap + self.S - self.h * (T - self.T_air)

    def dt_dt(self, T: np.ndarray, t: float) -> float:
        return 1.0

    def next_step_integration(self) -> None:
        self.arr_T, t_new = RK4(self.state, self.funcs_rk4, self.dt)
        # Жёстко фиксируем только лёд внизу
        self.arr_T[:, :, 0] = 0.0
        self.step += 1
        self.state = [self.arr_T.copy(), t_new]

    def set_T_air(self, value: float) -> None:
        self.T_air = value

    def set_a(self, value: float) -> None:
        self.a = value
        self.a_dimless = value

    def set_h(self, value: float) -> None:
        self.h = value

    def set_P(self, value: float) -> None:
        self.P = value
        iy = self.N // 2
        iz = self.N // 2
        vol_src = 27 * (self.delta ** 3)
        self.S.fill(0.0)
        self.S[0, iy-1:iy+2, iz-1:iz+2] = self.P / (vol_src * self.rho_cp)

    def set_dt(self, value: float) -> None:
        self.dt = value

    def get_temperature_field(self) -> np.ndarray:
        """Возвращает копию текущего поля температур."""
        return self.arr_T.copy()
