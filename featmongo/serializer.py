import bson
import datetime
import threading

from six import iteritems
from past.types import unicode, long
from future.utils import PY3
from serialization import reflect
from serialization import base, json_ as json

from pymongo.son_manipulator import SONManipulator


TUPLE_ATOM = u"_tuple"
BYTES_ATOM = u"_bytes"
BYTES_ENCODING = "BASE64"
ENCODED_ATOM = u"_enc"
SET_ATOM = u"_set"
ENUM_ATOM = u"_enum"
TYPE_ATOM = u"_type"
EXTERNAL_ATOM = u"_ext"
REFERENCE_ATOM = u"_ref"
DEREFERENCE_ATOM = u"_deref"
FUNCTION_ATOM = u"_function"
INSTANCE_TYPE_ATOM = u"_type"
INSTANCE_STATE_ATOM = u"_state"

VERSION_ATOM = '_version'

DEFAULT_ENCODING = "UTF8"
ALLOWED_CODECS = set(["UTF8", "UTF-8", "utf8"])


class Serializer(base.Serializer):

    pack_dict = dict

    def __init__(self, force_unicode=True):
        base.Serializer.__init__(
            self,
            converter_caps=json.JSON_CONVERTER_CAPS,
            freezer_caps=json.JSON_FREEZER_CAPS,
            version_atom=VERSION_ATOM,
        )
        self._force_unicode = force_unicode

    def flatten_passthrough(self, value, caps, freezing):
        return value

    def get_target_ver(self, instance, snapshot):
        return getattr(instance, 'version', None)

    def get_source_ver(self, instance, snapshot):
        return getattr(instance, 'version', None)

    ### lookup tables ###

    _value_lookup = dict(base.Serializer._value_lookup)

    for passthrough_type in (datetime.datetime, bson.regex.Regex,
                             bson.binary.Binary, bson.ObjectId,
                             bson.dbref.DBRef, bson.code.Code):
        _value_lookup[passthrough_type] = flatten_passthrough

    ### Overridden Methods ###

    def flatten_key(self, key, caps, freezing):
        if not isinstance(key, bytes):
            if isinstance(key, unicode) and self._force_unicode:
                return key
            else:
                raise TypeError("Serializer %s is not capable of serializing "
                                "non-string dictionary keys: %r"
                                % (reflect.canonical_name(self), key))
        # Flatten it as unicode by using the selected encoding
        return self.pack_unicode, key.decode(DEFAULT_ENCODING)

    def pack_tuple(self, data):
        # JSON do not support tuple so we just fake it
        return [TUPLE_ATOM] + data

    def pack_str(self, data):
        # we try to decode the string from default encoding
        try:
            value = data.decode(DEFAULT_ENCODING)
            if self._force_unicode:
                return value
            return [ENCODED_ATOM, DEFAULT_ENCODING, value]
        except UnicodeDecodeError:
            # if it fail store it as base64 encoded bytes
            return [BYTES_ATOM, data.encode(BYTES_ENCODING).strip()]

    def pack_set(self, data):
        return [SET_ATOM] + data

    def pack_enum(self, data):
        return [ENUM_ATOM, reflect.canonical_name(data) + "." + data.name]

    def pack_type(self, data):
        return [TYPE_ATOM, reflect.canonical_name(data)]

    def pack_external(self, data):
        return [EXTERNAL_ATOM] + data

    def pack_instance(self, data):
        type_name, snapshot = data

        if isinstance(snapshot, dict):
            result = dict(snapshot) # Copy the dict to not modify the original
            assert INSTANCE_TYPE_ATOM not in result
            assert INSTANCE_STATE_ATOM not in result
            result[INSTANCE_TYPE_ATOM] = type_name
            return result

        return {INSTANCE_TYPE_ATOM: type_name,
                INSTANCE_STATE_ATOM: snapshot}

    def pack_reference(self, data):
        return [REFERENCE_ATOM] + data

    def pack_dereference(self, data):
        return [DEREFERENCE_ATOM, data]

    def pack_frozen_external(self, data):
        snapshot, = data
        return snapshot

    def pack_frozen_instance(self, data):
        snapshot, = data
        return snapshot

    def pack_frozen_function(self, data):
        return reflect.canonical_name(data)

    def pack_function(self, data):
        return [FUNCTION_ATOM, reflect.canonical_name(data)]

    pack_frozen_builtin = pack_frozen_function
    pack_frozen_method = pack_frozen_function


