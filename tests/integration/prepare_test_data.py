import json
from pathlib import Path

from app import db_utils, utils
from app.services import logger


def load_test_data():
    # logger.debug("Remove any seeds if exist...")
    # logger.debug(f"Removed {remove_test_seeds()} seeds from test db")
    # query = {"MRN": {"$regex": "^TEST"}}
    # return (col.delete_many(query)).deleted_count
    logger.debug(f"Remove test db: {db_utils.remove_db('test')}")
    _load_consent_form()


def _load_consent_form():
    file = "test-data/Consent.pdf"
    path = Path(__file__).parent.parent.absolute()
    # upload initial version
    comments = "initial version"
    return db_utils.save_new_consent_form(open(path / file, "rb"), comments, "Test")


def load_seeds_for_participant_testing():
    # remove all existing seeds and participants
    db_utils.remove_collection("seeds")
    db_utils.remove_collection("participants")
    # db_utils.remove_all_collections()
    file = "test-data/seeds.json"
    return _import_data_from_json(file, "seeds")


def _import_data_from_json(file, coll):
    path = Path(__file__).parent.parent.absolute()
    with open(path / file) as f:
        count = 0
        data = json.load(f)
        if coll == "seeds":
            for seed in data:
                # manipulate test result date for testing
                if count == 0:
                    seed["RESULT_DATE"] = utils.current_time().strftime(
                        "%m-%d-%Y %H:%M"
                    )
                seed["REPORT_DATE"] = utils.current_time()
                logger.debug(seed)
                db_utils.insert_seed(seed)
                count += 1
            logger.debug(f"Inserted {count} seeds")
        return data
