# RORM

基于`Redis`的结构化存储驱动

## Example

### 定义模型

模型将会被序列化为`json`格式存储在`Redis`中。如果`ORMCache`使用`list`或`dict`来存储`ORMModel`，那么`ORMModel`必须实现`unique_id`方法，用于唯一标识`ORMModel`

```python

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

```

### 使用模型

定义一个类继承`ORMCache`，并在类中持有模型的实例，`ORMCache`的子类必须实现`unique_id`方法，用于唯一实例。

```python

class Player(ORMCache):

    role: RoleInfo = RoleInfo()
    items: dict[str, ItemInfo] = {}
    mails: list[MailInfo] = []

    def __init__(self, client: Redis, user_id: int) -> None:
        super().__init__(client)
        self.__user_id = user_id

    def unique_id(self) -> str:
        return f"{self.__class__.__name__}:{self.__user_id}"
```

### 存储数据

```python

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

```

```log
127.0.0.1:6379> KEYS *
1) "Player:10001"
127.0.0.1:6379> HGETALL Player:10001
 1) "items:ItemInfo:4"
 2) "{\"item_id\":4,\"item_name\":\"\xe7\x89\xa9\xe5\x93\x814\",\"item_count\":1}"
 3) "items:ItemInfo:1"
 4) "{\"item_id\":1,\"item_name\":\"\xe7\x89\xa9\xe5\x93\x811\",\"item_count\":1}"
 5) "items:ItemInfo:2"
 6) "{\"item_id\":2,\"item_name\":\"\xe7\x89\xa9\xe5\x93\x812\",\"item_count\":1}"
 7) "role:RoleInfo"
 8) "{\"role_id\":10001,\"role_name\":\"\xe8\x99\x8e\xe5\xb0\x8f\xe9\xbb\x91\",\"role_level\":1}"
 9) "items:ItemInfo:3"
10) "{\"item_id\":3,\"item_name\":\"\xe7\x89\xa9\xe5\x93\x813\",\"item_count\":1}"
11) "mails:MailInfo:2"
12) "{\"mail_id\":2,\"mail_title\":\"\xe9\x82\xae\xe4\xbb\xb62\",\"mail_content\":\"\xe9\x82\xae\xe4\xbb\xb62\xe5\x86\x85\xe5\xae\xb9\"}"
13) "items:ItemInfo:5"
14) "{\"item_id\":5,\"item_name\":\"\xe7\x89\xa9\xe5\x93\x815\",\"item_count\":1}"
15) "mails:MailInfo:4"
16) "{\"mail_id\":4,\"mail_title\":\"\xe9\x82\xae\xe4\xbb\xb64\",\"mail_content\":\"\xe9\x82\xae\xe4\xbb\xb64\xe5\x86\x85\xe5\xae\xb9\"}"
17) "mails:MailInfo:5"
18) "{\"mail_id\":5,\"mail_title\":\"\xe9\x82\xae\xe4\xbb\xb65\",\"mail_content\":\"\xe9\x82\xae\xe4\xbb\xb65\xe5\x86\x85\xe5\xae\xb9\"}"
19) "mails:MailInfo:1"
20) "{\"mail_id\":1,\"mail_title\":\"\xe9\x82\xae\xe4\xbb\xb61\",\"mail_content\":\"\xe9\x82\xae\xe4\xbb\xb61\xe5\x86\x85\xe5\xae\xb9\"}"
21) "mails:MailInfo:3"
22) "{\"mail_id\":3,\"mail_title\":\"\xe9\x82\xae\xe4\xbb\xb63\",\"mail_content\":\"\xe9\x82\xae\xe4\xbb\xb63\xe5\x86\x85\xe5\xae\xb9\"}"
```

### 加载数据

通过`load`方法加载数据后，`ORMModel`都被标记为脏

```python
class TestCache(unittest.IsolatedAsyncioTestCase):

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
```

```log
Received JSON data in run
test_load_data (test_cache.TestCache.test_load_data) ... 
{"role":{"role_id":10001,"role_name":"虎小黑","role_level":1},"items":{"4":{"item_id":4,"item_name":"物品4","item_count":1},"1":{"item_id":1,"item_name":"物品1","item_count":1},"2":{"item_id":2,"item_name":"物品2","item_count":1},"3":{"item_id":3,"item_name":"物品3","item_count":1},"5":{"item_id":5,"item_name":"物品5","item_count":1}},"mails":[{"mail_id":2,"mail_title":"邮件2","mail_content":"邮件2内容"},{"mail_id":4,"mail_title":"邮件4","mail_content":"邮件4内容"},{"mail_id":5,"mail_title":"邮件5","mail_content":"邮件5内容"},{"mail_id":1,"mail_title":"邮件1","mail_content":"邮件1内容"},{"mail_id":3,"mail_title":"邮件3","mail_content":"邮件3内容"}]}
ok
```

### 更新数据

调用`save`方法时，只有被标记为脏的`ORMModel`才会被保存

```python
class TestCache(unittest.IsolatedAsyncioTestCase):

    async def test_update_data(self):
        client = await Redis.from_url('redis://localhost:6379/0')
        player = Player(client, 10001)
        await player.load()
        player.role.role_level = 2
        await player.save()
        player.role.role_level = 3
        await player.save()
        await client.close()
```

```log
RoleInfo Update role_level from 3 to 2
Player:10001 update {'role:RoleInfo': '{"role_id":10001,"role_name":"虎小黑","role_level":2}', 'items:ItemInfo:3': '{"item_id":3,"item_name":"物品3","item_count":1}', 'items:ItemInfo:5': '{"item_id":5,"item_name":"物品5","item_count":1}', 'items:ItemInfo:4': '{"item_id":4,"item_name":"物品4","item_count":1}', 'items:ItemInfo:2': '{"item_id":2,"item_name":"物品2","item_count":1}', 'items:ItemInfo:1': '{"item_id":1,"item_name":"物品1","item_count":1}', 'mails:MailInfo:2': '{"mail_id":2,"mail_title":"邮件2","mail_content":"邮件2内容"}', 'mails:MailInfo:4': '{"mail_id":4,"mail_title":"邮件4","mail_content":"邮件4内容"}', 'mails:MailInfo:5': '{"mail_id":5,"mail_title":"邮件5","mail_content":"邮件5内容"}', 'mails:MailInfo:1': '{"mail_id":1,"mail_title":"邮件1","mail_content":"邮件1内容"}', 'mails:MailInfo:3': '{"mail_id":3,"mail_title":"邮件3","mail_content":"邮件3内容"}'}
RoleInfo Update role_level from 2 to 3
Player:10001 update {'role:RoleInfo': '{"role_id":10001,"role_name":"虎小黑","role_level":3}'}
```
