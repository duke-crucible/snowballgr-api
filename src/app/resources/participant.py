import copy

from flask import current_app as app
from flask import request
from flask_restful import Resource

from app import db_utils, status, utils
from app.services import logger


class CohortReport(Resource):
    def get(self):
        q = {}
        if request.args.get("age"):
            q.update(
                {app.config["PAT_AGE"]: utils.parse_age_group(request.args.get("age"))}
            )
        if request.args.get("ethnic"):
            q.update({app.config["ETHNIC_GROUP"]: request.args.get("ethnic")})
        if request.args.get("sex"):
            q.update({app.config["PAT_SEX"]: request.args.get("sex")})
        if request.args.get("race"):
            q.update({"RACE": request.args.get("race")})
        if request.args.get("date_range"):
            q.update(
                {
                    app.config["RESULT_DATE"]: utils.parse_date_range(
                        request.args.get("date_range")
                    )
                }
            )
        return _process_get_participants(
            q, app.config["COHORT_REPORT_FIELDS"], cohort=True
        )


class CrmReport(Resource):
    def get(self):
        if request.args.get("record_id"):
            record_id = int(request.args.get("record_id"))
        else:
            error_msg = "Failed to retrieve logs: record id is missing"
            logger.error(error_msg)
            return utils.response_with_status_code(error_msg)
        try:
            comments = db_utils.get_comments(record_id, app.config["CRM_FIELD"])
            return utils.response_with_status_code(
                "success", status.HTTP_200_OK, comments
            )
        except Exception as err:
            error_msg = f"Error retrieving logs for record id {record_id}: {str(err)}"
            logger.error(error_msg)
            return utils.response_with_status_code(error_msg)

    def post(self):
        data = request.get_json()
        if not data or data.get("comment") is None:
            resp_msg = "No new log in request"
            logger.info(resp_msg)
            return utils.response_with_status_code(resp_msg, status.HTTP_200_OK)

        data["time"] = utils.current_time().strftime("%Y-%m-%dT%H:%M:%S")
        return _process_post_requests(data, participant_only=False, coll="crm")


class RedeemCoupon(Resource):
    def get(self):
        error_msg = None
        if request.args.get("coupon") is None:
            error_msg = "Coupon is missing"
        else:
            coupon = request.args.get("coupon")
            try:
                participant = db_utils.get_participant(
                    app.config["PARTICIPANT_TOKEN"],
                    coupon,
                    app.config["FIELDS_FOR_COUPON_REDEEM_PAGE"],
                )
                if participant is None:
                    error_msg = f"Failed to retrieve participant with coupon {coupon}"
                elif participant.get(app.config["ENROLLMENT_COMPLETED"]):
                    error_msg = f"Coupon {coupon} was redeemed already"
            except Exception as err:
                error_msg = (
                    f"Error retrieving participant with coupon {coupon}: " + str(err)
                )

        if error_msg is None:
            logger.debug(f"Retrieved participant: {participant}")
            return utils.response_with_status_code(
                "success", status.HTTP_200_OK, participant
            )
        else:
            logger.error(error_msg)
            return utils.response_with_status_code(error_msg)

    def post(self):
        data = request.get_json()
        return _process_post_requests(data, time_field=app.config["COUPON_REDEEM_DATE"])


class Consent(Resource):
    def get(self):
        # currently no page requires this information, prepare for future use
        return _get_record(
            request.args.get("record_id"), "consent", app.config["CONSENT_DATE"]
        )

    def post(self):
        data = request.form
        return _process_post_requests(
            dict(data),
            participant_only=False,
            coll="consent",
            time_field=app.config["CONSENT_DATE"],
        )


class Survey(Resource):
    def get(self):
        # currently no page requires this information, prepare for future use
        return _get_record(request.args.get("record_id"), "survey")

    def post(self):
        data = request.get_json()
        submit = data.get("completed", False) if data else False
        return _process_post_requests(
            data,
            participant_only=False,
            coll="survey",
            time_field=app.config["SURVEY_COMPLETION_DATE"] if submit else None,
        )


class TestSchedule(Resource):
    def get(self):
        q = {"PTYPE": "peer", app.config["COUPON_REDEEM_DATE"]: {"$exists": True}}
        if request.args.get("test_result"):
            q.update({app.config["TEST_RESULT"]: request.args.get("test_result")})
        if request.args.get("notified"):
            q.update({app.config["RESULT_NOTIFIED"]: request.args.get("notified")})
        if request.args.get("date_range"):
            q.update(
                {
                    app.config["REPORT_DATE"]: utils.parse_date_range(
                        request.args.get("date_range")
                    )
                }
            )
        return _process_get_participants(q, app.config["FIELDS_FOR_TEST_SCHEDULE_PAGE"])

    def post(self):
        data = request.get_json()
        return _process_post_requests(data)


