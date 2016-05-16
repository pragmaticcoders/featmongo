import serialization
from serialization import formatable
from six import with_metaclass

field = formatable.field


class Document(formatable.Formatable):

    field('_id', None, '_id')


class VersionedDocument(formatable.VersionedFormatable):

    field('_id', None, '_id')
