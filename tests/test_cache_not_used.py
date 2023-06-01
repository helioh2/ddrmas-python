"""Tests the caching module.
Source: https://gist.github.com/dlebech/c16a34f735c0c4e9b604"""

import asyncio
import unittest

from . import cache_not_used

called = 0
called2 = 0


@cache_not_used.memoize
def wrapped():
    global called
    called += 1
    return 10


@cache_not_used.memoize(except_args=["y"])
def wrapped2(x,y):
    global called2
    called2 += 1
    return 10

class MemoizeClass(object):
    cls_called = 0
    cls_async_called = 0

    @classmethod
    @cache_not_used.memoize
    def my_class_fun(cls):
        cls.cls_called += 1
        return 20

    @classmethod
    @cache_not_used.memoize
    async def my_async_classmethod(cls):
        cls.cls_async_called += 1
        return 40

    def __init__(self):
        self.called = 0

    @cache_not_used.memoize
    def my_fun(self):
        self.called += 1
        return 30

    @cache_not_used.memoize
    async def my_async_fun(self):
        self.called += 1
        return 50


class TestMemoize(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_memoize_fun(self):
        """It should work for a module level method"""
        self.assertEqual(called, 0)

        val = wrapped()
        self.assertEqual(val, 10)
        self.assertEqual(called, 1)

        val = wrapped()
        self.assertEqual(val, 10)
        self.assertEqual(called, 1)

    def test_memoize_fun_with_except_args(self):
        """It should work for a module level method"""
        self.assertEqual(called2, 0)

        val = wrapped2(x=5, y=2)
        self.assertEqual(val, 10)
        self.assertEqual(called2, 1)
        print(called2)

        val = wrapped2(5, 1)
        self.assertEqual(val, 10)
        self.assertEqual(called2, 1)
        print(called2)

        val = wrapped2(4, 2)
        self.assertEqual(val, 10)
        self.assertEqual(called2, 2)
        print(called2)

    def test_memoize_class_method(self):
        """It should work for a classmethod"""
        self.assertEqual(MemoizeClass.cls_called, 0)

        val = MemoizeClass.my_class_fun()
        self.assertEqual(val, 20)
        self.assertEqual(MemoizeClass.cls_called, 1)

        val = MemoizeClass.my_class_fun()
        self.assertEqual(val, 20)
        self.assertEqual(MemoizeClass.cls_called, 1)

    def test_memoize_instance_method(self):
        """It should work for an instance method"""
        mc = MemoizeClass()
        self.assertEqual(mc.called, 0)

        val = mc.my_fun()
        self.assertEqual(val, 30)
        self.assertEqual(mc.called, 1)

        val = mc.my_fun()
        self.assertEqual(val, 30)
        self.assertEqual(mc.called, 1)

    def test_memoize_async_classmethod(self):
        """It should work with an async coroutine as classmethod."""
        self.assertEqual(MemoizeClass.cls_async_called, 0)

        async def go():
          val_fut1 = await MemoizeClass.my_async_classmethod()
          val_fut2 = await MemoizeClass.my_async_classmethod()
          self.assertEqual(val_fut1, 40)
          self.assertEqual(val_fut2, 40)

        self.loop.run_until_complete(go())
        self.assertEqual(MemoizeClass.cls_async_called, 1)

    def test_memoize_async(self):
        """It should work with an async coroutine instance method."""
        mc = MemoizeClass()
        self.assertEqual(mc.called, 0)

        async def go():
          val_fut1 = await mc.my_async_fun()
          val_fut2 = await mc.my_async_fun()
          self.assertEqual(val_fut1, 50)
          self.assertEqual(val_fut2, 50)

        self.loop.run_until_complete(go())
        self.assertEqual(mc.called, 1)


if __name__ == '__main__':
    unittest.main()