import pytest
import numpy as np
from solver_hyp_eq_therm import SolverHypEqTherm


# ─────────────────────────────────────────────────────────────────────────────
# 1. Тесты пространственной дискретизации (Лапласиан)
# ─────────────────────────────────────────────────────────────────────────────
class TestLaplacian:
    def test_constant_field_gives_zero(self):
        """Лапласиан константного поля должен быть строго 0."""
        solver = SolverHypEqTherm(N=20, T0=300.0, tau=1e-4, a=0.1,
                                  crds_S=(0.5, 0.5, 0.5), S="0", dt=1e-5)
        T_const = np.full((solver.N, solver.N, solver.N), 300.0)
        lap = solver.laplacian_neumann_vectorized(T_const)
        np.testing.assert_allclose(lap, 0.0, atol=1e-12,
                                   err_msg="Laplacian of constant field is not zero!")

    def test_neumann_bc_eigenfunction(self):
        """Проверка лапласиана на аналитическом решении cos(πx)cos(πy)cos(πz).
        Аналитически: ∇²T = -3π²T. Ошибка должна быть O(h²)."""
        N = 50
        solver = SolverHypEqTherm(N=N, T0=0, tau=1, a=1,
                                  crds_S=(0.5, 0.5, 0.5), S="0", dt=1e-3)
        X, Y, Z = solver.X, solver.Y, solver.Z
        T = np.cos(np.pi * X) * np.cos(np.pi * Y) * np.cos(np.pi * Z)

        lap_num = solver.laplacian_neumann_vectorized(T)
        lap_exact = -3 * (np.pi ** 2) * T

        err = np.max(np.abs(lap_num - lap_exact))
        # В 3D ошибки по осям складываются. Для cos(πx) константа ошибки ~π⁴/12 ≈ 8.1
        # При h≈0.0204: err ≈ 3 * 8.1 * h² ≈ 0.0101. Порог 1.5e-2 безопасен.
        assert err < 1.5e-2, f"Max Laplacian error {err:.4e} exceeds expected O(h²)"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Тесты физических законов и сохранения
# ─────────────────────────────────────────────────────────────────────────────
class TestPhysics:
    def test_zero_source_no_evolution(self):
        """При S=0 и нулевой начальной скорости ∂T/∂t поле должно оставаться постоянным."""
        solver = SolverHypEqTherm(N=10, T0=300.0, tau=1e-4, a=0.1,
                                  crds_S=(0.5, 0.5, 0.5), S="0", dt=1e-5)
        for _ in range(50):
            solver.next_step_integration()

        np.testing.assert_allclose(solver.arr_T, 300.0, atol=1e-10)
        np.testing.assert_allclose(solver.arr_dT, 0.0, atol=1e-10)

    def test_uniform_source_energy_balance(self):
        """Интегрирование уравнения по объему с S=const даёт ОДУ для среднего T."""
        N = 20
        tau = 1e-4
        S0 = 1e5
        T0 = 300.0
        solver = SolverHypEqTherm(N=N, T0=T0, tau=tau, a=0.01,
                                  crds_S=(0.5, 0.5, 0.5), S=str(S0), dt=1e-6)

        steps = 2000
        for _ in range(steps):
            solver.next_step_integration()

        t = steps * solver.dt
        T_avg_num = np.mean(solver.arr_T)
        T_avg_exact = T0 + S0 * (t - tau * (1 - np.exp(-t / tau)))

        np.testing.assert_allclose(T_avg_num, T_avg_exact, rtol=1e-3,
                                   err_msg="Volume average temperature violates energy balance")

    def test_symmetry_centered_source(self):
        """Сферически симметричный источник в центре куба должен давать симметричное поле."""
        N = 21
        src_expr = "1e5*exp(-((x-0.5)**2 + (y-0.5)**2 + (z-0.5)**2)/0.01)"
        solver = SolverHypEqTherm(N=N, T0=300, tau=1e-4, a=1e-3,
                                  crds_S=(0.5, 0.5, 0.5), S=src_expr, dt=1e-5)

        for _ in range(300):
            solver.next_step_integration()

        T = solver.arr_T
        np.testing.assert_allclose(T, T[::-1, :, :], atol=1e-10)
        np.testing.assert_allclose(T, T[:, ::-1, :], atol=1e-10)
        np.testing.assert_allclose(T, T[:, :, ::-1], atol=1e-10)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Тесты интегратора и состояния
# ─────────────────────────────────────────────────────────────────────────────
class TestIntegration:
    def test_time_advancement_and_state_update(self):
        """Проверка, что время корректно шагает, а массивы заменяются, а не модифицируются."""
        solver = SolverHypEqTherm(N=10, T0=300, tau=1e-4, a=0.1,
                                  crds_S=(0.5, 0.5, 0.5), S="0", dt=0.01)

        old_T = solver.arr_T.copy()
        old_V = solver.arr_dT.copy()

        solver.next_step_integration()

        assert np.isclose(solver.state[2], 0.01), "Time variable not updated correctly"
        assert solver.state[0] is not old_T
        assert solver.state[1] is not old_V

    def test_rk4_convergence_order(self):
        """Проверка 4-го порядка точности RK4 по шагу времени.
        Важно: чтобы увидеть O(dt⁴), нужно подавить пространственную погрешность (большой N)
        и остановиться до выхода на стационар, пока решение активно меняется."""
        N = 60  # Подавляем пространственную погрешность O(h²)
        tau, a, T0 = 1e-4, 0.05, 300.0
        S_str = "5e4 * exp(-((x-0.2)**2+(y-0.5)**2+(z-0.5)**2)/0.05)"
        t_final = 2e-5  # Время ~0.2*tau: система ещё динамична, временная погрешность доминирует

        # Референсное решение с очень мелким шагом
        dt_ref = 1e-7
        solver_ref = SolverHypEqTherm(N=N, T0=T0, tau=tau, a=a, crds_S=(0.2, 0.5, 0.5), S=S_str, dt=dt_ref)
        for _ in range(int(t_final / dt_ref)):
            solver_ref.next_step_integration()
        T_ref = solver_ref.arr_T.copy()

        errors = []
        # Шаги в асимптотической зоне сходимости RK4
        for dt in [4e-6, 2e-6, 1e-6]:
            solver = SolverHypEqTherm(N=N, T0=T0, tau=tau, a=a, crds_S=(0.2, 0.5, 0.5), S=S_str, dt=dt)
            for _ in range(int(t_final / dt)):
                solver.next_step_integration()
            errors.append(np.max(np.abs(solver.arr_T - T_ref)))

        ratio1 = errors[0] / errors[1]
        ratio2 = errors[1] / errors[2]

        # Для 4-го порядка ожидаем отношение ~16. Допускаем 10-25 из-за численного шума и PDE-особенностей.
        assert 10 < ratio1 < 25, f"Convergence ratio1 {ratio1:.2f} deviates from 4th order"
        assert 10 < ratio2 < 25, f"Convergence ratio2 {ratio2:.2f} deviates from 4th order"