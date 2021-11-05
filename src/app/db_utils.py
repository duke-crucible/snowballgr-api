import dateutil.parser
from flask import current_app as app
from gridfs import GridFS
from pymongo import ASCENDING, DESCENDING, errors

from app import utils
from app.services import logger, mongo


def create_indexes():
    db = get_db_handle()
    # Cosmos db is different from mongodb, compound indexes is only needed if
    # query needs to sort on multiple fields at once, our case only need single
    # field indexes
    for coll, indexes in app.config["COLLECTION_INDEXES"].items():
        for index in indexes:
            db[coll].create_index(index)
        logger.info(db[coll].index_information())


def mongodb_check():
    logger.info("Checking database connection...")
    result = "status: "
    try:
        logger.info(mongo.cx.server_info())
        result += "Database connection is successful."
    except errors.ServerSelectionTimeoutError as err:
        logger.error(str(err))
        result += "Failed to connect to database " + str(err)
    return result


def get_db_handle(db_name=None):
    if db_name is None:
        db_name = app.config["MONGODB_NAME"]
    return mongo.cx[db_name]


def remove_db(db_name=None):
    if db_name is None:
        db_name = app.config["MONGODB_NAME"]
    mc = mongo.cx
    mc.drop_database(db_name)


def remove_collection(collection, db_name=None):
    db = get_db_handle(db_name)
    coll_name = app.config["COLLECTIONS"].get(collection)
    coll = db[coll_name]
    return coll.drop()


def remove_all_collections(db_name=None):
    db = get_db_handle()
    for _name, coll in app.config["COLLECTIONS"].items():
        logger.info(f"Dropping collection {coll}")
        db[coll].drop()
    list_collections()


def list_collections(db_name=None):
    return get_db_handle(db_name).list_collection_names()


def _get_many(collection_name, query, fields, sort_field, sort_dir=DESCENDING):
    logger.debug(f"Query collection {collection_name} with {query} to get {fields}")
    db = get_db_handle()
    coll = db[collection_name]
    return coll.find(query, fields).sort(sort_field, sort_dir)


def _get_one(collection_name, query, fields):
    db = get_db_handle()
    coll = db[collection_name]
    return coll.find_one(query, fields)


def _insert_one(collection_name, doc):
    db = get_db_handle()
    coll = db[collection_name]
    doc[app.config["CREATED_AT"]] = utils.current_time()
    return coll.insert_one(doc)


def _update_one(collection_name, query, updates, insertIfNotExists=False):
    db = get_db_handle()
    coll = db[collection_name]
    return coll.update_one(query, updates, upsert=insertIfNotExists)


def _delete_one(collection_name, query):
    db = get_db_handle()
    coll = db[collection_name]
    return coll.delete_one(query)


def insert_doc(collection, doc):
    return _insert_one(app.config["COLLECTIONS"].get(collection), doc)


def upsert_doc(collection, query, doc):
    return _update_one(
        app.config["COLLECTIONS"].get(collection), query, {"$set": doc}, True
    )


def insert_seed(doc):
    # Set _id to MRN to ensure MRN is unique
    doc["_id"] = doc["MRN"]
    field = app.config["RESULT_DATE"]
    if field in doc:
        doc[field] = dateutil.parser.parse(doc[field])
    return _insert_one(app.config["COLLECTIONS"].get("seeds"), doc)


def update_seed_report(mrn, updates):
    mrn_query = {"MRN": mrn}
    updates[app.config["UPDATED_AT"]] = utils.current_time()
    _update_one(app.config["COLLECTIONS"].get("seeds"), mrn_query, {"$set": updates})


def update_seed_status(mrn, new_status, new_log):
    mrn_query = {"MRN": mrn}
    _update_one(
        app.config["COLLECTIONS"].get("seeds"),
        mrn_query,
        {
            "$set": {
                "STATUS": new_status,
                app.config["UPDATED_AT"]: utils.current_time(),
            },
            "$push": {app.config["STATUS_LOG"]: new_log},
        },
    )


