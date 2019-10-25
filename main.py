import numpy as np

from crr import CRR

###################################################################################################

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    # parser.add_argument('polynomial')
    args = parser.parse_args()

    crr = CRR(*np.array([8, 7, 5], dtype="uint8"))
    x_vec = np.array([3, 2, 1], dtype="uint8")
    y_vec = np.array([5, 5, 0], dtype="uint8")
    print(crr.add(x_vec, y_vec))
    print(crr.mul(x_vec, y_vec))
