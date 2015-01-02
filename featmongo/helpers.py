def find_with_applied_manipulators(collection, query, **kwargs):
    db = collection.database
    manip_query = db._apply_incoming_manipulators(query, collection)
    coursor = collection.find(manip_query, manipulate=True, **kwargs)
    return coursor


def find_one_with_applied_manipulators(collection, query, **kwargs):
    db = collection.database
    manip_query = db._apply_incoming_manipulators(query, collection)
    feat_object = collection.find_one(manip_query, manipulate=True, **kwargs)
    return feat_object


def update_with_applied_manipulators(collection, query, feat_obj, **kwargs):
    db = collection.database
    manip_query = db._apply_incoming_manipulators(query, collection)
    manip_object = db._apply_incoming_manipulators(feat_obj, collection)
    update_value = collection.update(manip_query, manip_object, manipulate=True, **kwargs)
    return update_value