def update_participant(record_id, updates):
    query = {"_id": utils.record_id_str(record_id)}
    updates[app.config["UPDATED_AT"]] = utils.current_time()
    return _update_one(
        app.config["COLLECTIONS"].get("participants"), query, {"$set": updates}
    )


def update_crm(record_id, data):
    query = {"_id": utils.record_id_str(record_id)}
    # no more crm collection, now saved into participants collection
    _update_one(
        app.config["COLLECTIONS"].get("participants"),
        query,
        {"$push": {"comments": {"$each": [data], "$position": 0}}},
    )


def delete_participant(_id):
    return _delete_one(app.config["COLLECTIONS"].get("participants"), {"_id": _id})


def save_new_consent_form(form, comments, modifier):
    fs = GridFS(get_db_handle(), app.config["COLLECTIONS"].get("consentform"))
    version = get_current_consent_version() + 1
    fs.put(
        form.read(),
        filename=app.config["CONSENT_FORM_FILENAME"],
        contentType="application/pdf",
        version=version,
        comments=comments,
        modifier=modifier,
        _id=version,
    )
    return version


def get_seed_report(mrn, fields=None):
    mrn_query = {"MRN": mrn}
    return _get_one(app.config["COLLECTIONS"].get("seeds"), mrn_query, fields)


def get_seeds(query, fields=None, sort_field=None):
    return _get_many(app.config["COLLECTIONS"].get("seeds"), query, fields, sort_field)


def get_participant(query_field, query_value, extract_fields=None):
    query = {query_field: query_value}
    return _get_one(
        app.config["COLLECTIONS"].get("participants"), query, extract_fields
    )


def get_participants(query, fields=None):
    return _get_many(
        app.config["COLLECTIONS"].get("participants"),
        query,
        fields,
        app.config["RECORD_ID"],
        ASCENDING,
    )


def get_comments(record_id, fields=None):
    query = {"_id": utils.record_id_str(record_id)}
    return _get_one(app.config["COLLECTIONS"].get("participants"), query, fields)


# General get method using record_id
def get_record(record_id, coll):
    query = {"_id": utils.record_id_str(record_id)}
    return _get_one(app.config["COLLECTIONS"].get(coll), query, {"_id": 0})


def get_num_of_docs(collection, sort_field):
    db = get_db_handle()
    coll = db[app.config["COLLECTIONS"].get(collection)]
    return coll.count_documents({sort_field: 1})


def get_latest(collection, sort_field, field=None):
    db = get_db_handle()
    coll = db[app.config["COLLECTIONS"].get(collection)]
    if field is not None:
        extract_data_field = {sort_field: 1, field: 1, "_id": 0}
    else:
        extract_data_field = {"_id": 0}
    temp = list(
        coll.find({}, extract_data_field).sort([(sort_field, DESCENDING)]).limit(1)
    )
    return temp[0] if len(temp) > 0 else None


def get_current_consent_version():
    db = get_db_handle()
    coll = db[app.config["COLLECTIONS"].get("consentform") + ".files"]
    return len(list(coll.find({"filename": app.config["CONSENT_FORM_FILENAME"]})))


def get_version_consent_form(version):
    fs = GridFS(get_db_handle(), app.config["COLLECTIONS"].get("consentform"))
    return fs.get_version(filename=app.config["CONSENT_FORM_FILENAME"], version=version)


def get_consent_form_history():
    db = get_db_handle()
    coll = db[app.config["COLLECTIONS"].get("consentform") + ".files"]
    return coll.find({}, app.config["CONSENT_FORM_METADATA_FIELDS"]).sort(
        "version", DESCENDING
    )


def download_report(coll):
    return _get_many(
        app.config["COLLECTIONS"].get(coll), {}, {"_id": 0}, app.config["CREATED_AT"]
    )
