# -*- coding= utf-8 -*-

__time__ = '2024/07/29'
__author__ = '虎小黑'


import unittest
from typing import Awaitable
from redis.asyncio import Redis


class TestRedis(unittest.IsolatedAsyncioTestCase):

    async def test_redis_connection(self):
        client = Redis.from_url('redis://localhost:6379/0')
        ping = await client.ping()
        await client.close()
        print(type(ping))

    async def test_redis_hset(self):
        client = Redis.from_url('redis://localhost:6379/0')
        result = client.hset('test', 'A', 'a')
        if isinstance(result, Awaitable):
            a = await result
        else:
            a = result
        print(a)
        await client.close()
        key = 'a:b:c:d'
        attr_name, orm_name = key.split(':')[:2]
        print(attr_name, orm_name)
