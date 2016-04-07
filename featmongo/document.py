from feat.common import formatable, serialization
from serializer import VERSION_ATOM


field = formatable.field


class MetaVersionedFormatable(
        type(formatable.Formatable), type(serialization.VersionAdapter)):
    pass


class VersionedFormatable(formatable.Formatable, serialization.VersionAdapter):

    __metaclass__ = MetaVersionedFormatable

    version = 1

    def snapshot(self):
        snapshot = formatable.Formatable.snapshot(self)
        return self.store_version(snapshot, self.version)

    def store_version(self, snapshot, version):
        snapshot[str(VERSION_ATOM)] = version
        return snapshot


class Document(formatable.Formatable):

    field('_id', None, '_id')


class VersionedDocument(VersionedFormatable):

    field('_id', None, '_id')