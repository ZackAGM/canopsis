#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------
# Copyright (c) 2014 "Capensis" [http://www.capensis.com]
#
# This file is part of Canopsis.
#
# Canopsis is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Canopsis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Canopsis.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------

from unittest import TestCase, main

from canopsis.common.utils import path
from canopsis.task import (
    __TASKS_BY_ID as TASKS_BY_ID, TASK_PARAMS, TASK_ID, TaskError,
    get_task, new_conf, get_task_with_params,
    run_task, register_tasks, register_task, unregister_tasks
)


def test_exception(**kwargs):
    raise Exception()

COUNT = 'count'


class TaskUnregisterTest(TestCase):
    """
    Test unregister_tasks function
    """

    def setUp(self):
        """
        Create two tasks for future unregistration.
        """

        # clear dico and add only self names
        TASKS_BY_ID.clear()
        self.names = 'a', 'b'
        for name in self.names:
            register_tasks(**{name: None})

    def tearDown(self):
        """
        Empty task_by_id.
        """

        TASKS_BY_ID.clear()

    def test_unregister(self):
        """
        Unregister one by one
        """

        for name in self.names:
            unregister_tasks(name)
            self.assertNotIn(name, TASKS_BY_ID)

    def test_unregister_all(self):
        """
        Unregister all tasks at a time.
        """

        unregister_tasks(*self.names)
        self.assertFalse(TASKS_BY_ID)

    def test_unregister_clear(self):
        """
        Unregister all tasks with an empty parameter.
        """

        unregister_tasks()
        self.assertFalse(TASKS_BY_ID)


class TaskRegistrationTest(TestCase):
    """
    Test to register tasks.
    """

    def setUp(self):
        """
        """
        # clean task paths
        TASKS_BY_ID.clear()
        self.tasks = {'a': 1, 'b': 2, 'c': 3}
        register_tasks(**self.tasks)

    def tearDown(self):
        """
        Empty task_by_id.
        """

        TASKS_BY_ID.clear()

    def test_register(self):
        """
        Check for registered task in registered tasks
        """
        for task in self.tasks:
            self.assertIn(task, TASKS_BY_ID)

    def test_register_raise(self):
        """
        Test to catch TaskError while registring already present tasks.
        """

        self.assertRaises(TaskError, register_tasks, **self.tasks)

    def test_register_force(self):
        """
        Test to register existing tasks with force.
        """

        self.assertNotIn('d', TASKS_BY_ID)
        new_tasks = {'a': 'a', 'c': 'c', 'd': 'd'}
        old_tasks = register_tasks(
            force=True, **new_tasks
        )
        for new_task in new_tasks:
            self.assertEqual(get_task(new_task), new_tasks[new_task])
        self.assertNotIn('b', old_tasks)
        self_tasks_wo_b = self.tasks
        del self_tasks_wo_b['b']
        self.assertEqual(old_tasks, self_tasks_wo_b)


class GetTaskTest(TestCase):
    """
    Test get task function.
    """

    def setUp(self):
        # clean all task paths
        TASKS_BY_ID.clear()

    def tearDown(self):
        """
        Empty task_by_id.
        """

        TASKS_BY_ID.clear()

    def test_get_unregisteredtask(self):
        """
        Test to get unregistered task.
        """

        getTaskTest = path(GetTaskTest)
        task = get_task(getTaskTest)
        self.assertEqual(task, GetTaskTest)

    def test_get_registeredtask(self):
        """
        Test to get registered task.
        """

        _id = 'a'
        register_tasks(**{_id: GetTaskTest})
        task = get_task(_id=_id)
        self.assertEqual(task, GetTaskTest)


class TaskRegistrationDecoratorTest(TestCase):
    """
    Test registration decorator
    """

    def setUp(self):
        TASKS_BY_ID.clear()

    def test_register_without_parameters(self):

        @register_task
        def register():
            pass
        self.assertIn(path(register), TASKS_BY_ID)

    def test_register(self):

        @register_task()
        def register():
            pass
        self.assertIn(path(register), TASKS_BY_ID)

    def test_registername(self):

        _id = 'toto'

        @register_task(_id)
        def register():
            pass
        self.assertIn(_id, TASKS_BY_ID)

    def test_raise(self):

        def toto():
            pass
        _id = path(toto)

        register_tasks(**{_id: 6})

        self.assertRaises(TaskError, register_task, toto)


class GetTaskWithParamsTest(TestCase):
    """
    Test get task with params function.
    """

    def setUp(self):

        self.wrong_function = 'test.test'

        self.existing_function = 'canopsis.task.get_task_with_params'

    def test_none_task_from_str(self):

        conf = self.wrong_function

        self.assertRaises(ImportError, get_task_with_params, conf=conf)

    def test_none_task_from_dict(self):

        conf = {TASK_ID: self.wrong_function}

        self.assertRaises(ImportError, get_task_with_params, conf=conf)

    def test_task_from_str(self):

        conf = self.existing_function

        task, params = get_task_with_params(conf=conf)

        self.assertEqual((task, params), (get_task_with_params, {}))

    def test_task_from_dict(self):

        conf = {TASK_ID: self.existing_function}

        task, params = get_task_with_params(conf=conf)

        self.assertEqual((task, params), (get_task_with_params, {}))

    def test_task_from_dict_with_params(self):

        param = {'a': 1}

        conf = {
            TASK_ID: self.existing_function,
            TASK_PARAMS: param}

        task, params = get_task_with_params(conf=conf)

        self.assertEqual((task, params), (get_task_with_params, param))

    def test_cache(self):

        conf = self.existing_function

        task_not_cached_0, _ = get_task_with_params(
            conf=conf, cache=False)

        task_not_cached_1, _ = get_task_with_params(
            conf=conf, cache=False)

        self.assertTrue(task_not_cached_0 is task_not_cached_1)

        task_cached_0, _ = get_task_with_params(conf=conf)

        task_cached_1, _ = get_task_with_params(conf=conf)

        self.assertTrue(task_cached_0 is task_cached_1)


if __name__ == '__main__':
    main()
