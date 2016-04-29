import bson
import datetime
import pytest

import serialization
from serialization import formatable

from featmongo import serializer, document


class TestDoc(document.Document):

    type_name = "test-doc"

    document.field('foo', None)
    document.field('bar', None)
    document.field('created_at', None)

    def recover(self, snapshot):
        super(TestDoc, self).recover(snapshot)


class TestVersionedDoc(document.VersionedDocument):

    type_name = "versioned-test-doc"

    version = 2

    document.field('foo', None)
    document.field('bar', 'default bar')

    @staticmethod
    def upgrade_to_2(snapshot):
        snapshot['foo'] = 'migrated foo'
        return snapshot

    @staticmethod
    def downgrade_to_2(snapshot):
        snapshot['foo'] = 'downgraded foo'
        return snapshot


class SomeObject(formatable.Formatable):

    formatable.field('field', None)


@pytest.fixture
def registry(request):
    registry = serialization.get_registry()

    snapshot = registry.get_snapshot()
    request.addfinalizer(lambda: registry.reset(snapshot))

    registry.register(TestDoc)
    registry.register(TestVersionedDoc)
    registry.register(SomeObject)
    print(SomeObject.type_name)

    return registry


class TestVersionedDocument(object):

    def test_provides_version_adapter(self):
        assert serialization.IVersionAdapter.providedBy(TestVersionedDoc)


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


def test_create_versioned_document(db):
    ids = db.tests.insert([
        TestVersionedDoc(foo='hello')
    ])
    assert db.tests.find_one({'foo': 'hello'})._id == ids[0]


def test_fetch_old_document(db):
    old_document = {
        'foo': 'hello',
        '_version': 1,
        '_type': 'versioned-test-doc',
    }
    ids = db.tests.insert([old_document])
    obj = db.tests.find_one(ids[0])
    assert obj.version == TestVersionedDoc.version
    assert obj.bar == 'default bar'


def test_upgrade_to_new_version(db):
    old_document = {
        'foo': 'hello',
        '_version': 1,
        '_type': 'versioned-test-doc',
    }
    ids = db.tests.insert([old_document])
    obj = db.tests.find_one(ids[0])
    assert obj.foo == 'migrated foo'


def test_downgrade_to_old_version(db):
    newer_document = {
        'foo': 'hello',
        '_version': 3,
        '_type': 'versioned-test-doc',
    }
    ids = db.tests.insert([newer_document])
    obj = db.tests.find_one(ids[0])
    assert obj.foo == 'downgraded foo'
