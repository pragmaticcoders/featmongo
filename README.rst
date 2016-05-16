Featmongo
---------

.. image:: https://img.shields.io/travis/kowalski/featmongo.svg
        :target: https://travis-ci.org/kowalski/featmongo

.. image:: https://img.shields.io/pypi/v/featmongo.svg
        :target: https://pypi.python.org/pypi/featmongo


This is a wrapper allowing the usage of `serialization` (https://github.com/pragmaticcoders/serialization) with `pymongo`.


Usage
=====

::

    from bson.objectid import ObjectId
    import serialization
    from featmongo import serializer, document
    from pymongo import MongoClient


    @serialization.register
    class TestDoc(document.Document):

        type_name = "test-doc"

        document.field('foo', None)


    client = MongoClient('mongodb://localhost:27017')
    db = client['test']
    # This configures the client to use the serialization layer.
    db.add_son_manipulator(serializer.Transform())

    print db.tests.insert([TestDoc(foo='bar')])
    #> [ObjectId('5416df0728fcb236317dff7d')]
    print db.tests.find_one({'foo': 'bar'})
    #> <TestDoc {'_id': ObjectId('5416df0728fcb236317dff7d'), 'foo': u'bar'}>


Changes
=======

=============
Version 0.3.1
=============

* Adapt to `serialization` version 1.2.0.

=============
Version 0.3.0
=============

* Python 3 support. Drop support from `feat`. Use `serialization` instead.

=============
Version 0.2.0
=============

* Add support for handling different versions of documents loaded from mongo.
