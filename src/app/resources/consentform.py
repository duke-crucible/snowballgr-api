from base64 import b64encode

from flask import make_response, request
from flask_restful import Resource

from app import db_utils, status, utils
from app.services import logger


class ConsentForm(Resource):
    def post(self):
        if "comments" in request.form:
            comments = request.form.get("comments")
        else:
            comments = "N/A"
            logger.error("No comments provided")
        file = request.files["form"]
        try:
            version = db_utils.save_new_consent_form(file, comments, "N/A")
            return utils.response_with_status_code(
                f"Successfully saved new version ({version}) of consent form into db",
                status.HTTP_200_OK,
            )
        except Exception as err:
            return utils.response_with_status_code(
                f"Failed to save new version of consent form into db: {str(err)}"
            )

    def get(self):
        try:
            version = request.args.get("version", -1)
            consent = db_utils.get_version_consent_form(version)
            logger.info(f"comments: {consent.comments}, modifier: {consent.modifier}")
            dict = {
                "version": consent.version,
                "uploadDate": consent.uploadDate,
                "form": b64encode(consent.read()).decode("utf-8"),
            }
            logger.debug(
                "Successfully retrieved version "
                + str(dict["version"])
                + " consent form uploaded on "
                + str(dict["uploadDate"])
            )
            response = make_response(dict)
            response.status_code = status.HTTP_200_OK
            return response
        except Exception as err:
            logger.error(err)
            error_msg = f"Failed to retrieve latest consent document: {str(err)}"
            logger.error(error_msg)
            return utils.response_with_status_code(error_msg)


class ConsentFormHistory(Resource):
    def get(self):
        try:
            cf_list = list(db_utils.get_consent_form_history())
            logger.info(f"Found {len(cf_list)} versions of consent form")
            return utils.response_with_status_code(
                "success", status.HTTP_200_OK, cf_list
            )
        except Exception as err:
            logger.error(err)
            return utils.response_with_status_code(str(err))
