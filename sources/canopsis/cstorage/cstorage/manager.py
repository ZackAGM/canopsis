#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------
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

from cconfiguration import Configurable, Category, Parameter, Configuration
from ccommon.utils import resolve_element


class Manager(Configurable):

    CONF_FILE = '~/etc/manager.conf'

    TIMED_STORAGE = 'timed_storage'
    PERIODIC_STORAGE = 'periodic_storage'
    LAST_VALUE_STORAGE = 'last_value_storage'
    SHARED = 'shared'

    CATEGORY = 'MANAGER'

    STORAGE_SUFFIX = '_storage'

    _STORAGE_BY_DATA_TYPE_BY_TYPE = dict()

    def __init__(
        self, shared=True,
        last_value_storage=None, timed_storage=None, periodic_storage=None,
        *args, **kwargs
    ):

        super(Manager, self).__init__(*args, **kwargs)

        self.shared = shared

        self.periodic_storage = periodic_storage
        self.timed_storage = timed_storage
        self.last_value_storage = last_value_storage

    @property
    def shared(self):
        return self._shared

    @shared.setter
    def shared(self, value):
        self._shared = value

    @property
    def periodic_storage(self):
        return self._periodic_storage

    @periodic_storage.setter
    def periodic_storage(self, value):
        self._periodic_storage = value

    @property
    def timed_storage(self):
        return self._timed_storage

    @timed_storage.setter
    def timed_storage(self, value):
        self._timed_storage = value

    @property
    def last_value_storage(self):
        return self._last_value_storage

    @last_value_storage.setter
    def last_value_storage(self, value):
        self._last_value_storage = value

    def get_storage(
        self, data_type, storage_type, shared=None, *args, **kwargs
    ):
        """
        Load a storage related to input data type and storage type.

        If shared, the result instance is shared among same storage type and
        data type.

        :param data_type: storage data type
        :type data_type: str

        :param storage_type: storage type (among timed, last_value ,etc.)
        :type storage_type: Storage or str

        :param shared: if True, the result is a shared storage instance among
            managers. If None, use self.shared
        :type shared: bool

        :return: storage instance corresponding to input storage_type
        :rtype: Storage
        """

        result = None

        if shared is None:
            shared = self.shared

        if isinstance(storage_type, str):
            storage_type = resolve_element(storage_type)

        elif callable(storage_type):
            pass

        # if shared, try to find an instance with same storage and data types
        if shared:
            # search among isntances registred on storage_type
            storage_by_data_type = \
                Manager._STORAGE_BY_DATA_TYPE_BY_TYPE.setdefault(
                    storage_type, dict())

            if data_type not in storage_by_data_type:
                storage_by_data_type[data_type] = storage_type(
                    data_type=data_type, *args, **kwargs)

            result = storage_by_data_type[data_type]

        else:
            result = storage_type(data_type=data_type, *args, **kwargs)

        return result

    def get_timed_storage(
        self, data_type, timed_type=None, shared=None,
        *args, **kwargs
    ):

        if timed_type is None:
            timed_type = self.timed_storage

        result = self.get_storage(
            data_type=data_type, storage_type=timed_type, shared=shared,
            *args, **kwargs)

        return result

    def get_periodic_storage(
        self, data_type, periodic_type=None, shared=None,
        *args, **kwargs
    ):

        if periodic_type is None:
            periodic_type = self.periodic_storage

        result = self.get_storage(data_type=data_type, shared=shared,
            storage_type=periodic_type, *args, **kwargs)

        return result

    def get_last_value_storage(
        self, data_type, last_value_type=None, shared=None,
        *args, **kwargs
    ):

        if last_value_type is None:
            last_value_type = self.last_value_storage

        result = self.get_storage(data_type=data_type, shared=shared,
            storage_type=last_value_type, *args, **kwargs)

        return result

    def _get_conf_files(self, *args, **kwargs):

        result = super(Manager, self)._get_conf_files(*args, **kwargs)

        result.append(Manager.CONF_FILE)

        return result

    def _conf(self, *args, **kwargs):

        result = super(Manager, self)._conf(*args, **kwargs)

        result += Category(Manager.CATEGORY,
            Parameter(Manager.TIMED_STORAGE),
            Parameter(Manager.PERIODIC_STORAGE),
            Parameter(Manager.LAST_VALUE_STORAGE),
            Parameter(Manager.SHARED, parser=bool))

        return result

    def _configure(self, conf, *args, **kwargs):

        super(Manager, self)._configure(conf=conf, *args, **kwargs)

        values = conf[Configuration.VALUES]

        # set shared
        self._update_parameter(values, Manager.SHARED)

        # set all storages
        for parameter in values:
            if parameter.name.endswith(Manager.STORAGE_SUFFIX):
                self._update_parameter(values, parameter.name)
