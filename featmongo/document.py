from feat.common import formatable


field = formatable.field


class Document(formatable.Formatable):

    field('_id', None, '_id')
