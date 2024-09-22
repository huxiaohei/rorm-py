# RORM

基于`Redis`的结构化存储驱动，使用者只需要定义数据模型，即可实现数据的持久化和缓存

在`rorm`中，`ORMModel`作为数据模型使用，`ORMCache`将持有`ORMModel`的实例，并提供数据的持久化和缓存功能

## 注意事项与基本原理

* `ORMModel`的子类需要实现`unique_id`方法，以便`ORMCache`能够正确的管理数据
* 每个`ORMCache`实例都会对应`redis`中的一个`hash`结构，`hash`名为`ORMCache`的`unique_id`
  * `key`由`ORMCache`的属性名与对应`ORMModel`的类型名以及`ORMModel`的`unique_id`
  * `value`为`ORMModel`的`json`序列化结果
* 在调用`ORMCache`对象的`save_all`方法时，会将`ORMCache`实例中的所有`ORMModel`的实例保存到`redis`中
  * `ORMModel`实现的标脏检查，只有数据发生变化时才会序列化并保存，因此不用担心序列化性能和访问`redis`过于频繁的问题

## Example

### 定义ORMModel和ORMCache

```python
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

```

### 存储数据

```python
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
```

**注意** 只有`ORMModel`类型的数据才会被存储

```log
127.0.0.1:6379> KEYS *
1) "Player:10001"
127.0.0.1:6379> HGETALL Player:10001
 1) "mails:MailInfo:1"
 2) "{\"mail_id\":1,\"mail_title\":\"mail-1\",\"mail_content\":\"mail-1\",\"attarchments\":[{\"item_id\":1,\"item_name\":\"item-1\",\"item_count\":1}]}"
 3) "items:ItemInfo:1"
 4) "{\"item_id\":1,\"item_name\":\"item-1\",\"item_count\":1}"
 5) "items:ItemInfo:3"
 6) "{\"item_id\":3,\"item_name\":\"item-3\",\"item_count\":3}"
 7) "mails:MailInfo:2"
 8) "{\"mail_id\":2,\"mail_title\":\"mail-2\",\"mail_content\":\"mail-2\",\"attarchments\":[{\"item_id\":2,\"item_name\":\"item-2\",\"item_count\":2}]}"
 9) "items:ItemInfo:4"
10) "{\"item_id\":4,\"item_name\":\"item-4\",\"item_count\":4}"
11) "role:RoleInfo:10001"
12) "{\"role_id\":10001,\"role_name\":\"rorm-py\",\"role_level\":1}"
13) "mails:MailInfo:3"
14) "{\"mail_id\":3,\"mail_title\":\"mail-3\",\"mail_content\":\"mail-3\",\"attarchments\":[{\"item_id\":3,\"item_name\":\"item-3\",\"item_count\":3}]}"
15) "mails:MailInfo:4"
16) "{\"mail_id\":4,\"mail_title\":\"mail-4\",\"mail_content\":\"mail-4\",\"attarchments\":[{\"item_id\":4,\"item_name\":\"item-4\",\"item_count\":4}]}"
17) "items:ItemInfo:2"
18) "{\"item_id\":2,\"item_name\":\"item-2\",\"item_count\":2}"
19) "items:ItemInfo:5"
20) "{\"item_id\":5,\"item_name\":\"item-5\",\"item_count\":5}"
21) "mails:MailInfo:5"
22) "{\"mail_id\":5,\"mail_title\":\"mail-5\",\"mail_content\":\"mail-5\",\"attarchments\":[{\"item_id\":5,\"item_name\":\"item-5\",\"item_count\":5}]}"
```

### 读取数据

```python
async def test_load(self):
    client = await Redis.from_url("redis://localhost:6379/0")
    player = Player(client, 10001)
    await player.load_from_redis()
    print(player.model_dump_json())
    await client.close()
```

```json
{
    "role":{"role_id":10001,"role_name":"rorm-py","role_level":1},
    "items":{
        "1":{"item_id":1,"item_name":"item-1","item_count":1},
        "3":{"item_id":3,"item_name":"item-3","item_count":3},
        "4":{"item_id":4,"item_name":"item-4","item_count":4},
        "2":{"item_id":2,"item_name":"item-2","item_count":2},
        "5":{"item_id":5,"item_name":"item-5","item_count":5}
    },
    "mails":[
        {"mail_id":1,"mail_title":"mail-1","mail_content":"mail-1","attarchments":[{"item_id":1,"item_name":"item-1","item_count":1}]},
        {"mail_id":2,"mail_title":"mail-2","mail_content":"mail-2","attarchments":[{"item_id":2,"item_name":"item-2","item_count":2}]},
        {"mail_id":3,"mail_title":"mail-3","mail_content":"mail-3","attarchments":[{"item_id":3,"item_name":"item-3","item_count":3}]},
        {"mail_id":4,"mail_title":"mail-4","mail_content":"mail-4","attarchments":[{"item_id":4,"item_name":"item-4","item_count":4}]},
        {"mail_id":5,"mail_title":"mail-5","mail_content":"mail-5","attarchments":[{"item_id":5,"item_name":"item-5","item_count":5}]}],
    "tmp":[]
}
```

### 修改与删除数据

```python
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
```

```log
127.0.0.1:6379> HGETALL Player:10001
 1) "role:RoleInfo:10001"
 2) "{\"role_id\":10001,\"role_name\":\"rorm-py\",\"role_level\":2}"
 3) "mails:MailInfo:3"
 4) "{\"mail_id\":3,\"mail_title\":\"mail-3\",\"mail_content\":\"modify\",\"attarchments\":[{\"item_id\":3,\"item_name\":\"item-3\",\"item_count\":4}]}"
 5) "role:RoleInfo:0"
 6) "{\"role_id\":0,\"role_name\":\"\",\"role_level\":0}"
 7) "mails:MailInfo:1"
 8) "{\"mail_id\":1,\"mail_title\":\"mail-1\",\"mail_content\":\"modify\",\"attarchments\":[{\"item_id\":1,\"item_name\":\"item-1\",\"item_count\":2}]}"
 9) "items:ItemInfo:5"
10) "{\"item_id\":5,\"item_name\":\"item-5\",\"item_count\":6}"
11) "items:ItemInfo:3"
12) "{\"item_id\":3,\"item_name\":\"item-3\",\"item_count\":4}"
13) "items:ItemInfo:1"
14) "{\"item_id\":1,\"item_name\":\"item-1\",\"item_count\":2}"
15) "mails:MailInfo:5"
16) "{\"mail_id\":5,\"mail_title\":\"mail-5\",\"mail_content\":\"modify\",\"attarchments\":[{\"item_id\":5,\"item_name\":\"item-5\",\"item_count\":6}]}"
```
