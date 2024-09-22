# -*- coding= utf-8 -*-

__time__ = "2024/07/29"
__author__ = "虎小黑"


import inspect
from pydantic import BaseModel
from redis.asyncio import Redis
from orm.orm_model import ORMModel
from typing import Awaitable, Callable, Type, TypeVar, get_args

T = TypeVar("T", bound=ORMModel)

_ORMS: dict[str, Type[ORMModel]] = {}


class ORMCache(BaseModel):

    def __init__(self, client: Redis) -> None:
        super().__init__()
        self.__list_copy: dict[str, set[str]] = {}
        self.__dict_copy: dict[str, set[str]] = {}
        self.__client = client

    def unique_id(self) -> str:
        return self.__class__.__qualname__

    @classmethod
    def register(cls, _cls: Type[T]) -> Type[T]:
        if _cls.__qualname__ in _ORMS:
            raise ValueError(
                f"{_cls.__qualname__} has already been registered")
        _ORMS[_cls.__qualname__] = _cls
        return _cls

    async def save_all(self):
        modified: dict[str, ORMModel] = dict()
        del_fields: set[str] = set()
        for attr_name, attr in self.__dict__.items():
            if attr_name.startswith("_ORMCache"):
                continue
            if isinstance(attr, ORMModel):
                if not attr.is_dirty():
                    continue
                modified[
                    f"{attr_name}:{attr.__class__.__qualname__}:{attr.unique_id()}"] = attr
            elif isinstance(attr, list | set):
                list_copy: set[str] = set()
                for item in attr:
                    if not isinstance(item, ORMModel):
                        break
                    list_copy.add(
                        f"{attr_name}:{item.__class__.__qualname__}:{item.unique_id()}")
                    if not item.is_dirty():
                        continue
                    modified[
                        f"{attr_name}:{item.__class__.__qualname__}:{item.unique_id()}"] = item
                diff = self.__list_copy.get(attr_name, set()) - list_copy
                del_fields |= diff
                self.__list_copy[attr_name] = list_copy
            elif isinstance(attr, dict):
                dict_copy: set[str] = set()
                for _, item in attr.items():
                    if not isinstance(item, ORMModel):
                        break
                    dict_copy.add(
                        f"{attr_name}:{item.__class__.__qualname__}:{item.unique_id()}")
                    if not item.is_dirty():
                        continue
                    modified[
                        f"{attr_name}:{item.__class__.__qualname__}:{item.unique_id()}"] = item
                diff = self.__dict_copy.get(attr_name, set()) - dict_copy
                del_fields |= diff
                self.__dict_copy[attr_name] = dict_copy

        if modified:
            result = self.__client.hmset(
                self.unique_id(), mapping={key: value.encode() for key, value in modified.items()})
            if isinstance(result, Awaitable):
                await result
            for _, value in modified.items():
                value.clear_dirty()
        if del_fields:
            result = self.__client.hdel(self.unique_id(), *del_fields)
            if isinstance(result, Awaitable):
                await result

    async def load_from_redis(self, err_callback: Callable[[str, Exception], bool] | None = None) -> bool:
        result: Awaitable[dict[str, bytes]] | dict[str, bytes] = self.__client.hgetall(
            self.unique_id())
        if isinstance(result, Awaitable):
            result = await result
        for key, value in result.items():
            try:
                if isinstance(key, bytes):
                    key = key.decode()
                sp = key.split(":")
                if len(sp) != 3:
                    continue
                attr_name, orm_qualname, unique_id = sp
                if attr_name not in self.__annotations__ or \
                        attr_name not in self.__dict__ or \
                        orm_qualname not in _ORMS:
                    continue

                attr = self.__dict__[attr_name]
                if isinstance(attr, ORMModel):
                    attr = _ORMS[orm_qualname].decode(value)
                    self.__dict__[attr_name] = attr
                elif isinstance(attr, list | set):
                    arg_type = get_args(self.__annotations__[attr_name])[0]
                    if not inspect.isclass(arg_type) or not issubclass(arg_type, ORMModel):
                        continue
                    m = _ORMS[orm_qualname].decode(value)
                    if isinstance(attr, list):
                        attr.append(m)
                    else:
                        attr.add(m)
                    if attr_name not in self.__list_copy:
                        self.__list_copy[attr_name] = set()
                    self.__list_copy[attr_name].add(key)
                elif isinstance(attr, dict):
                    arg_type = get_args(self.__annotations__[attr_name])[1]
                    if not inspect.isclass(arg_type) or not issubclass(arg_type, ORMModel):
                        continue
                    m = _ORMS[orm_qualname].decode(value)
                    attr[unique_id] = m
                    if attr_name not in self.__dict_copy:
                        self.__dict_copy[attr_name] = set()
                    self.__dict_copy[attr_name].add(key)
                else:
                    raise TypeError(
                        f"{self.__class__.__qualname__}:{attr_name} {type(attr)} is not supported")
            except Exception as e:
                if err_callback and not err_callback(key, e):
                    return False
        return True
