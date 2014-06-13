#!/usr/bin/env python
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

import unittest
import sys
import os
import time
import logging


sys.path.append(os.path.expanduser('~/lib/canolibs/unittest/'))
sys.path.append(os.path.expanduser('~/opt/amqp2engines/engines/'))


#from crecord import crecord
from cstorage import get_storage
from caccount import caccount

import eventstore
import camqpmock
import managermock

import pprint
pp = pprint.PrettyPrinter(indent=2)

class KnownValues(unittest.TestCase):
	def setUp(self):

		self.storage = get_storage(namespace='object', account=caccount(user="root", group="root"))

		self.engine = eventstore.engine(logging_level=logging.DEBUG)
		self.engine.archiver.autolog = False
		#mock for amqp and manager, allowing to manager events and perfdata for testing purposes
		self.engine.amqp = camqpmock.CamqpMock(self.engine)
		self.engine.manager = managermock.ManagerMock(self.engine)

		#self.engine.beat()
		now = int(time.time())

		event = {
			'timestamp': now,
			'component': 'event_store_test',
			'connector': 'test',
			'connector_name': 'test',
			'event_type': 'check',
			'source_type': 'source',
			'state': 1,
			'state_type': 1,
			'resource': 'resource_{}'.format(now)
		}

		routing_key = '.'.join([event[key] for key in ('connector', 'connector_name', 'event_type', 'source_type', 'component', 'resource')])
		event['rk'] = routing_key
		self.event = event

	def test_01_work_init(self):
		self.engine.work(self.event)
		inserted_event = self.storage.get_backend('events').find_one({'timestamp': self.event['timestamp']})

		for extra_key in ['perf_data_array', 'event_id']:
			if extra_key in self.event:
				del self.event[extra_key]


		for key in self.event:
			self.assertTrue(self.event[key] == inserted_event[key])

		self.show()

	def reset_data(self):
		#init engine as needed

		self.engine.manager.clean()
		self.engine.amqp.clean()


	def show(self):
		print 'DATA'
		for d in self.engine.manager.data:
			print d
		print 'Events'
		for e in self.engine.amqp.events:
			print e


if __name__ == "__main__":
	unittest.main()