class Unserializer(base.Unserializer):

    pass_through_types = set([bytes, unicode, int, long,
                              float, bool, type(None),
                              datetime.datetime, bson.regex.Regex,
                              bson.binary.Binary, bson.ObjectId,
                              bson.dbref.DBRef, bson.code.Code])

    def __init__(self, registry=None, externalizer=None,
                 source_ver=None, target_ver=None):
        base.Unserializer.__init__(self,
                                   converter_caps=json.JSON_CONVERTER_CAPS,
                                   registry=registry,
                                   )

    def get_target_ver(self, restorator, snapshot):
        return getattr(restorator, 'version', None)

    def get_source_ver(self, restorator, snapshot):
        return snapshot.get(VERSION_ATOM, 1)

    ### Overridden Methods ###

    def pre_convertion(self, data):
        return data

    def analyse_data(self, data):
        if isinstance(data, dict):
            if INSTANCE_TYPE_ATOM in data:
                return data[INSTANCE_TYPE_ATOM], Unserializer.unpack_instance
            return dict, Unserializer.unpack_dict

        if isinstance(data, list):
            default = list, Unserializer.unpack_list
            if not data:
                # Empty list
                return default
            key = data[0]
            if isinstance(key, unicode):
                return self._list_unpackers.get(key, default)
            # Just a list
            return default

    ### Private Methods ###

    def unpack_instance(self, data, *args):
        data = dict(data)
        type_name = data.pop(INSTANCE_TYPE_ATOM)
        if INSTANCE_STATE_ATOM in data:
            snapshot = data.pop(INSTANCE_STATE_ATOM)
        else:
            snapshot = data
        return self.restore_instance(type_name, snapshot, *args)

    def unpack_external(self, data):
        _, identifier = data
        return self.restore_external(identifier)

    def unpack_reference(self, data):
        _, refid, value = data
        return self.restore_reference(refid, value)

    def unpack_dereference(self, data):
        _, refid = data
        return self.restore_dereference(refid)

    def unpack_enum(self, data):
        _, full_name = data
        parts = full_name.split('.')
        type_name = ".".join(parts[:-1])
        enum = self.restore_type(type_name)
        return enum[parts[-1]]

    def unpack_type(self, data):
        _, type_name = data
        return self.restore_type(type_name)

    def unpack_encoded(self, data):
        _, codec, bytes = data
        if codec not in ALLOWED_CODECS:
            raise ValueError("Unsupported codec: %r" % codec)
        return bytes.encode(codec)

    def unpack_bytes(self, data):
        _, bytes = data
        return bytes.decode(BYTES_ENCODING)

    def unpack_tuple(self, data):
        return tuple([self.unpack_data(d) for d in data[1:]])

    def unpack_list(self, container, data):
        container.extend([self.unpack_data(d) for d in data])

    def unpack_set(self, container, data):
        container.update(self.unpack_unordered_values(data[1:]))

    def unpack_dict(self, container, data):
        if PY3:
            items = data.items()
        else:
            items = [(k.encode(DEFAULT_ENCODING), v)for k, v in data.items()]
        container.update(self.unpack_unordered_pairs(items))

    def unpack_function(self, data):
        return reflect.named_object(data[1])

    _list_unpackers = {BYTES_ATOM: (None, unpack_bytes),
                       ENCODED_ATOM: (None, unpack_encoded),
                       ENUM_ATOM: (None, unpack_enum),
                       TYPE_ATOM: (None, unpack_type),
                       TUPLE_ATOM: (None, unpack_tuple),
                       SET_ATOM: (set, unpack_set),
                       EXTERNAL_ATOM: (None, unpack_external),
                       REFERENCE_ATOM: (None, unpack_reference),
                       DEREFERENCE_ATOM: (None, unpack_dereference),
                       FUNCTION_ATOM: (None, unpack_function)}


class Transform(SONManipulator):

    def __init__(self, registry=None):
        self._tls = threading.local()
        self._registry = registry

    def transform_incoming(self, son, collection):
        return self._get_serializer().convert(son)

    def transform_outgoing(self, son, collection):
        return self._get_unserializer().convert(son)

    def _get_serializer(self):
        if not hasattr(self._tls, 'serializer'):
            self._tls.serializer = Serializer()
        return self._tls.serializer

    def _get_unserializer(self):
        if not hasattr(self._tls, 'unserializer'):
            self._tls.unserializer = Unserializer(registry=self._registry)
        return self._tls.unserializer
