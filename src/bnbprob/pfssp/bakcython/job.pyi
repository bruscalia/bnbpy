import numpy as np

class Job:
    j: int
    p: np.ndarray[int, int]
    r: np.ndarray[int, int]
    q: np.ndarray[int, int]
    lat: np.ndarray[tuple[int, int], int]
    slope: int
    T: int
