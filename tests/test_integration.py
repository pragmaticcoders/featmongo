import bson
import datetime
import pytest

from feat.common import serialization, formatable

from featmongo import serializer, document


class TestDoc(document.Document):

    type_name = "test-doc"

    document.field('foo', None)
    document.field('bar', None)
    document.field('created_at', None)


class SomeObject(formatable.Formatable):

    formatable.field('field', None)


@pytest.fixture
def registry(request):
    registry = serialization.get_registry()

    snapshot = registry.get_snapshot()
    request.addfinalizer(lambda: registry.reset(snapshot))

    registry.register(TestDoc)
    registry.register(SomeObject)

    return registry


@pytest.fixture
def db(mongodb, registry):
    db = mongodb['test']
    db.add_son_manipulator(serializer.Transform(registry))
    return db


def test_create_fetch_delete(db):
    doc_id, = db.tests.insert([
        TestDoc(
            foo='foo',
            bar=SomeObject(field='value'),
            created_at=datetime.datetime.now(),
            ),
        ])
    assert isinstance(doc_id, bson.ObjectId)

    fetched = db.tests.find_one({'_id': doc_id})
    assert isinstance(fetched, TestDoc)
    assert isinstance(fetched.bar, SomeObject)
    assert fetched.bar.field == 'value'
    assert isinstance(fetched.created_at, datetime.datetime)
    assert isinstance(fetched._id, bson.ObjectId)
    assert fetched.foo == 'foo'

    db.tests.remove({'_id': doc_id})

    count = db.tests.find({'_id': doc_id}).count()
    assert count == 0


def test_update_with_complex_object(db):
    doc_id, = db.tests.insert([
        TestDoc(
            created_at=datetime.datetime.now(),
            ),
        ])
    r = db.tests.update({'_id': bson.ObjectId(doc_id)},
                   {'$set': {'bar': SomeObject(field='value'),
                             'foo': 'foo'}},
                   manipulate=True)

    fetched = db.tests.find_one({'_id': doc_id})
    assert isinstance(fetched, TestDoc)
    assert fetched.foo == 'foo'
    assert isinstance(fetched.bar, SomeObject)
    assert fetched.bar.field == 'value'
    assert isinstance(fetched.created_at, datetime.datetime)
    assert isinstance(fetched._id, bson.ObjectId)
