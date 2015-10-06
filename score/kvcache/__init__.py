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

from score.init import init_object, extract_conf, parse_time_interval, \
    ConfiguredModule
import logging


log = logging.getLogger(__name__)


def init(confdict):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:

    :confkey:`container`
        The cache container configuration. A container defines a name,
        a backend and optionally an expire. The configuration key for a
        container starts with ``container`` followed by the name and the
        configuration keys for the container.

        For example, the following configuration::

            container.greeter.backend = score.kvcache.backend.FileCache
            container.greeter.backend.path = /tmp/greeter.sqlite3
            container.greeter.expire = 1m

        The Backend config will be passed to
        :func:`score.init.init_object`. Have a look at the configurable
        backend's constructor parameters for further information about
        the backend's configurable keys.

        To make life easier for a huge set of container configurations, we serve
        the possibililty to configure backend aliases that will replace the
        container's backend config if the name matches.

        For example::

            backend.examplefilecache = score.kvcache.backend.FileCache
            backend.examplefilecache.path = /tmp/filecache.sqlite3
            container.greeter.backend = examplefilecache
            container.greeter.expire = 1m
            container.anothergreeter.backend = examplefilecache
            container.anothergreeter.expire = 30 seconds

    """
    containers = {}
    for container_conf in extract_conf(confdict, 'container.'):
        if not container_conf.endswith('.backend'):
            continue
        backend_key = 'container.%s' % container_conf
        backend_val = confdict[backend_key]
        if backend_val in extract_conf(confdict, 'backend.'):
            alias_conf = extract_conf(confdict, 'backend.%s' % backend_val)
            for k, v in alias_conf.items():
                confdict.update({'%s%s' % (backend_key, k): v})
        container_name = container_conf[:-len('.backend')]
        backend = init_object(confdict, backend_key)
        expire_key = 'container.%s.expire' % container_name
        expire = None
        if expire_key in confdict:
            expire = parse_time_interval(confdict[expire_key])
        containers[container_name] = CacheContainer(container_name, backend,
                                                    expire)
    return ConfiguredKvCacheModule(containers)


class ConfiguredKvCacheModule(ConfiguredModule):
    """
    This module's :class:`configuration object
    <score.init.ConfiguredModule>`.
    """

    def __init__(self, containers):
        super().__init__(__package__)
        self.containers = containers

    def __getitem__(self, container):
        """
        Gets a :class:`Cachecontainer <CacheContainer>` for given name.
        """
        return self.containers[container]

    def register_generator(self, container, generator):
        """
        Registers the generator to call if the cache is invalid.
        """
        if container not in self.containers:
            log.warn('Cache container "%s" not configured, using default.' %
                     container)
            self.create_container(container)
        self.containers[container].generator = generator

    def create_container(self, container, *, exist_ok=False):
        """
        Creates a container with given name and a
        :class:`VariableCache <backend.VariableCache>` and adds it to the
        configured :attr:`containers <ConfiguredKvCacheModule.containers>`.
        dictionary. Will raise a :class:`ContainerAlreadyConfigured` if
        *exist_ok=False* and the container is already configured.
        """
        if exist_ok is False and container in self.containers:
            raise ContainerAlreadyConfigured(container)
        from score.kvcache.backend import VariableCache
        self.containers[container] = CacheContainer(container, VariableCache())


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


class ContainerAlreadyConfigured(Exception):
    """
    Thrown while trying to create a :term:`cache container` that already exists.
    """
    pass
