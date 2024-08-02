# -*- coding= utf-8 -*-

__time__ = '2024/07/29'
__author__ = '虎小黑'

import unittest
from pydantic import Field
from orm.orm_model import ORMModel


class TestORMModel(unittest.TestCase):

    class Person(ORMModel):
        name: str = Field('', title='姓名')
        age: int = Field(0, title='年龄')
        sex: int = Field(0, title='性别', description='0: 女, 1: 男')

    def test_orm_model(self):
        person = self.Person(name='虎小黑', age=18, sex=0)

        assert person.name == '虎小黑'
        assert person.age == 18
        assert person.is_dirty()

        person.clear_dirty()
        assert not person.is_dirty()

        person.name = '小黑虎'
        assert person.is_dirty()

    def test_orm_model_dump(self):
        person = self.Person(name='虎小黑', age=18, sex=1)
        person1 = self.Person.model_validate_json(person.model_dump_json())

        assert person1.name == person.name
        assert person1.age == person.age
        assert person1.sex == person.sex

        assert person1 == person

        person1.name = '小黑虎'
        assert person1.name != person.name

    def test_orm_model_inherit(self):

        class SuperPerson(self.Person):
            hp: int = Field(0, title='生命值')
            skills: list[int] = Field([], title='技能', description='技能id列表')

        super_person = SuperPerson(
            name='虎小黑', age=18, sex=1, hp=100, skills=[1, 2, 3])
        assert super_person.name == '虎小黑'
        assert super_person.age == 18
        assert super_person.hp == 100
        assert super_person.skills == [1, 2, 3]

        assert super_person.is_dirty()
        super_person.clear_dirty()

        super_person.skills.append(4)
        assert super_person.is_dirty()
        super_person.clear_dirty()

        super_person1 = SuperPerson.model_validate_json(
            super_person.model_dump_json())
        assert super_person1.is_dirty()

        assert super_person1.name == super_person.name
        assert super_person1.age == super_person.age
        assert super_person1.hp == super_person.hp
        assert super_person1.skills == super_person.skills
        assert super_person1 == super_person

    def test_orm_model_combination(self):

        class Item(ORMModel):
            id: int = Field(0, title='id')
            name: str = Field('', title='名称')
            desc: str = Field('', title='描述')

        class Task(ORMModel):
            id: int = Field(0, title='id')
            name: str = Field('', title='名称')

        class SuperPerson(ORMModel):
            person: TestORMModel.Person = Field(self.Person(
                name='虎小黑', age=18, sex=1), title='人物')
            hp: int = Field(0, title='生命值')
            skills: list[int] = Field([], title='技能', description='技能id列表')
            items: list[Item] = Field([], title='物品列表')
            tasks: dict[int, Task] = Field({}, title='任务列表')

        super_person = SuperPerson(
            person=self.Person(name='虎小黑', age=19, sex=1), hp=100, skills=[1, 2, 3], items=[], tasks={})
        super_person.items.append(Item(id=1, name='item1', desc='desc1'))
        super_person.items.append(Item(id=2, name='item2', desc='desc2'))
        super_person.tasks[1] = Task(id=1, name='task1')
        super_person.tasks[2] = Task(id=2, name='task2')

        super_person.clear_dirty()
        super_person.items[0].name = 'item3'
        assert super_person.is_dirty()

        super_person.clear_dirty()
        super_person.items.append(Item(id=3, name='item3', desc='desc3'))
        assert super_person.is_dirty()

        super_person.clear_dirty()
        super_person.items.pop()
        assert super_person.is_dirty()

        super_person.clear_dirty()
        super_person.tasks[3] = Task(id=3, name='task3')
        assert super_person.is_dirty()

        super_person.clear_dirty()
        del super_person.tasks[1]
        assert super_person.is_dirty()