class Participants(Resource):
    def get(self):
        # peer coupon distribution page
        contacts = request.args.get("contacts", None)
        q = {
            "contacts": {"$exists": True if contacts == "y" else False},
            app.config["SURVEY_COMPLETION_DATE"]: {"$exists": True},
        }
        return _process_get_participants(
            q, app.config["FIELDS_FOR_PEER_COUPON_PAGE"], contacts=contacts
        )

    def post(self):
        data = request.get_json()
        if data:
            if data.get("contacts"):
                # add contact(s) information
                peers = data["contacts"]
                contact_id = 1
                for peer in peers:
                    peer["CONTACT_ID"] = utils.contact_id_str(contact_id)
                    contact_id += 1
            elif data.get("ENROLLMENT_COMPLETED"):
                # no contact entered, check if enrollment is completed
                if data.get("ENROLLMENT_COMPLETED") == "Y":
                    data[app.config["ENROLLMENT_COMPLETED"]] = utils.current_time()
        return _process_post_requests(data)


def _process_post_requests(data, participant_only=True, coll=None, time_field=None):
    record_id = data.get(app.config["RECORD_ID"]) if data else None
    if not record_id:
        error_msg = "Record id is missing, cannot save data"
        logger.error(error_msg)
        return utils.response_with_status_code(error_msg)

    try:
        record_id = int(record_id)
        data["RECORD_ID"] = record_id
        if participant_only:
            # redeem and peers update
            coll = "participants"
            if time_field is not None:
                data[time_field] = utils.current_time()
            db_utils.update_participant(record_id, data)
        else:
            # save consent/survey/crm data
            if coll == "survey" or coll == "consent":
                # TODO: for now allow overwrites on survey and consent data
                data["_id"] = utils.record_id_str(record_id)
                db_utils.upsert_doc(coll, {"_id": data["_id"]}, data)
            elif coll == "crm":
                # No more crm collection, data saved in participants collection
                del data[app.config["RECORD_ID"]]
                db_utils.update_crm(record_id, data)
            else:
                # participant, use record_id as key to avoid duplicates
                data["_id"] = utils.record_id_str(record_id)
                db_utils.insert_doc(coll, data)
            if time_field is not None:
                # update participant
                db_utils.update_participant(
                    record_id, {time_field: utils.current_time()}
                )
        logger.info(f"Successfully updated {coll} data")
        return utils.response_with_status_code("success", status.HTTP_200_OK)
    except Exception as err:
        if "11000" in str(err):
            error_msg = (
                f"{coll.capitalize()} was already completed for record {record_id}"
            )
        else:
            error_msg = (
                f"Exception in saving {coll} data for record {record_id}: {str(err)}"
            )
        logger.error(error_msg)
        return utils.response_with_status_code(error_msg)


def _process_get_participants(query, fields_to_get, cohort=False, contacts=None):
    error_msg = None
    try:
        participants = db_utils.get_participants(query, fields_to_get)
        if participants is None:
            error_msg = f"Failed to retrieve participants with query {query}"
        else:
            participants = list(participants)
    except Exception as err:
        error_msg = f"Exception in retrieving participants with {query}: {str(err)}"

    if error_msg is None:
        if cohort:
            # cohort page requires full name
            for participant in participants:
                fn = participant.get("FIRST_NAME", "")
                ln = participant.get("LAST_NAME", "")
                participant[app.config["PAT_NAME"]] = ln + "," + fn
        elif contacts == "y":
            # peer coupon distribution page
            data = []
            for participant in participants:
                peers = participant["contacts"]
                dict = {k: participant[k] for k in participant if k != "contacts"}
                for peer in peers:
                    new_ele = copy.deepcopy(dict)
                    fn = peer.get("FIRST_NAME", "")
                    ln = peer.get("LAST_NAME", "")
                    new_ele["CONTACT"] = ln + "," + fn
                    data.append(new_ele)
            participants = data

        logger.debug(f"Found {len(participants)} participants")
        return utils.response_with_status_code(
            "success", status.HTTP_200_OK, participants
        )
    else:
        logger.error(error_msg)
        return utils.response_with_status_code(error_msg)


def _get_record(record_id, coll, verify_field=None):
    error_msg = None
    if record_id is None:
        error_msg = "Record id is missing"
    else:
        try:
            record = db_utils.get_record(record_id, coll)
            if record is None:
                error_msg = f"Failed to retrieve record {record_id}"
            elif verify_field and record.get(verify_field):
                error_msg = (
                    f" {coll.capitalize()} was already completed for record {record_id}"
                )
        except Exception as err:
            error_msg = f"Error retrieving record {record_id}: " + str(err)

    if error_msg is None:
        logger.debug(f"Retrieved record: {record}")
        return utils.response_with_status_code("success", status.HTTP_200_OK, record)
    else:
        logger.error(error_msg)
        return utils.response_with_status_code(error_msg)
