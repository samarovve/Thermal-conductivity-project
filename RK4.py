# Алгоритм численного интегрирования RK4 для произвольного количества переменных и функций
def RK4(vars, funcs, h):


    if len(vars) != len(funcs):
        raise ValueError("Количество переменных должно быть равно количеству функций!")

    # список для хранения промежуточный значений переменных
    temp_vars = []

    # K1
    lst_k1 = [funcs[i](*vars) for i in range(len(funcs))]

    # K2
    temp_vars = [vars[i] + 0.5 * h * lst_k1[i] for i in range(len(vars))]
    lst_k2 = [funcs[i](*temp_vars) for i in range(len(funcs))]

    # K3
    temp_vars = [vars[i] + 0.5 * h * lst_k2[i] for i in range(len(vars))]
    lst_k3 = [funcs[i](*temp_vars) for i in range(len(funcs))]

    # K4
    temp_vars = [vars[i] + h * lst_k3[i] for i in range(len(vars))]
    lst_k4 = [funcs[i](*temp_vars) for i in range(len(funcs))]

    # Новое значение переменных
    new_vars = [vars[i] + h * (lst_k1[i] + 2 * lst_k2[i] + lst_k3[i] * 2 + lst_k4[i]) / 6 for i in range(len(vars))]

    # Возвращаем новое значение переменных
    return new_vars
