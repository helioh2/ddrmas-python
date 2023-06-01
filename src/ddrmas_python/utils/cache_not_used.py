"""Global LRU caching utility. For that little bit of extra speed.
The caching utility provides a single wrapper function that can be used to
provide a bit of extra speed for some often used function. The cache is an LRU
cache including a key timeout.
Usage::
    import cache
    @cache.memoize
    def myfun(x, y):
        return x + y
Also support asyncio coroutines::
    @cache.memoize
    async def myfun(x, y):
        x_result = await fetch_x(x)
        return x_result + y
The cache can be manually cleared with `myfun.cache.clear()`

Based on: https://gist.github.com/dlebech/c16a34f735c0c4e9b604
"""

import asyncio
from functools import wraps
import inspect

from lru import LRUCacheDict

__all__ = ['memoize']



def _wrap_coroutine_storage(cache_dict, key, future):
    async def wrapper():
        val = await future
        cache_dict[key] = val
        return val
    return wrapper()


def _wrap_value_in_coroutine(val):
    async def wrapper():
        return val
    return wrapper()

def memoize(original_function=None, except_args=[]):

    def _decorate(f):
        """An in-memory cache wrapper that can be used on any function, including
        coroutines.
        """
        __cache = LRUCacheDict(max_size=256, expiration=60)

        @wraps(f)
        def wrapper(*args, **kwargs):
            # Simple key generation. Notice that there are no guarantees that the
            # key will be the same when using dict arguments.
            
            arg_names = inspect.signature(f).parameters.keys()

            args_to_cache = [arg for arg_name, arg in 
                    zip(arg_names, args+tuple(kwargs.values())) 
                    if arg_name not in except_args]
            
            key = f.__module__ + '#' + f.__name__ + '#' + repr(args_to_cache)
            try:
                val = __cache[key]
                if asyncio.iscoroutinefunction(f):
                    return _wrap_value_in_coroutine(val)
                print("USOU RESPOSTA CACHEADA!!")
                return val
            except KeyError:
                val = f(*args, **kwargs)

                if asyncio.iscoroutine(val):
                    # If the value returned by the function is a coroutine, wrap
                    # the future in a new coroutine that stores the actual result
                    # in the cache.
                    return _wrap_coroutine_storage(__cache, key, val)

                # Otherwise just store and return the value directly
                __cache[key] = val
                return val

        return wrapper
    
    if original_function:
        return _decorate(original_function)
    
    return _decorate
    
