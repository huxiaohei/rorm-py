# -*- coding= utf-8 -*-

__time__ = '2024/07/29'
__author__ = '虎小黑'


from pydantic import BaseModel
from redis.asyncio import Redis
from orm.orm_model import ORMModel
from typing import Any, Awaitable, Type, TypeVar, Union

T = TypeVar('T', bound=ORMModel)

_ORMS: dict[str, Type[ORMModel]] = {}


class ORMCache(BaseModel):

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, client: Redis, /, **data: Any) -> None:
        super().__init__(**data)
        self.__client = client

    def unique_id(self) -> str:
        return self.__class__.__name__

    @classmethod
    def register(cls, _cls: Type[T]) -> Type[T]:
        if _cls.__name__ in _ORMS:
            raise ValueError(f'{_cls.__name__} has already been registered')
        _ORMS[_cls.__name__] = _cls
        return _cls

    async def save(self):
        mapping: dict[str, str] = {}
        for attr_name, attr in self.__dict__.items():
            if isinstance(attr, ORMModel):
                if not attr.is_dirty():
                    continue
                mapping[f"{attr_name}:{attr.__class__.__name__}"] =\
                    attr.model_dump_json()
                attr.clear_dirty()
            elif isinstance(attr, list):
                for item in attr:
                    if not isinstance(item, ORMModel):
                        break
                    if not item.is_dirty():
                        continue
                    mapping[f"{attr_name}:{item.__class__.__name__}:{item.unique_id()}"] =\
                        item.model_dump_json()
                    item.clear_dirty()
            elif isinstance(attr, dict):
                for _, item in attr.items():
                    if not isinstance(item, ORMModel):
                        break
                    if not item.is_dirty():
                        continue
                    mapping[f"{attr_name}:{item.__class__.__name__}:{item.unique_id()}"] =\
                        item.model_dump_json()
                    item.clear_dirty()
            else:
                continue
        if mapping:
            result = self.__client.hmset(self.unique_id(), mapping=mapping)
            if isinstance(result, Awaitable):
                await result
            print(f'{self.unique_id()} update {mapping}')

    async def load(self):
        result: Union[Awaitable[dict[str, bytes]], dict[str, bytes]] = self.__client.hgetall(
            self.unique_id())
        if isinstance(result, Awaitable):
            result = await result
        for key, value in result.items():
            if isinstance(key, bytes):
                key = key.decode()
            attr_name, orm_name = key.split(':')[:2]
            if attr_name not in self.__dict__:
                print(f'{attr_name} not in {self.unique_id()}')
                continue
            if orm_name not in _ORMS:
                print(f'{orm_name} not in _ORMS')
                continue
            attr = self.__dict__[attr_name]
            if isinstance(attr, ORMModel):
                # attr = _ORMS[orm_name].model_validate_json(value)
                self.__dict__[attr_name] = _ORMS[orm_name].model_validate_json(
                    value)
            elif isinstance(attr, list):
                attr.append(_ORMS[orm_name].model_validate_json(value))
            elif isinstance(attr, dict):
                if len(key.split(':')) != 3:
                    print(f'{key} is not a dict')
                    continue
                item_id = key.split(':')[-1]
                attr[item_id] = _ORMS[orm_name].model_validate_json(
                    value)
            else:
                # 类型不支持
                raise ValueError(f'{type(attr)} is not supported')
