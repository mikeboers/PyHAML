
# For compatibility with 2.5
# Lifted from http://stackoverflow.com/questions/1716428/def-next-for-python-pre-2-6-instead-of-object-next-method/1716464#1716464

class Throw(object): pass
throw = Throw() # easy sentinel hack

def next(iterator, default=throw):
    """next(iterator[, default])

    Return the next item from the iterator. If default is given
    and the iterator is exhausted, it is returned instead of
    raising StopIteration.
    """
    try:
        iternext = iterator.next.__call__
        # this way an AttributeError while executing next() isn't hidden
        # (2.6 does this too)
    except AttributeError:
        raise TypeError("%s object is not an iterator" % type(iterator).__name__)
    try:
        return iternext()
    except StopIteration:
        if default is throw:
            raise
        return default
