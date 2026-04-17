import numpy as np
from solver_hyp_eq_therm import SolverHypEqTherm
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


dt = 2e-4
crds = (0.2, 0.2, 0.5)
S = "1e5 * exp(-((x-x0)**2 + (y-y0)**2 + (z-z0)**2)/(2*0.02**2)) * exp(-(t-0.003)**2/(2*0.0008**2))"
Solver = SolverHypEqTherm(80, 300, 3e-3, 8e-4, crds, S, dt)


class DrawCubeSections():

    def __init__(self, Solver):
        self.Solver = Solver

        self.x0, self.y0, self.z0 = Solver.crds_S

        self.ix0 = np.argmin(np.abs(Solver.x_lin - self.x0))
        self.iy0 = np.argmin(np.abs(Solver.y_lin - self.y0))
        self.iz0 = np.argmin(np.abs(Solver.z_lin - self.z0))


    # Функция одного шага
    def compute_next_frame(self):
        self.Solver.next_step_integration()

        T_slice_z = self.Solver.arr_T[:, :, self.iz0]
        T_slice_y = self.Solver.arr_T[:, self.iy0, :]

        return T_slice_z, T_slice_y, self.Solver.state[2]


    # Настройка графиков
    def starting_position(self):
        Tz0, Ty0, _ = self.compute_next_frame()


        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Z-срез
        self.im1 = self.ax1.imshow(Tz0, cmap='hot', origin='lower', vmin=300, vmax=400)
        self.ax1.set_title('Срез Z')
        plt.colorbar(self.im1, ax=self.ax1)

        # Y-срез
        self.im2 = self.ax2.imshow(Ty0, cmap='hot', origin='lower', vmin=300, vmax=400)
        self.ax2.set_title('Срез Y')

        self.ax1.scatter(self.iy0, self.ix0, c='cyan', s=50, marker='x')
        self.ax2.scatter(self.iz0, self.ix0, c='cyan', s=50, marker='x')

        plt.colorbar(self.im2, ax=self.ax2)


    # Функция обновления кадра
    def update(self, *args, **kwargs):
        Tz, Ty, t = self.compute_next_frame()

        self.im1.set_array(Tz)
        self.im2.set_array(Ty)

        self.im1.set_clim(200, 600)
        self.im2.set_clim(200, 600)

        return self.im1, self.im2


    # Запуск анимации
    def start(self):

        self.starting_position()
        ani = FuncAnimation(self.fig, self.update, interval=50, blit=False, cache_frame_data=False)

        plt.tight_layout()
        plt.show()


Draw = DrawCubeSections(Solver)
Draw.start()