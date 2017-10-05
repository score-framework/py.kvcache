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

from abc import ABCMeta, abstractmethod
from score.kvcache import NotFound
import pickle
import time
import sqlite3


class Backend(metaclass=ABCMeta):

    @abstractmethod
    def store(self, container, key, value, expire=None):
        """
        Stores a value for given container name and key with given expire.
        """
        pass

    @abstractmethod
    def retrieve(self, container, key):
        """
        Retrieves a value for given container and key and raises an
        :class:`NotFound <score.kvcache.NotFound>` if the value is
        invalid.
        """
        return None

    @abstractmethod
    def invalidate(self, container, key):
        """
        Invalidates a value for given container and key.
        """
        return None


class VariableCache(Backend):
    """
    This backend implementation caches values in a variable. Note, that the
    expire is restricted to the process's lifetime.
    """

    def __init__(self):
        self.cache = {}

    def retrieve(self, container, key):
        try:
            return self.cache[container][key]
        except KeyError:
            raise NotFound()

    def store(self, container, key, value, expire=None):
        if container not in self.cache:
            self.cache[container] = {}
        self.cache[container][key] = value

    def invalidate(self, container, key):
        del self.cache[container][key]


class FileCache(Backend):
    """
    This backend implementation caches values in a sqlite3_ database with
    given path.
    """

    def __init__(self, path):
        self.path = path

    def retrieve(self, container, key):
        try:
            cursor = sqlite3.connect(self.path).cursor()
            cursor.execute('SELECT value '
                           'FROM kvcache WHERE container = ? AND key = ? AND '
                           'expire > ?', (container, key, time.time()))
            result = cursor.fetchone()
        except sqlite3.OperationalError:
            raise NotFound()
        if not result:
            raise NotFound()
        return pickle.loads(result[0])

    def store(self, container, key, value, expire=None):
        if expire is None:
            expire = 10**6
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR REPLACE INTO kvcache (container, key, '
                           'value, expire) VALUES (?, ?, ?, ?)',
                           (container, key, pickle.dumps(value),
                            time.time() + expire))
            conn.commit()
        except sqlite3.OperationalError:
            cursor.execute('CREATE TABLE IF NOT EXISTS kvcache ('
                           'container VARCHAR(255), '
                           'key VARCHAR(255), '
                           'value BLOB, '
                           'expire INTEGER, '
                           'PRIMARY KEY (container, key))')
            self.store(container, key, value, expire)

    def invalidate(self, container, key):
        self.store(container, key, None, time.time())


class SQLAlchemyCache(Backend):
    """
    This backend implementation caches values in a database supported by
    sqlalchemy_.

    .. _sqlalchemy: http://docs.sqlalchemy.org/en/latest/
    """

    def __init__(self, **confdict):
        from sqlalchemy import Column, String, Integer, Binary
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        from score.db import engine_from_config
        engine = engine_from_config(confdict)
        self.Session = sessionmaker(bind=engine)
        Base = declarative_base()
        Base.metadata.bind = engine
        self.kvcache_cls = type('KvCache', (Base,), {
            '__tablename__': 'kvcache',
            'container': Column(String(256), nullable=False, primary_key=True),
            'key': Column(String(256), nullable=False, primary_key=True),
            'value': Column(Binary),
            'expire': Column(Integer, nullable=False),
        })
        Base.metadata.create_all()

    def store(self, container, key, value, expire=None):
        try:
            key = str(key)
            if expire is None:
                expire = 10**6
            session = self.Session()
            cls = self.kvcache_cls
            entry = session.query(cls).\
                filter(cls.container == container).\
                filter(cls.key == key).\
                first()
            if not entry:
                entry = cls(container=container,
                            key=key,
                            value=pickle.dumps(value),
                            expire=time.time() + expire)
                session.add(entry)
                return
            entry.value = pickle.dumps(value)
            entry.expire = time.time() + expire
        except:
            session.rollback()
            session = None
            raise
        finally:
            if session:
                session.commit()

    def retrieve(self, container, key):
        try:
            key = str(key)
            session = self.Session()
            cls = self.kvcache_cls
            entry = session.query(cls).\
                filter(cls.container == container).\
                filter(cls.key == key).\
                filter(cls.expire > time.time()).\
                first()
            if not entry:
                raise NotFound()
            return pickle.loads(entry.value)
        except:
            session.rollback()
            session = None
            raise
        finally:
            if session:
                session.commit()

    def invalidate(self, container, key):
        self.store(container, key, None)
