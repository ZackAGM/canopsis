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
import logging
import time
import sys
import os

sys.path.append(os.path.expanduser('~/lib/canolibs/unittest/'))

import ctimemeasure
import managermock

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    )


class KnownValues(unittest.TestCase):

	def setUp(self):
		self.time_measure = ctimemeasure.CTimeMeasure('test', logging_level=logging.DEBUG)
		self.time_measure.manager = managermock.ManagerMock(self.time_measure)

	def test_1_Init(self):
		self.assertTrue(self.time_measure.logging_level == logging.DEBUG)
		self.assertTrue(self.time_measure.time_measures == {})
		self.assertTrue(self.time_measure.measure_name == 'test')

	def test_2_start(self):
		self.assertFalse(hasattr(self.time_measure,'previous_measure'))
		before = time.time()
		self.time_measure.start()
		self.assertTrue(hasattr(self.time_measure,'previous_measure'))
		self.assertTrue(self.time_measure.previous_measure >= before and self.time_measure.previous_measure <= time.time())

	def test_3_add_measure(self):
		# mainly check data structures
		self.time_measure.start()
		before = time.time()
		self.time_measure.add_measure('step')
		self.assertTrue('step' in self.time_measure.time_measures)
		time_measure_len = len(self.time_measure.time_measures['step'])
		self.assertTrue(time_measure_len > 0)
		#we got a delta
		self.assertTrue(self.time_measure.time_measures['step'][0] < time.time() - before)
		self.time_measure.add_measure('step')
		self.assertTrue(len(self.time_measure.time_measures['step']) > time_measure_len)
		self.time_measure.add_measure('step2')
		self.assertTrue('step2' in self.time_measure.time_measures)

	def test_4_publish(self):
		self.time_measure.publish()
		self.assertTrue(self.time_measure.manager.data == [])
		self.time_measure.start()
		self.time_measure.add_measure('step')
		self.time_measure.add_measure('step')
		measures = self.time_measure.time_measures['step']
		self.time_measure.publish()
		mean = sum(measures) / len(measures)
		self.assertTrue(self.time_measure.manager.data[0]['value'] == mean)
		self.assertTrue(self.time_measure.manager.data[0]['name'] == 'test_time_measurestepcps_eventstore_time')

	def test_5_canPublish(self):
		self.assertTrue(self.time_measure.canPublish())
		self.time_measure.logging_level = logging.INFO
		self.assertTrue(self.time_measure.canPublish())
		self.time_measure.logging_level = logging.ERROR
		self.assertFalse(self.time_measure.canPublish())


if __name__ == "__main__":
	unittest.main(verbosity=2)
