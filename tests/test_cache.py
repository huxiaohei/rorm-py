# -*- coding= utf-8 -*-

__time__ = '2024/07/30'
__author__ = '虎小黑'

import unittest
from pydantic import Field
from typing import Awaitable
from redis.asyncio import Redis
from orm.orm_model import ORMModel
from orm.orm_cache import ORMCache


@ORMCache.register
class RoleInfo(ORMModel):
    role_id: int = Field(0, title='角色id')
    role_name: str = Field('', title='角色名')
    role_level: int = Field(0, title='角色等级')

    def __init__(self,  /, **data) -> None:
        super().__init__(**data)


@ORMCache.register
class ItemInfo(ORMModel):
    item_id: int = Field(0, title='物品id')
    item_name: str = Field('', title='物品名')
    item_count: int = Field(0, title='物品数量')

    def __init__(self,  /, **data) -> None:
        super().__init__(**data)

    def unique_id(self) -> str:
        return f"{self.item_id}"


@ORMCache.register
class MailInfo(ORMModel):
    mail_id: int = Field(0, title='邮件id')
    mail_title: str = Field('', title='邮件标题')
    mail_content: str = Field('', title='邮件内容')

    def __init__(self,  /, **data) -> None:
        super().__init__(**data)

    def unique_id(self) -> str:
        return f'{self.mail_id}'


class Player(ORMCache):

    role: RoleInfo = RoleInfo()
    items: dict[str, ItemInfo] = {}
    mails: list[MailInfo] = []

    def __init__(self, client: Redis, user_id: int) -> None:
        super().__init__(client)
        self.__user_id = user_id

    def unique_id(self) -> str:
        return f"{self.__class__.__name__}:{self.__user_id}"


class TestCache(unittest.IsolatedAsyncioTestCase):

    async def test_save_data(self):
        client = await Redis.from_url('redis://localhost:6379/0')
        player = Player(client, 10001)

        rep = client.delete(player.unique_id())
        if isinstance(rep, Awaitable):
            rep = await rep

        player.role.role_id = 10001
        player.role.role_name = '虎小黑'
        player.role.role_level = 1

        for item_id in range(1, 6):
            item = ItemInfo(
                item_id=item_id,
                item_name=f'物品{item_id}',
                item_count=1)
            player.items[f'{item_id}'] = item

        for mail_id in range(1, 6):
            mail = MailInfo(
                mail_id=mail_id,
                mail_title=f'邮件{mail_id}',
                mail_content=f'邮件{mail_id}内容')
            player.mails.append(mail)

        await player.save()

        exists = client.exists(player.unique_id())
        if isinstance(exists, Awaitable):
            exists = await exists
        assert exists == 1

        await client.close()

    async def test_load_data(self):
        client = await Redis.from_url('redis://localhost:6379/0')
        player = Player(client, 10001)
        await player.load()
        assert player.role.role_id == 10001
        assert player.role.role_name == '虎小黑'
        assert len(player.items) == 5
        assert len(player.mails) == 5
        await client.close()
        print(player.model_dump_json())

    async def test_update_data(self):
        client = await Redis.from_url('redis://localhost:6379/0')
        player = Player(client, 10001)
        await player.load()
        player.role.role_level = 2
        await player.save()
        player.role.role_level = 3
        await player.save()
        await client.close()
