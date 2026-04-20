import numpy as np


def high_energy_computation(size):
    # Create a large random matrix
    matrix = np.random.rand(size, size)
    result = 0
    # Triple nested loop with redundant calculations
    for i in range(size):
        for j in range(size):
            for k in range(size):
                # Inefficient repeated computation
                result += np.sum(matrix[i, :] *
                                 matrix[:, j]) * np.sqrt(matrix[k, j])
    return result


if __name__ == "__main__":
    # This will consume a lot of CPU and energy
    print(high_energy_computation(300))
