from importlib.util import find_spec

# QR error correct levels
ERROR_CORRECT_L = 1
ERROR_CORRECT_M = 0
ERROR_CORRECT_Q = 3
ERROR_CORRECT_H = 2

# Constant whether the PIL library is installed.
PIL_AVAILABLE = find_spec("PIL") is not None
