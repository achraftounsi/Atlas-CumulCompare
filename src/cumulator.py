import os

import numpy as np
from tqdm import tqdm


def most_frequent(_List):
    return max(set(_List), key=list(_List).count)


def likelihood(_array):
    _array[np.isnan(_array)] = 0
    return np.array([[most_frequent(_array[:, row, column]).sum() for column in range(_array.shape[2])] for row in
                     range(_array.shape[1])])


def make_cumulations(nowcast_linda):
    res = np.zeros((nowcast_linda[list(nowcast_linda)[0]].shape[1], nowcast_linda[list(nowcast_linda)[0]].shape[2]))
    for e in tqdm(list(nowcast_linda), desc='Cumulating ...'):
        res = np.add(res, likelihood(nowcast_linda[e]))
    return res


def generate_cumulations(nowcast_linda, save_path):
    if not os.path.exists(os.path.join(save_path, 'graphs')):
        os.makedirs(os.path.join(save_path, 'graphs'))
    return make_cumulations(nowcast_linda)
