import os
import tempfile
import pytest
import score.kvcache
from test.initializer import valid_greeter


base_conf = {
        'backend.dbcache': 'score.kvcache.backend.SQLAlchemyCache',
        'backend.dbcache.sqlalchemy.url':
            'postgresql://postgres:postgrespw@localhost/score',
        'backend.filecache': 'score.kvcache.backend.FileCache',
        'backend.filecache.path':
            tempfile.gettempdir() + os.path.sep + 'score_kvcache_test.sqlite3',
        'backend.varcache': 'score.kvcache.backend.VariableCache',
        'container.greeter_file.backend': 'filecache',
        'container.greeter_file.expire': '5 sec',
        'container.greeter_var.backend': 'varcache',
        'container.greeter_var.expire': '5 sec',
    }


def test_missing_generator():
    kvcache = score.kvcache.init(base_conf)
    with pytest.raises(score.kvcache.NotFound):
        kvcache['greeter_var']['Peter']


def test_registered_generator():
    def welcome(name):
        return 'Welcome %s!' % name
    kvcache = score.kvcache.init(base_conf)
    kvcache.register_generator('welcome_var', welcome)
    assert kvcache['welcome_var']['William'] == welcome('William')


def test_configured_generator():
    config = base_conf.copy()
    config.update({
        'container.greeter_file.generator':
            'test.initializer.valid_greeter.greeter',
        'container.greeter_var.generator':
            'test.initializer.valid_greeter.greeter',
    })
    kvcache = score.kvcache.init(config)
    # with FileCache
    assert isinstance(kvcache, score.kvcache.ConfiguredKvCacheModule)
    assert isinstance(kvcache['greeter_file'], score.kvcache.CacheContainer)
    assert kvcache['greeter_file']['Peter'] == valid_greeter.greeter('Peter')
    assert kvcache['greeter_file']['William'] == \
           valid_greeter.greeter('William')
    # with VariableCache
    assert isinstance(kvcache, score.kvcache.ConfiguredKvCacheModule)
    assert isinstance(kvcache['greeter_var'], score.kvcache.CacheContainer)
    assert kvcache['greeter_var']['Peter'] == valid_greeter.greeter('Peter')
    assert kvcache['greeter_var']['William'] == valid_greeter.greeter('William')
