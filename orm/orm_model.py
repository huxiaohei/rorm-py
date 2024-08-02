# -*- coding= utf-8 -*-

__time__ = '2024/07/29'
__author__ = '虎小黑'


from typing import Any, Self
from pydantic import BaseModel


class ORMModel(BaseModel):

    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self.__copy: Self | None = None

    def unique_id(self) -> str:
        return self.__class__.__name__

    def __delattr__(self, _: str) -> None:
        raise AttributeError('ORMModel is immutable')

    def is_dirty(self) -> bool:
        return self != self.__copy

    def clear_dirty(self) -> None:
        self.__copy = self.model_copy(deep=True)
