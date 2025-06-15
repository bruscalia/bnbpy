from typing import Any

import numpy as np

class PyJob:
    j: int
    p: np.ndarray[tuple[int], Any]
    r: np.ndarray[tuple[int], Any]
    q: np.ndarray[tuple[int], Any]
    lat: np.ndarray[tuple[int, int], Any]
    slope: int
    T: int
