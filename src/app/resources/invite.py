import copy

from flask import current_app as app
from flask import make_response, request
from flask_restful import Resource

from app import db_utils, status, utils
from app.services import logger


class SeedStatus(Resource):
    def post(self):
        # first save the status
        update = request.get_json()
        logger.debug(f"update seed status: {update}")
        if not update:
            resp = make_response()
            resp.status_code = status.HTTP_200_OK
            return resp

        current_time = utils.current_time()
        mrn = update.get("MRN")
        new_status = update.get("STATUS")
        if not mrn or not new_status:
            return utils.response_with_status_code("Missing MRN or STATUS")
        if new_status not in app.config["SEED_STATUS_LIST"]:
            return utils.response_with_status_code(
                f"Failed to update STATUS: invalid status {new_status}"
            )

        try:
            # first update status in db
            revert_step = 0
            current = db_utils.get_seed_report(
                mrn, app.config["FIELDS_FROM_SEEDS_TO_PARTICIPANT"]
            )
            if new_status == current["STATUS"]:
                return utils.response_with_status_code(
                    "No action taken, status not changed", status.HTTP_200_OK
                )
            new_log = f"Changed STATUS to: {new_status} at {str(current_time)}"
            db_utils.update_seed_status(mrn, new_status, new_log)

            # send invitation only to "included" seeds
            resp = {"status_code": status.HTTP_200_OK, "msg": "success"}
            if new_status.upper() == "INCLUDE":
                revert_step = 1
                doc = _create_pdoc(current, "seed", current_time)
                comment = _send_coupon(doc)
                doc["comments"] = [
                    {
                        "time": current_time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "comment": comment,
                    }
                ]
                # create a participant, removed UPDATED_AT copied from seed
                db_utils.insert_doc("participants", doc)

        # except (ConnectionFailure, exceptions.BadRequestsError, exceptions.ForbiddenError) as e:
        except Exception as err:
            logger.error(f"SeedStatus Exception: {str(err)}")
            if revert_step > 0:
                # revert seed status and log
                db_utils.update_seed_status(
                    mrn,
                    current["STATUS"],
                    "Failed to invite seed, revert status",
                )
            resp = {
                "msg": "Exception occurred: " + str(err),
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            }

        return utils.response_with_status_code(resp["msg"], resp["status_code"])


def _get_new_record_id():
    record_id_dict = db_utils.get_latest("participants", "RECORD_ID", "RECORD_ID")
    return int(record_id_dict["RECORD_ID"]) + 1 if record_id_dict else 1


def _copy_seed_info_to_participant(seed):
    name = seed.get(app.config["PAT_NAME"])
    if "," not in name:
        logger.warn(
            f"First name does not exist for MRN {seed.get('MRN')}, last name is {name}"
        )
        # for now set first name to empty
        name += ","
    pat_name = name.split(",") if name else ["", ""]
    participant = copy.deepcopy(seed)
    participant["LAST_NAME"] = pat_name[0]
    participant["FIRST_NAME"] = pat_name[1]
    participant["STATUS"] = "INCLUDE"
    del participant["PAT_NAME"]
    if participant.get(app.config["STATUS_LOG"]):
        del participant[app.config["STATUS_LOG"]]
    return participant


def _copy_peer_info_to_participant(parent):
    return {
        app.config["PARENT_RECORD_ID"]: parent[app.config["RECORD_ID"]],
        app.config["REPORT_DATE"]: utils.current_time(),
    }


def _create_pdoc(from_data, ptype, timestamp):
    if ptype == "seed":
        doc = _copy_seed_info_to_participant(from_data)
    else:
        doc = _copy_peer_info_to_participant(from_data)
    doc[app.config["PARTICIPANT_TOKEN"]] = utils.generate_coupon()
    record_id = _get_new_record_id()
    doc[app.config["RECORD_ID"]] = record_id
    doc["_id"] = utils.record_id_str(record_id)
    doc["PTYPE"] = ptype
    doc[app.config["COUPON_ISSUE_DATE"]] = timestamp
    return doc


def _create_log(record_id, comment):
    log = {
        "_id": utils.record_id_str(record_id),
        app.config["RECORD_ID"]: record_id,
        "comments": [
            {
                "time": utils.current_time().strftime("%Y-%m-%dT%H:%M:%S"),
                "comment": comment,
            }
        ],
    }
    logger.debug(f"Creating first log for record {record_id}: {log}")
    return db_utils.insert_doc("crm", log)


