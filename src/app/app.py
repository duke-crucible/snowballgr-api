from flask import Flask
from flask_cors import CORS

from app.config import CONFIGURATIONS
from app.db_utils import create_indexes
from app.resources.admin import Download, DownloadFileFromURL, HealthCheck
from app.resources.consentform import ConsentForm, ConsentFormHistory
from app.resources.invite import InvitePeer, SeedStatus
from app.resources.participant import (
    CohortReport,
    Consent,
    CrmReport,
    Participants,
    RedeemCoupon,
    Survey,
    TestSchedule,
)
from app.resources.seed import AddNewSeed, SeedReport, UpdateSeeds, UploadCSV
from app.services import api, logger, mongo


def register_endpoints(app):
    logger.info("Registering endpoints")
    api.app = app

    # Endpoints/routes need to be all lowercase to make Flask happy.
    api.add_resource(HealthCheck, "/healthcheck")
    api.add_resource(SeedReport, "/seedreport")
    api.add_resource(SeedStatus, "/seedstatus")
    api.add_resource(InvitePeer, "/invitepeer")
    api.add_resource(UploadCSV, "/uploadcsv")
    api.add_resource(UpdateSeeds, "/updateseed")
    api.add_resource(AddNewSeed, "/addseed")
    api.add_resource(ConsentForm, "/consentform")
    api.add_resource(RedeemCoupon, "/redeem")
    api.add_resource(CohortReport, "/cohort")
    api.add_resource(CrmReport, "/crm")
    api.add_resource(Survey, "/survey")
    api.add_resource(Consent, "/consent")
    api.add_resource(Participants, "/participants")
    api.add_resource(Download, "/download")
    api.add_resource(TestSchedule, "/testschedule")
    api.add_resource(DownloadFileFromURL, "/downloadfile")
    api.add_resource(ConsentFormHistory, "/consentformhistory")


def register_services(app, *services):
    # flask services all have the same syntax
    for service in services:
        service.init_app(app)


def create_app(app_env, testing=False):
    if testing is True:
        logger.info("Creating app for testing...")
        app_env = "test"
    # Cannot use get_config in utils as Api is not bound with app yet
    config = CONFIGURATIONS[app_env]

    app = Flask(__name__)
    app.config.from_object(config)
    app.secret_key = config.SESSION_KEY  # enables flask session
    app.testing = testing  # true for pytest-flask testing env

    # Enable CORS.
    CORS(app)

    # Attach the api routes.
    register_endpoints(app)

    # Register the app services
    register_services(app, api, mongo)
    if app_env != "local" and app_env != "test":
        with app.app_context():
            # create indexes in mongo
            create_indexes()

    logger.info(f"Configuring app with: {config.__name__}.")

    return app
