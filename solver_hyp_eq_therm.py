import numpy as np
from RK4 import RK4
import sympy as sp



class SolverHypEqTherm:

    # инициализация всякой хрени
    def __init__(self, N, T0, tau, a, crds_S, S, dt):

        self.tau = tau          # время релаксации
        self.a = a              # температурапроводность
        self.crds_S = crds_S    # координаты мгновенного импульса тепла

        self.N = N                      # количество разбиений
        self.delta = 1.0 / (N - 1)      # шаг разбиений

        self.arr_T = np.full((N, N, N), T0, dtype=np.float64)       # массив температур узлов дискретной сетки
        self.arr_dT = np.zeros((N, N, N), dtype=np.float64)         # массив производных узлов дискретной сетки
        self.delta = 1.0 / (N - 1)                                        # шаг дискретной сетки

        self.x_lin = np.linspace(0, 1, N)
        self.y_lin = np.linspace(0, 1, N)
        self.z_lin = np.linspace(0, 1, N)
        self.X, self.Y, self.Z = np.meshgrid(self.x_lin, self.y_lin, self.z_lin, indexing='ij')

        self.funcs_rk4 = [self.dT_dt, self.dV_dt, self.dt_dt]
        self.dt = dt
        self.step = 0
        self.state = [self.arr_T, self.arr_dT, self.step * self.dt]


        # Парсинг строки sumpy
        x, y, z, t = sp.symbols('x y z t')

        local_dict = {
            'x': x, 'y': y, 'z': z, 't': t,
            'x0': crds_S[0],
            'y0': crds_S[1],
            'z0': crds_S[2],
            'exp': sp.exp
        }

        expr = sp.parse_expr(S, local_dict=local_dict)

        # уравнение вспышки тепла
        self.S = sp.lambdify((t, x, y, z), expr, modules='numpy')





    # Вычисление Лапласиан ∇2T, учитывая дискретность сетки и условия равенства 0 вторых частных производных
    def laplacian_neumann_vectorized(self, T):
        h2 = self.delta ** 2

        d2x = np.zeros_like(T)
        d2x[1:-1, :, :] = (T[2:, :, :] - 2 * T[1:-1, :, :] + T[:-2, :, :]) / h2
        d2x[0, :, :] = 2.0 * (T[1, :, :] - T[0, :, :]) / h2
        d2x[-1, :, :] = 2.0 * (T[-2, :, :] - T[-1, :, :]) / h2

        d2y = np.zeros_like(T)
        d2y[:, 1:-1, :] = (T[:, 2:, :] - 2 * T[:, 1:-1, :] + T[:, :-2, :]) / h2
        d2y[:, 0, :] = 2.0 * (T[:, 1, :] - T[:, 0, :]) / h2
        d2y[:, -1, :] = 2.0 * (T[:, -2, :] - T[:, -1, :]) / h2

        d2z = np.zeros_like(T)
        d2z[:, :, 1:-1] = (T[:, :, 2:] - 2 * T[:, :, 1:-1] + T[:, :, :-2]) / h2
        d2z[:, :, 0] = 2.0 * (T[:, :, 1] - T[:, :, 0]) / h2
        d2z[:, :, -1] = 2.0 * (T[:, :, -2] - T[:, :, -1]) / h2

        return d2x + d2y + d2z

    # Производная T по t
    def dT_dt(self, T, V, t):
        return V

    # Производная V по t
    def dV_dt(self, T, V, t):
        lap = self.laplacian_neumann_vectorized(T)
        S = self.S(t, self.X, self.Y, self.Z)
        return (self.a * lap + S - V) / self.tau


    # Чисто для RK4
    def dt_dt(self, T, V, t):
        return 1.0


    # Обновление всех параметров после одного шага численного интегрирования RK4
    def next_step_integration(self):

        self.arr_T, self.arr_dT, t_new = RK4(self.state, self.funcs_rk4, self.dt)
        self.step += 1
        self.state = [self.arr_T, self.arr_dT, t_new]