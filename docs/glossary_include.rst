.. _kvcache_glossary:

.. glossary::

    cache container
        A :class:`cache container <score.kvcache.CacheContainer>` acts as a
        wrapper for different key-value pairs sharing some configuration and
        a registered callback function.

    cache value generator
        A callback function that will be invoked by a cache container using a
        key as argument if a requested value was not found in the
        :class:`cache backend <score.kvcache.backend.Backend>`.
