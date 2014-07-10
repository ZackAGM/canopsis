#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------
# Copyright (c) 2011 "Capensis" [http://www.capensis.com]
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

from canopsis.engine import Engine
from canopsis.old.storage import get_storage
from canopsis.old.account import Account

from pyperfstore2 import manager

from time import time

LOCK_DELAY = 300
LOCK_QUERY = {'crecord_name': 'lock_perfstore2_rotate'}


class engine(Engine):
    etype = 'perfstore2_rotate'

    def __init__(self, *args, **kargs):
        super(engine, self).__init__(*args, **kargs)

        self.beat_interval = 10

        self.kplan = "perfstore2:rotate:plan"

        self.rotation_interval = 60 * 60 * 24  # 24 hours

        self.last_build = time()

    def pre_run(self):
        self.manager = manager(logging_level=self.logging_level)
        self.storage = get_storage(
            namespace='object', account=Account(user="root", group="root"))
        self.beat()

    def consume_dispatcher(self, event, *args, **kargs):
        """
        This method performs a rotation for metric stored in temporary collection.
        It cannot be run twice at the same time in HA mode, so lock is put around the core method execution
        """
        self.logger.info("Entered in rotation")

        lock = self.storage.get_backend('object').find_one(LOCK_QUERY)
        if lock is None or lock['isFree'] or time() - lock['last_update'] > LOCK_DELAY:

            self.logger.info('Starting rotation')
            try:
                self.storage.get_backend('object').update(LOCK_QUERY, {'$set': {'last_update': time(), 'isFree': False}}, upsert=True)
                start = time()
                metric_to_rotate = self.manager.store.daily_collection.find({'insert_date': {'$lte': start - self.rotation_interval}})

                metric_count = 0
                for metric in metric_to_rotate:
                    self.manager.rotate(metric['_id'], metric['values'])
                    metric_count += 1

                elapsed = time() - start
                self.counter_event += metric_count
                self.counter_worktime += elapsed

                if elapsed > self.beat_interval - 3:
                    self.logger.warning("Rotation time %s s is to close from beat interval (%s s)" % (int(elapsed), self.beat_interval) )

                self.logger.debug("Done in %.2f ms", int(elapsed * 1000))

            except Exception as e:
                self.logger.error(
                    'Unable to perform rotation properly: {}'.format(e))

            self.storage.get_backend('object').update(
                LOCK_QUERY,
                {'$set': {'last_update': time(), 'isFree': True}},
                upsert=True)

        else:
            last_update = 0
            if lock:
                last_update = int(time() - lock['last_update'])
            self.logger.info(
                'Not yet ready, passing rotation. last update was {0} seconds delay is {1} seconds'.format(last_update, LOCK_DELAY))