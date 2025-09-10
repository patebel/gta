from copy import deepcopy


def split_list(a, n):
    k, m = divmod(len(a), n)
    return [deepcopy(a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)]) for i in range(n)]
