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

from cstorage.manager import Manager

DEFAULT_TABLE = 'ccontext'


class Context(Manager):
    """
    Manage access to ccontext (connector, component, resource) entities
    and ccontext data (metric, downtime, etc.) related to ccontext entities.
    """

    CONF_FILE = '~/etc/context.conf'

    CONTEXT = 'ccontext'

    def _init_conf_files(self, conf_files, *args, **kwargs):

        result = super(Context, self)._init_conf_files(
            conf_files, *args, **kwargs)

        result.append(Context.CONF_FILE)

        return result

    def get_element(self, id, )

    def _get_timed_types(self):

        return [Manager.CONTEXT]