import itertools
import re


def reshape_list(l, size_of_chunk):
    return list(itertools.izip_longest(*([iter(l)] * size_of_chunk)))

def flatten_list(l):
    return list(itertools.chain.from_iterable(l))


def camel_case_to_lower_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
