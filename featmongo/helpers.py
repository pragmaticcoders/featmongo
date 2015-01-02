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
