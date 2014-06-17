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

__all__ = ('TimedStorage')

from cstorage import Storage


class TimedStorage(Storage):
    """
    Store dedicated to manage timed data.
    """

    TIMESTAMP_INDEX = 0
    VALUE_INDEX = 1

    DATA_ID = 'data_id'
    VALUE = 'values'
    TIMESTAMP = 'timestamp'

    def get(
        self, data_ids, timewindow=None, limit=0, skip=0, sort=None,
        *args, **kwargs
    ):
        """
        Get a sorted list of triplet of dictionaries such as :
        tuple(
            timestamp,
            dict(data_type, data_value), dict(meta_name, meta_value)).

        If timewindow is None, result is all timed document.
        """

        raise NotImplementedError()

    def count(self, data_id, *args, **kwargs):
        """
        Get number of timed documents for input data_id.
        """

        raise NotImplementedError()

    def put(self, data_id, value, timestamp, *args, **kwargs):
        """
        Put a dictionary of value by name in collection.
        """

        raise NotImplementedError()

    def remove(self, data_ids, timewindow=None, *args, **kwargs):
        """
        Remove timed_data existing on input timewindow.
        """

        raise NotImplementedError()

    def _get_storage_type(self, *args, **kwargs):
        """
        Get collection prefix.
        """

        return "timed"
