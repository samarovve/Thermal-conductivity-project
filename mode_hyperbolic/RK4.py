from typing import List, Callable, Any


def RK4(vars: List[Any], funcs: List[Callable[..., Any]], h: float) -> List[Any]:

    """
    One step of the 4th-order Runge-Kutta method.


    Args:
        vars (List[float]): current values of variables
        funcs (List[Callable[..., float]]): list of system functions
        h (float): the integration step

    Returns:
        new variable values
    """

    if len(vars) != len(funcs):
        raise ValueError("The number of variables must be equal to the number of functions!")

    k1 = [f(*vars) for f in funcs]

    temp = [vars[i] + 0.5 * h * k1[i] for i in range(len(vars))]
    k2 = [f(*temp) for f in funcs]

    temp = [vars[i] + 0.5 * h * k2[i] for i in range(len(vars))]
    k3 = [f(*temp) for f in funcs]

    temp = [vars[i] + h * k3[i] for i in range(len(vars))]
    k4 = [f(*temp) for f in funcs]

    return [
        vars[i] + h * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / 6
        for i in range(len(vars))
    ]