class InvitePeer(Resource):
    def post(self):
        data = request.get_json()
        parent_record_id = data.get("RECORD_ID", None)
        if not parent_record_id:
            return utils.response_with_status_code("Missing record_id")

        logger.debug(f"Invite peers for record {parent_record_id}")
        error_msg = None
        try:
            parent = db_utils.get_participant(
                app.config["RECORD_ID"],
                parent_record_id,
                app.config["FIELDS_FOR_INVITE_PEER"],
            )
            if parent is None:
                error_msg = f"Failed to retrieve participant record {parent_record_id}"
                logger.error(error_msg)
                return utils.response_with_status_code(error_msg)

            num_coupons = int(parent.get(app.config["PEER_COUPON_NUM"], 1))
            current_time = utils.current_time()
            peers = parent.get(app.config["PEER_COUPONS_LIST"], [])
            num = 0
            coupons_sent = 0
            while num < num_coupons:
                doc = _create_pdoc(parent, "peer", current_time)
                record_id = doc[app.config["RECORD_ID"]]
                coupon = doc[app.config["PARTICIPANT_TOKEN"]]
                try:
                    # send coupon one by one
                    comment = _send_coupon(parent, to_peer=True, token=coupon)
                    doc["comments"] = [
                        {
                            "time": current_time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "comment": comment,
                        }
                    ]
                    # create a participant for peer
                    db_utils.insert_doc("participants", doc)
                    coupons_sent += 1
                    peers.append(
                        {
                            app.config["RECORD_ID"]: record_id,
                            app.config["PARTICIPANT_TOKEN"]: coupon,
                        }
                    )
                except Exception as e1:
                    logger.error(
                        f"Failed to send coupon {coupon} for record {record_id}: {str(e1)}"
                    )
                    error_msg = "Exception occurred: " + str(e1)

                num += 1

            # update parent participant
            updates = {
                app.config["PEER_COUPONS_LIST"]: peers,
                app.config["PEER_COUPONS_SENT"]: coupons_sent
                + parent.get(app.config["PEER_COUPONS_SENT"], 0),
            }
            db_utils.update_participant(parent_record_id, updates)
            logger.debug(
                f"Updated parent participant {parent_record_id} with {updates}"
            )

            if coupons_sent == num_coupons:
                resp = {
                    "msg": f"Successfully sent {coupons_sent} coupons",
                    "status_code": status.HTTP_200_OK,
                }
            elif coupons_sent == 0:
                resp = {
                    "msg": "Failed to send any coupons",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                }
            else:
                resp = {
                    "msg": f"Successfully sent {coupons_sent} coupons, {num_coupons-coupons_sent} failed",
                    "status_code": status.HTTP_200_OK,
                }

        except Exception as err:
            error_msg = (
                f"Exception updating participant peer-coupons: {str(err)}, {updates}"
            )
            logger.error(error_msg)
            resp = {
                "msg": error_msg,
                "status_code": status.HTTP_200_OK,
            }

        return utils.response_with_status_code(resp["msg"], resp["status_code"])


def _send_coupon(participant=None, to_peer=False, token=None):
    if to_peer and participant.get(app.config["ALTER_EMAIL"]):
        comm_type = "email"
        recipient = participant[app.config["ALTER_EMAIL"]]
    elif participant.get(app.config["EMAIL_ADDRESS"]):
        comm_type = "email"
        recipient = participant[app.config["EMAIL_ADDRESS"]]
    elif participant.get(app.config["MOBILE_NUM"]):
        comm_type = "mobile"
        recipient = participant[app.config["MOBILE_NUM"]]
    else:
        # should never come here
        error_msg = "Failed to send token: neither email nor cell number exists"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug("Invite recipient: " + recipient)

    if not token:
        token = participant[app.config["PARTICIPANT_TOKEN"]]
    if comm_type == "email":
        status_code = utils.send_email(
            recipient,
            token,
            app.config["SENDGRID_SEED_TEMPLATE"],
            participant.get("FIRST_NAME", "") + " " + participant.get("LAST_NAME", ""),
        )
    else:
        # send coupon invite by sms
        status_code = utils.send_sms_txt(recipient, token)

    if status_code != status.HTTP_202_ACCEPTED and status_code != status.HTTP_200_OK:
        msg = f"Failed to send coupon {token} to {recipient}: {str(status_code)}"
    else:
        msg = f"Successfully sent coupon {token} to {recipient}"
    logger.info(msg)
    return msg
