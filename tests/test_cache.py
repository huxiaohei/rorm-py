# -*- coding= utf-8 -*-

__time__ = "2024/07/30"
__author__ = "虎小黑"

import unittest
from pydantic import Field
from redis.asyncio import Redis
from orm.orm_model import ORMModel
from orm.orm_cache import ORMCache


@ORMCache.register
class RoleInfo(ORMModel):
    role_id: int = Field(0, title="角色id")
    role_name: str = Field("", title="角色名")
    role_level: int = Field(0, title="角色等级")

    def __init__(self,  /, **data) -> None:
        super().__init__(**data)

    def unique_id(self) -> str:
        return f"{self.role_id}"


@ORMCache.register
class ItemInfo(ORMModel):
    item_id: int = Field(0, title="物品id")
    item_name: str = Field("", title="物品名")
    item_count: int = Field(0, title="物品数量")

    def __init__(self,  /, **data) -> None:
        super().__init__(**data)

    def unique_id(self) -> str:
        return f"{self.item_id}"


@ORMCache.register
class MailInfo(ORMModel):
    mail_id: int = Field(0, title="邮件id")
    mail_title: str = Field("", title="邮件标题")
    mail_content: str = Field("", title="邮件内容")
    attarchments: list[ItemInfo] = []

    def __init__(self,  /, **data) -> None:
        super().__init__(**data)

    def unique_id(self) -> str:
        return f"{self.mail_id}"


class Player(ORMCache):

    role: RoleInfo = RoleInfo()
    items: dict[str, ItemInfo] = {}
    mails: list[MailInfo] = []
    tmp: list[str] = []

    def __init__(self, client: Redis, user_id: int) -> None:
        super().__init__(client)
        self.__user_id = user_id

    def unique_id(self) -> str:
        return f"{self.__class__.__qualname__}:{self.__user_id}"


class TestCache(unittest.IsolatedAsyncioTestCase):

    async def test_save(self):
        client = await Redis.from_url("redis://localhost:6379/0")
        player = Player(client, 10001)
        player.role = RoleInfo(
            role_id=10001, role_name="rorm-py", role_level=1)
        for i in range(1, 6):
            player.items[f"{i}"] = ItemInfo(
                item_id=i, item_name=f"item-{i}", item_count=i)
        for i in range(1, 6):
            player.mails.append(MailInfo(
                mail_id=i,
                mail_title=f"mail-{i}",
                mail_content=f"mail-{i}",
                attarchments=[ItemInfo(
                    item_id=i,
                    item_name=f"item-{i}",
                    item_count=i)]
            ))
        player.tmp.append("not save")
        await player.save_all()
        await client.close()

    async def test_load(self):
        client = await Redis.from_url("redis://localhost:6379/0")
        player = Player(client, 10001)
        await player.load_from_redis()
        print(player.model_dump_json())
        await client.close()

    async def test_modify(self):
        client = await Redis.from_url("redis://localhost:6379/0")
        player = Player(client, 10001)
        await player.load_from_redis()

        player.role.role_level = 2
        for item in player.items.values():
            item.item_count += 1

        for mail in player.mails:
            mail.mail_content = "modify"
            for item in mail.attarchments:
                item.item_count += 1

        await player.save_all()

    async def test_delete(self):
        client = await Redis.from_url("redis://localhost:6379/0")
        player = Player(client, 10001)
        await player.load_from_redis()

        player.role = RoleInfo()
        for key in list(player.items.keys()):
            if int(key) % 2 == 0:
                del player.items[key]

        for mail in list(player.mails):
            if mail.mail_id % 2 == 0:
                player.mails.remove(mail)

        await player.save_all()
