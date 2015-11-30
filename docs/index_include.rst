.. module:: score.kvcache
.. role:: faint
.. role:: confkey

*************
score.kvcache
*************

Introduction
============

This module allows storing python objects in key-value storages. It can
be used, for example, to cache frequently used data to avoid calling APIs
too often or to avoid exceeding the number of allowed calls to a service. It
should not be used to persist data, since it cannot guarantee that data is
retained, even if the specified expiration is not reached. Where and how long
the data is stored depends on the configurable backend.

How it works
============

This module uses configurable :term:`cache containers <cache container>` to
store values with different lifetimes and :term:`generators <cache value
generator>`. A :term:`cache value generator` is a function, that needs to be
configured or registered with the container. The cache container will invoke
this cache value generator to obtain the matching cache value for the
requested key.

If you want to configure your generator, have a look at the
:ref:`Configuration <kvcache_configuration>`. The registration of a
:term:`cache value generator` can be done by calling the container's
:meth:`ConfiguredKvCacheModule.register_generator` method:

.. code-block:: python

    import score.kvcache

    def greeting_generator(name):
        print('Generating the value for key "%s".' % name)
        return 'Hello %s!' % name

    kvcache = score.kvcache.init({
        'backend.variable': 'score.kvcache.backend.VariableCache',
        'container.greeting.backend': 'variable',
    })

    kvcache.register_generator('greeting', greeting_generator)

    print(kvcache['greeting']['Peter'])
    print(kvcache['greeting']['Peter'])
    print(kvcache['greeting']['William'])

The output will be::

    Generating the value for key "Peter".
    Hello Peter!
    Hello Peter!
    Generating the value for key "William".
    Hello William!

In this scenario, the configured kvcache will operate only on one container
called *greeting*. The container is associated with the backend called
*variable*, which is a dummy backend storing values in a python `dict`.

The first time the container is accessed with the key *Peter*, the container
will consult its backend and catch a :class:`NotFound` Exception. Since it was
not possible to retrieve the value from cache, it will invoke the registered
generator to create the desired value ("Hello Peter!").

The backend is then instructed to store the value, having it available the next
time the container is requested to retrieve the exact same key.

If we had chosen a more elaborate backend, we could have even configured an
:attr:`expiration time <score.kvcache.CacheContainer.expire>` for the values in
our container.


.. _kvcache_configuration:

Configuration
=============

.. autofunction:: init

.. autoclass:: ConfiguredKvCacheModule

    .. attribute:: containers

        A dictionary containing all configured
        :class:`CacheContainer <CacheContainer>`. The keys of the
        dictionary represent the container names.

    .. automethod:: __getitem__

    .. automethod:: register_generator

    .. automethod:: create_container

.. autoclass:: CacheContainer

    .. attribute:: name

        The container name.

    .. attribute:: backend

        The container :class:`Backend <backend.Backend>`.

    .. attribute:: expire

        The expire parsed by :func:`score.init.parse_time_interval`. May be
        ``None``.

    .. attribute:: generator

        The generator registered by
        :func:`ConfiguredKvCacheModule.register_generator`. The argument of
        the generator represents the key of the cache item.

    .. automethod:: __delitem__

    .. automethod:: __getitem__

    .. automethod:: __setitem__

.. autoclass:: score.kvcache.backend.Backend

    .. automethod:: score.kvcache.backend.Backend.store

    .. automethod:: score.kvcache.backend.Backend.retrieve

    .. automethod:: score.kvcache.backend.Backend.invalidate

.. autoclass:: NotFound

.. autoclass:: ContainerAlreadyConfigured

Ready-to-use Backends
=====================

.. autoclass:: score.kvcache.backend.VariableCache

.. autoclass:: score.kvcache.backend.FileCache

    .. attribute:: path

            The path to the sqlite3_ file.

    .. _sqlite3: https://docs.python.org/3/library/sqlite3.html

.. autoclass:: score.kvcache.backend.SQLAlchemyCache

    .. attribute:: confdict

        The sqlalchemy_ configuration dictionary. All configuration keys must
        start with *sqlalchemy*. The dictionary will be passed to
        :func:`sqlalchemy.engine_from_config`, which in turn calls
        :func:`sqlalchemy.create_engine` with these configuration values as
        keyword arguments. Usually the following is sufficient::

            sqlalchemy.url = postgresql://dbuser@localhost/dbname

    .. _sqlalchemy: http://docs.sqlalchemy.org/en/latest/
