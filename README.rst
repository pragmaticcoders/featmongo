This is a wrapper allowing the usage of `feat` (https://github.com/f3at/feat.git)
serialization layer with `pymongo`.


Usage
-----

::

    from bson.objectid import ObjectId
    from feat.common import serialization
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
-------

Version 0.2.0
=============

* Add support for handling different versions of documents loaded from mongo.
