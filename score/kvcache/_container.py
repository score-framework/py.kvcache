# Copyright © 2015 STRG.AT GmbH, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in the
# file named COPYING.LESSER.txt.
#
# The SCORE Framework and all its parts are distributed without any WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. For more details see the GNU Lesser General Public
# License.
#
# If you have not received a copy of the GNU Lesser General Public License see
# http://www.gnu.org/licenses/.
#
# The License-Agreement realised between you as Licensee and STRG.AT GmbH as
# Licenser including the issue of its valid conclusion and its pre- and
# post-contractual effects is governed by the laws of Austria. Any disputes
# concerning this License-Agreement including the issue of its valid conclusion
# and its pre- and post-contractual effects are exclusively decided by the
# competent court, in whose district STRG.AT GmbH has its registered seat, at
# the discretion of STRG.AT GmbH also the competent court, in whose district the
# Licensee has his registered seat, an establishment or assets.


class CacheContainer:
    """
    A cache container to wrap key-value pairs.
    """

    def __init__(self, name, backend, expire=None):
        self.name = name
        self.backend = backend
        self.expire = expire
        self.generator = None

    def __delitem__(self, key):
        """
        Invalidates a value for given key.
        """
        self.backend.invalidate(self.name, key)

    def __setitem__(self, key, value):
        """
        Explicitly sets a value for given key ignoring validity.
        """
        self.backend.store(self.name, key, value, self.expire)

    def __getitem__(self, key):
        """
        Gets a value for given key and takes care of not found cache items.
        """
        try:
            value = self.backend.retrieve(self.name, key)
        except NotFound:
            if self.generator is None:
                raise
            value = self.generator(key)
            self[key] = value
        return value


class NotFound(Exception):
    """
    Thrown if cache is invalid (either expired or not available).
    """
    pass
