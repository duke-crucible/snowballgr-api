import pandas as pd
from bson.json_util import dumps
from flask import current_app as app
from flask import make_response, request
from flask_restful import Resource
from pymongo import errors

from app import db_utils, status, utils
from app.services import logger


class UploadCSV(Resource):
    def post(self):
        try:
            df = pd.read_csv(request.files["csv"]).fillna(value="")
        except Exception as err:
            return utils.response_with_status_code(
                f"Failed to read csv file: {str(err)}"
            )

        count = 0
        rejected = 0
        error_list = []
        for index, row in df.iterrows():
            try:
                db_utils.insert_seed(_create_seed_report_row(row))
                count += 1
            except errors.DuplicateKeyError as dup_error:
                error_msg = "Duplicate MRN"
                logger.error(f"{error_msg} from row {index+1}: {str(dup_error)}")
                rejected += 1
                error_list.append({"row": index + 1, "errorMsg": error_msg})
            except Exception as e:
                logger.error(f"Failed to save row {index+1}: {str(e)}")
                rejected += 1
                error_list.append({"row": index + 1, "errorMsg": str(e)})

        logger.info(f"Saved {count} seed records")
        if count == 0:
            # if no row succeeded, consider upload failed
            errorMsg = error_list[0].get("errorMsg")
            logger.error(f"Failed to upload seed report CSV: {errorMsg}")
            return utils.response_with_status_code(errorMsg)
        else:
            dict = {
                "totalLines": len(df) + 1,
                "columnsFound": len(df.columns),
                "totalDataLinesInserted": count,
                "rejectedLines": rejected,
                "errors": error_list,
            }
            return utils.response_with_status_code(
                f"Saved {count} seeds into db",
                status.HTTP_200_OK,
                dict,
            )


def _create_seed_report_row(csv_row):
    # mandotory columns cannot be empty
    preferred = app.config["PREFERRED_COMM"]
    if preferred not in csv_row:
        csv_row[preferred] = "Email"

    return {
        **{
            key: value
            for key, value in csv_row.items()
        },
        "REPORT_DATE": utils.current_time(),
        "STATUS": _get_status(csv_row),
    }


def _get_status(csv_row):
    if "STATUS" in csv_row:
        return csv_row["STATUS"]

    excluded_email_addresses = {
        "none@email.com",
        "none@emailc.om",
        "none@emil.aom",
        "none@gmail.com",
    }
    should_be_excluded = (
        not csv_row["EMAIL_ADDRESS"]
        or csv_row["EMAIL_ADDRESS"] in excluded_email_addresses
    )
    return "EXCLUDE" if should_be_excluded else "ELIGIBLE"


class UpdateSeeds(Resource):
    def post(self):
        request_data = request.get_json()
        ret = _sanity_check(request_data)
        if ret:
            return ret

        mrn = request_data.get("MRN")
        updates = {}
        updated_logs = ""
        if app.config["MOBILE_NUM"] in request_data:
            updated_mobile = request_data.get(app.config["MOBILE_NUM"])
            logger.info("updated mobile is:" + updated_mobile)
            updates.update({"MOBILE_NUM": updated_mobile})
            updated_logs += f"changed mobile to: {updated_mobile}"
        if app.config["EMAIL_ADDRESS"] in request_data:
            updated_email = request_data.get(app.config["EMAIL_ADDRESS"])
            logger.info("updated email is:" + updated_email)
            updates.update({"EMAIL_ADDRESS": updated_email})
            if updated_logs:
                updated_logs += "; "
            updated_logs += "email address to: " + updated_email
        if app.config["TEST_RESULT"] in request_data:
            myc_viewed = request_data.get(app.config["TEST_RESULT"])
            logger.info("updated test_result is:" + myc_viewed)
            updates.update({"TEST_RESULT": myc_viewed})
            if updated_logs:
                updated_logs += "; "
            updated_logs += "TEST_RESULT to: " + myc_viewed
        try:
            if updates:
                updated_logs += " at:" + str(utils.current_time())
                updates.update({"LOGS": updated_logs})
                logger.info(f"Update seed MRN {mrn} with {updates}")
                db_utils.update_seed_report(mrn, updates)
                resp_msg = mrn + ": information successfully updated."
            else:
                resp_msg = f"Nothing updated for MRN {mrn}"

            return utils.response_with_status_code(resp_msg, status.HTTP_200_OK)

        except Exception as err:
            return utils.response_with_status_code(
                "Failed to update information for MRN: " + str(err) + mrn
            )


class AddNewSeed(Resource):
    def get(self):
        logger.error("Should never come here")

    def post(self):
        request_data = request.get_json()
        if request_data and "PAT_AGE" in request_data and request_data["PAT_AGE"] != "":
            request_data["PAT_AGE"] = int(request_data["PAT_AGE"])
        result = _sanity_check(request_data, add=True)
        if result:
            return result

        try:
            db_utils.insert_seed(request_data)
            return utils.response_with_status_code(
                "Successfully inserted a new seed", status.HTTP_200_OK
            )

        except errors.DuplicateKeyError as dup_error:
            error_msg = "Duplicate MRN"
            logger.error(f"{error_msg}: {str(dup_error)}")

        except Exception as err:
            error_msg = f"Failed to insert new seed: {str(err)}"
            logger.error(error_msg)

        if error_msg:
            return utils.response_with_status_code(error_msg)


def _sanity_check(request_data, add=False):
    if not request_data:
        resp = make_response()
        resp.status_code = status.HTTP_200_OK
        return resp

    if "MRN" not in request_data:
        return utils.response_with_status_code("MRN is missing")
    else:
        if add:
            # Combine first and last names
            request_data[app.config["PAT_NAME"]] = (
                request_data["LAST_NAME"] + "," + request_data["FIRST_NAME"]
            )
            del request_data["FIRST_NAME"]
            del request_data["LAST_NAME"]
            # Add preferred communication method
            preferred = app.config["PREFERRED_COMM"]
            if preferred not in request_data:
                request_data[preferred] = "Email"
            # Add report date
            request_data["REPORT_DATE"] = utils.current_time()
        return None


class SeedReport(Resource):
    def get(self):
        try:
            q = {
                app.config["RESULT_DATE"]: utils.parse_date_range(
                    request.args.get("date_range", app.config["TTLD_TEST_RESULT"])
                )
            }
            req_status = request.args.get("status")
            if req_status:
                q.update({"$or": [{"STATUS": req_status.upper()}]})
            else:
                q.update(
                    {
                        "$or": [
                            {"STATUS": "ELIGIBLE"},
                            {"STATUS": "DEFER"},
                            {"STATUS": "EXCLUDE"},
                        ]
                    }
                )

            if request.args.get("age"):
                q.update(
                    {
                        app.config["PAT_AGE"]: utils.parse_age_group(
                            request.args.get("age")
                        )
                    }
                )

            if request.args.get("ethnic"):
                q.update({app.config["ETHNIC_GROUP"]: request.args.get("ethnic")})

            if request.args.get("race"):
                q.update({"RACE": request.args.get("race")})

            if request.args.get("sex"):
                q.update({app.config["PAT_SEX"]: request.args.get("sex")})

            records = db_utils.get_seeds(
                q, app.config["SEED_REPORT_FIELDS"], app.config["REPORT_DATE"]
            )
            if records:
                data = list(records)
                logger.info(f"Found {len(data)} records for seed report!")
            return utils.response_with_status_code("success", status.HTTP_200_OK, data)
        except Exception as err:
            error_msg = "Error when retrieving daily seed report: " + str(err)
            return utils.response_with_status_code(error_msg)
