import numpy as np
from .RK4 import RK4
import sympy as sp


class SolverHypEqTherm:
    """Numerical solver for the 3D hyperbolic heat conduction equation.

    Solves:
        τ·∂²T/∂t² + ∂T/∂t = α·∇²T + S(x,y,z,t)

    on a unit cube with adiabatic boundary conditions (∂T/∂n = 0).
    Initial conditions: T(x,y,z,0) = T0, ∂T/∂t(x,y,z,0) = 0.
    Supports arbitrary space- and time-dependent heat sources defined via a SymPy expression.

    Attributes:
        N (int): Number of grid nodes in each dimension.
        tau (float): Relaxation time (τ).
        a (float): Thermal diffusivity (α).
        dt (float): Time step for Runge–Kutta integration.
        delta (float): Grid spacing (1/(N-1)).
        arr_T (np.ndarray): Current temperature field (3D array of shape N×N×N).
        arr_dT (np.ndarray): Current time derivative of temperature (3D array).
        crds_S (tuple[float, float, float]): Source center coordinates (x0, y0, z0) in [0,1].
        S (callable): Heat source function S(t, x, y, z) returning a scalar.
    """


    def __init__(self, N: int, T0: float, tau: float, a: float,
                 crds_S: tuple[float, float, float], S: str, dt: float):
        """Initialize the solver.

        Args:
            N (int): Number of grid nodes in each dimension.
            T0 (float): Initial temperature everywhere in the domain.
            tau (float): Relaxation time (τ > 0).
            a (float): Thermal diffusivity (α > 0).
            crds_S (tuple[float, float, float]): Source center coordinates (x0, y0, z0) in [0,1].
            S (str): SymPy expression as a string, e.g. "exp(-((x-x0)**2+(y-y0)**2+(z-z0)**2)/0.1)*sp.sin(t)".
                Available symbols: x, y, z, t, x0, y0, z0, exp.
            dt (float): Time step for Runge–Kutta integration (>0).
        """

        self.tau = tau
        self.a = a
        self.crds_S = crds_S

        self.N = N
        self.delta = 1.0 / (N - 1)      # grid spacing

        # temperature and its time derivative fields
        self.arr_T = np.full((N, N, N), T0, dtype=np.float64)
        self.arr_dT = np.zeros((N, N, N), dtype=np.float64)

        # coordinate grids
        self.x_lin = np.linspace(0, 1, N)
        self.y_lin = np.linspace(0, 1, N)
        self.z_lin = np.linspace(0, 1, N)
        self.X, self.Y, self.Z = np.meshgrid(self.x_lin, self.y_lin, self.z_lin, indexing='ij')

        # RK4 internals
        self.funcs_rk4 = [self.dT_dt, self.dV_dt, self.dt_dt]
        self.dt = dt
        self.step = 0
        self.state = [self.arr_T, self.arr_dT, self.step * self.dt]

        # Parse heat source expression
        x, y, z, t = sp.symbols('x y z t')
        local_dict = {
            'x': x, 'y': y, 'z': z, 't': t,
            'x0': crds_S[0], 'y0': crds_S[1], 'z0': crds_S[2],
            'exp': sp.exp
        }
        expr = sp.parse_expr(S, local_dict=local_dict)
        self.S = sp.lambdify((t, x, y, z), expr, modules='numpy')


    def laplacian_neumann_vectorized(self, T: np.ndarray) -> np.ndarray:
        """Compute the Laplacian ∇²T with second-order accuracy and adiabatic boundaries.

        Args:
            T (np.ndarray): 3D temperature field (shape N×N×N).

        Returns:
            ∇²T (np.ndarray): Laplacian of T as a 3D numpy array of the same shape.
        """

        h2 = self.delta ** 2

        # x-direction
        d2x = np.zeros_like(T)
        d2x[1:-1, :, :] = (T[2:, :, :] - 2*T[1:-1, :, :] + T[:-2, :, :]) / h2
        d2x[0, :, :] = 2.0 * (T[1, :, :] - T[0, :, :]) / h2
        d2x[-1, :, :] = 2.0 * (T[-2, :, :] - T[-1, :, :]) / h2

        # y-direction
        d2y = np.zeros_like(T)
        d2y[:, 1:-1, :] = (T[:, 2:, :] - 2*T[:, 1:-1, :] + T[:, :-2, :]) / h2
        d2y[:, 0, :] = 2.0 * (T[:, 1, :] - T[:, 0, :]) / h2
        d2y[:, -1, :] = 2.0 * (T[:, -2, :] - T[:, -1, :]) / h2

        # z-direction
        d2z = np.zeros_like(T)
        d2z[:, :, 1:-1] = (T[:, :, 2:] - 2*T[:, :, 1:-1] + T[:, :, :-2]) / h2
        d2z[:, :, 0] = 2.0 * (T[:, :, 1] - T[:, :, 0]) / h2
        d2z[:, :, -1] = 2.0 * (T[:, :, -2] - T[:, :, -1]) / h2

        return d2x + d2y + d2z


    def dT_dt(self, T: np.ndarray, V: np.ndarray, t: float) -> np.ndarray:
        """Compute the partial derivative of T with respect to t.

        Returns:
            dT/dt = V (np.ndarray).
        """
        return V


    def dV_dt(self, T: np.ndarray, V: np.ndarray, t: float) -> np.ndarray:
        """Compute the partial derivative of V with respect to t.

        Computes:
            dV/dt = (α·∇²T + S - V) / τ

        Returns:
            Time derivative of V.
        """
        lap = self.laplacian_neumann_vectorized(T)
        S_val = self.S(t, self.X, self.Y, self.Z)
        return (self.a * lap + S_val - V) / self.tau


    def dt_dt(self, T: np.ndarray, V: np.ndarray, t: float) -> float:
        """Function needed only for RK4.

        Returns:
            1.0 (float).
        """
        return 1.0


    def next_step_integration(self) -> None:
        """Advance the solution by one time step using the RK4 integrator.

        Updates:
            arr_T, arr_dT and the internal time counter.
        """
        self.arr_T, self.arr_dT, t_new = RK4(self.state, self.funcs_rk4, self.dt)
        self.step += 1
        self.state = [self.arr_T, self.arr_dT, t_new]