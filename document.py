from feat.common import formatable, adapters


field = formatable.field


class Document(formatable.Formatable):

    field('_id', None, '_id')
