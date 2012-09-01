import itertools

def reshape_list(l, size_of_chunk):
    return list(itertools.izip_longest(*([iter(l)] * size_of_chunk)))

def flatten_list(l):
    return list(itertools.chain.from_iterable(l))
