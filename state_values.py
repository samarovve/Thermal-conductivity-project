from multiprocessing import Value
import ctypes

should_continue=Value(ctypes.c_bool, True)

mode=Value(ctypes.c_int, 0)