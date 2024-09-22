# -*- coding= utf-8 -*-

from typing import Any, Self
from pydantic import BaseModel


class ORMModel(BaseModel):

    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self.__copy: Self | None = None

    def unique_id(self) -> str:
        raise NotImplementedError

    def __delattr__(self, _: str) -> None:
        raise AttributeError("ORMModel is immutable")

    def is_dirty(self) -> bool:
        return self != self.__copy

    def encode(self) -> str:
        return self.model_dump_json()

    @classmethod
    def decode(cls, data:  str | bytes | bytearray) -> Self:
        m = cls.model_validate_json(data)
        m.clear_dirty()
        return m

    def clear_dirty(self) -> None:
        self.__copy = self.model_copy(deep=True)
