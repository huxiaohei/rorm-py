# -*- coding= utf-8 -*-

__time__ = '2024/07/29'
__author__ = '虎小黑'


from typing import Any
from pydantic import BaseModel


class ORMModel(BaseModel):

    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self.__dirty = True
        self.__initialised = True

    def unique_id(self) -> str:
        return self.__class__.__name__

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__dict__.get('_ORMModel__initialised', False):
            if name not in self.__dict__:
                raise AttributeError('ORMModel is immutable')
            if name not in ('_ORMModel__initialised', '_ORMModel__dirty'):
                print('{0} Update {1} from {2} to {3}'
                      .format(self.unique_id(), name, getattr(self, name), value))
            super().__setattr__('_ORMModel__dirty', True)
        super().__setattr__(name, value)

    def __delattr__(self, _: str) -> None:
        raise AttributeError('ORMModel is immutable')

    def is_dirty(self) -> bool:
        return self.__dirty

    def clear_dirty(self) -> None:
        self.__dirty = False

    def is_initialised(self) -> bool:
        return self.__initialised
