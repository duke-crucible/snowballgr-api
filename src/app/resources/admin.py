import pandas as pd
from flask import request
from flask_restful import Resource

from app import db_utils, utils
from app.db_utils import mongodb_check
from app.services import api, logger


class HealthCheck(Resource):
    def get(self):
        health_dict = {"app env": api.app.config["APP_ENV"], "mongodb": mongodb_check()}
        logger.info("healthcheck: %r", health_dict)
        try:
            logger.info(f"db name: {api.app.config['MONGODB_NAME']}")
            logger.info(db_utils.list_collections())
        except Exception as e:
            logger.error(f"Exception caught: {str(e)}")
        return health_dict


class Download(Resource):
    def get(self):
        # seeds/participants/consent/survey
        collection = request.args.get("type", None)
        logger.info(f"download request for {collection}")
        try:
            cursor = db_utils.download_report(collection)
            rl = list(cursor)
            df = pd.DataFrame(rl)
            logger.debug(df)
            csv = df.to_csv(index=False, sep=",")
            return csv
        except Exception as err:
            logger.error(str(err))
            return utils.response_with_status_code(f"Exception caught: {str(err)}")


class DownloadFileFromURL(Resource):
    def get(self):
        url = request.args.get("url", None)
        if url is None:
            return utils.response_with_status_code(
                "URL missing in downloadfile request"
            )
        logger.info(f"download file from {url}")
        df = pd.read_csv(url, index_col=0, parse_dates=[0])
        logger.debug(df)
        return df.to_csv(sep=",")
