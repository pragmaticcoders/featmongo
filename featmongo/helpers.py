def find_with_applied_manipulators(collection, query):
    db = collection.database
    manip_query = db._apply_incoming_manipulators(query, collection)
    coursor = collection.find(manip_query, manipulate=True)
    return coursor
