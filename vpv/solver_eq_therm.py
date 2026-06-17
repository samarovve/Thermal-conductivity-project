import numpy as np
from mode_hyperbolic.RK4 import RK4

class SolverFourierTherm:
    """
    Численный решатель 3D уравнения теплопроводности (параболическое/Фурье):
        ∂T/∂t = a·∇²T + S(x,y,z) - h·(T - T_air)
    Граничные условия:
        - Нижняя грань (z=0): T = 0 (лед)
        - Остальные грани: адиабатические + объёмный теплообмен с воздухом
    Начальное условие: T(x,y,z,0) = T0
    """
    def __init__(self, N: int, T0: float, a: float, h: float,
                 P: float, T_air: float, dt: float):
        self.a = a          # Температуропроводность
        self.h = h          # Коэф. теплообмена с воздухом (1/с)
        self.P = P          # Мощность паяльника (Вт)
        self.T_air = T_air  # Температура воздуха
        self.dt = dt
        self.N = N
        self.delta = 1.0 / (N - 1)

        # Поле температур
        self.arr_T = np.full((N, N, N), T0, dtype=np.float64)
        self.arr_T[:, :, 0] = 0.0  # Нижняя грань = 0°C (лед)

        # Сетки координат
        self.x_lin = np.linspace(0, 1, N)
        self.y_lin = np.linspace(0, 1, N)
        self.z_lin = np.linspace(0, 1, N)

        # Источник тепла (паяльник в центре грани x=0)
        self.S = np.zeros_like(self.arr_T)
        iy = np.argmin(np.abs(self.y_lin - 0.5))
        iz = np.argmin(np.abs(self.z_lin - 0.5))
        # Распределяем мощность P на блок 3x3x3 ячеек у грани x=0
        vol_src = 27 * (self.delta ** 3)
        self.S[0, iy-1:iy+2, iz-1:iz+2] = self.P / vol_src

        # Состояние для RK4: [T, время]
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
        # Dirichlet на дне (z=0): T=0 фиксировано
        d2z[:, :, 0] = (T[:, :, 1] - 2*T[:, :, 0]) / h2
        d2z[:, :, -1] = 2.0 * (T[:, :, -2] - T[:, :, -1]) / h2

        return d2x + d2y + d2z

    def dT_dt(self, T: np.ndarray, t: float) -> np.ndarray:
        lap = self.laplacian_vectorized(T)
        return self.a * lap + self.S - self.h * (T - self.T_air)

    def dt_dt(self, T: np.ndarray, t: float) -> float:
        return 1.0

    def next_step_integration(self) -> None:
        self.arr_T, t_new = RK4(self.state, self.funcs_rk4, self.dt)
        self.arr_T[:, :, 0] = 0.0  # Жёстко фиксируем лёд внизу
        self.step += 1
        self.state = [self.arr_T.copy(), t_new]