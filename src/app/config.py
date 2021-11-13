import os

from dotenv import load_dotenv


class DefaultConfig(object):
    DEBUG = True

    # Load .env for local development
    load_dotenv()

    APP_ENV = os.environ.get("SERVICE_APP_ENV", "local")
    SESSION_KEY = os.environ["SERVICE_SESSION_KEY"]
    BASE_URI = os.getenv("SERVICE_BASE_URI", "http://localhost:8000")
    # Mongo Settings
    MONGO_URI = os.environ["SERVICE_MONGODB_URI"]
    MONGODB_NAME = os.environ["SERVICE_DB_NAME"]
    MAX_SERVER_SEL_DELAY = 10000  # 10000ms as maximum server selection delay
    COLLECTIONS = {
        "seeds": "Seeds",
        "participants": "Participants",
        "consent": "Consent",
        "survey": "Surveys",
        "consentform": "ConsentForm",
    }

    # Lifetime of token (in days) for various states throughout the process
    TTLD_GENERATION_TO_CONSENT = os.getenv("TTLD_GENERATION_TO_CONSENT", "4")
    TTLD_TEST_RESULT = 99999

    REACT_APP_UI_ROOT = os.getenv("REACT_APP_UI_ROOT", "http://localhost:3000")
    # Email Settings
    SENDGRID_API_KEY = os.environ["SERVICE_SENDGRID_API_KEY"]
    SENDGRID_FROM_ADDRESS = os.environ["SERVICE_SENDGRID_FROM_ADDRESS"]
    SENDGRID_SEED_TEMPLATE = os.environ["SERVICE_SENDGRID_INVITE_TEMPLATE"]

    # SMS Settings
    SMS_PHONE_NUMBER = os.environ["SERVICE_COMMUNICATION_PHONE_NUMBER"]
    SMS_CONNECTION_STRING = os.environ["SERVICE_COMMUNICATION_CONNECTION_STRING"]

    # P for prod, D for dev
    ENV = ["P", "D"]

    # Field definitions to avoid typo
    PAT_NAME = "PAT_NAME"
    PAT_AGE = "PAT_AGE"
    PAT_SEX = "PAT_SEX"
    ETHNIC_GROUP = "ETHNIC_GROUP"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    ALTER_EMAIL = "ALTERNATIVE_EMAIL"
    MOBILE_NUM = "MOBILE_NUM"
    HOME_NUM = "HOME_NUM"
    PREFERRED_COMM = "PREFERRED_COMMUNICATION"
    PARTICIPANT_TOKEN = "COUPON"
    STATUS_LOG = "STATUS_CHANGE_LOG"
    RESULT_DATE = "RESULT_DATE"
    REPORT_DATE = "REPORT_DATE"
    TEST_RESULT = "TEST_RESULT"
    TEST_DATE = "TEST_DATE"
    RESULT_NOTIFIED = "RESULT_NOTIFIED"
    RECORD_ID = "RECORD_ID"
    COUPON_ISSUE_DATE = "COUPON_ISSUE_DATE"
    COUPON_REDEEM_DATE = "COUPON_REDEEM_DATE"
    CONSENT_DATE = "CONSENT_DATE"
    SURVEY_COMPLETION_DATE = "SURVEY_COMPLETION_DATE"
    ENROLLMENT_COMPLETED = "ENROLLMENT_COMPLETED_DATE"
    PEER_COUPON_NUM = "NUM_COUPONS"
    PARENT_RECORD_ID = "PARENT_RECORD_ID"
    PEER_COUPONS_SENT = "COUPON_SENT"
    PEER_COUPONS_LIST = "peer-coupons"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    CONSENT_FORM_FILENAME = "consent-form.pdf"

    SEED_STATUS_LIST = [
        "INCLUDE",
        "EXCLUDE",
        "DEFER",
        "ELIGIBLE",
    ]
    # Fields to index
    SEEDS_INDEXES = [
        REPORT_DATE,
        "MRN",
        "STATUS",
        PAT_NAME,
        PAT_AGE,
        PAT_SEX,
        ETHNIC_GROUP,
        "RACE",
        "ZIP",
        RESULT_DATE,
        CREATED_AT,
    ]
    PARTICIPANTS_INDEXES = [
        "MRN",
        "STATUS",
        PAT_NAME,
        PAT_AGE,
        PAT_SEX,
        ETHNIC_GROUP,
        "RACE",
        "ZIP",
        RECORD_ID,
        COUPON_ISSUE_DATE,
        COUPON_REDEEM_DATE,
        CONSENT_DATE,
        SURVEY_COMPLETION_DATE,
        CREATED_AT,
        TEST_DATE,
    ]
    CONSENT_FORM_INDEXES = [
        "version",
        "modifier",
        "uploadDate",
    ]
    CONSENT_INDEXES = {
        CREATED_AT,
    }
    SURVEY_INDEXES = {
        CREATED_AT,
    }
    COLLECTION_INDEXES = {
        "Seeds": SEEDS_INDEXES,
        "Participants": PARTICIPANTS_INDEXES,
        "ConsentForm.files": CONSENT_FORM_INDEXES,
        "Consent": CONSENT_INDEXES,
        "Surveys": SURVEY_INDEXES,
    }

    # Fields to extract from mongodb
    SEED_REPORT_FIELDS = {
        "STATUS": 1,
        "MRN": 1,
        EMAIL_ADDRESS: 1,
        MOBILE_NUM: 1,
        # "ZIP": 1,
        TEST_RESULT: 1,
        RESULT_DATE: 1,
        HOME_NUM: 1,
        PAT_AGE: 1,
        PAT_SEX: 1,
        "RACE": 1,
        ETHNIC_GROUP: 1,
        REPORT_DATE: 1,
        "_id": 0,
        "RECORD_ID": 1,
        "FIRST_NAME": 1,
        "LAST_NAME": 1,
        "ZIP": 1,
        MOBILE_NUM: 1,
        HOME_NUM: 1,
        EMAIL_ADDRESS: 1,
    }
    COHORT_REPORT_FIELDS = {
        "MRN": 1,
        PAT_NAME: 1,
        PAT_AGE: 1,
        PAT_SEX: 1,
        "RACE": 1,
        ETHNIC_GROUP: 1,
        EMAIL_ADDRESS: 1,
        MOBILE_NUM: 1,
        HOME_NUM: 1,
        PREFERRED_COMM: 1,
        "LANGUAGE": 1,
        "ZIP": 1,
        TEST_RESULT: 1,
        RESULT_DATE: 1,
        REPORT_DATE: 1,
        "STATUS": 1,
        RECORD_ID: 1,
        PARTICIPANT_TOKEN: 1,
        "FIRST_NAME": 1,
        "LAST_NAME": 1,
        COUPON_ISSUE_DATE: 1,
        COUPON_REDEEM_DATE: 1,
        CONSENT_DATE: 1,
        SURVEY_COMPLETION_DATE: 1,
        ENROLLMENT_COMPLETED: 1,
        "PTYPE": 1,
        PARENT_RECORD_ID: 1,
        PEER_COUPONS_LIST: 1,
        "_id": 0,
    }
    # important dates
    FIELDS_FOR_DATES_CHECK = {
        CONSENT_DATE: 1,
        SURVEY_COMPLETION_DATE: 1,
        ENROLLMENT_COMPLETED: 1,
    }
    # fields for coupon redeem page
    FIELDS_FOR_COUPON_REDEEM_PAGE = {
        "_id": 0,
        RECORD_ID: 1,
        "FIRST_NAME": 1,
        "LAST_NAME": 1,
        "ZIP": 1,
        MOBILE_NUM: 1,
        HOME_NUM: 1,
        EMAIL_ADDRESS: 1,
        "PTYPE": 1,
        SURVEY_COMPLETION_DATE: 1,
        ENROLLMENT_COMPLETED: 1,
    }
    # fields for peer coupon distribution page
    FIELDS_FOR_PEER_COUPON_PAGE = {
        "_id": 0,
        RECORD_ID: 1,
        "FIRST_NAME": 1,
        "LAST_NAME": 1,
        MOBILE_NUM: 1,
        ALTER_EMAIL: 1,
        EMAIL_ADDRESS: 1,
        PEER_COUPON_NUM: 1,
        PEER_COUPONS_SENT: 1,
        COUPON_ISSUE_DATE: 1,
        COUPON_REDEEM_DATE: 1,
        CONSENT_DATE: 1,
        SURVEY_COMPLETION_DATE: 1,
        "contacts": 1,
    }
    # fields for invite peer
    FIELDS_FOR_INVITE_PEER = {
        "_id": 0,
        RECORD_ID: 1,
        MOBILE_NUM: 1,
        ALTER_EMAIL: 1,
        EMAIL_ADDRESS: 1,
        PEER_COUPON_NUM: 1,
        PEER_COUPONS_LIST: 1,
        PEER_COUPONS_SENT: 1,
    }
    #  fields for test schedule page
    FIELDS_FOR_TEST_SCHEDULE_PAGE = {
        "_id": 0,
        RECORD_ID: 1,
        "FIRST_NAME": 1,
        "LAST_NAME": 1,
        EMAIL_ADDRESS: 1,
        MOBILE_NUM: 1,
        HOME_NUM: 1,
        "ZIP": 1,
        PAT_AGE: 1,
        "PTYPE": 1,
        PARTICIPANT_TOKEN: 1,
        TEST_RESULT: 1,
        TEST_DATE: 1,
        RESULT_DATE: 1,
        RESULT_NOTIFIED: 1,
    }
    # fields to be copied from seeds to participants
    FIELDS_FROM_SEEDS_TO_PARTICIPANT = {
        "MRN": 1,
        PAT_NAME: 1,
        PAT_AGE: 1,
        PAT_SEX: 1,
        "RACE": 1,
        ETHNIC_GROUP: 1,
        EMAIL_ADDRESS: 1,
        MOBILE_NUM: 1,
        HOME_NUM: 1,
        PREFERRED_COMM: 1,
        "LANGUAGE": 1,
        "ZIP": 1,
        TEST_RESULT: 1,
        RESULT_DATE: 1,
        REPORT_DATE: 1,
        "STATUS": 1,
        STATUS_LOG: 1,
        "_id": 0,
    }
    CRM_FIELD = {
        "comments": 1,
        "_id": 0,
    }
    CONSENT_FORM_METADATA_FIELDS = {
        "_id": 0,
        "version": 1,
        "comments": 1,
        "modifier": 1,
    }

    # unauthorized response:
    UNAUTHORIZED_MESSAGE = 'Error 403: You do not have permission to access this information. If you believe you have \
    received this notification in error, please contact the \
    < a href = "https://app.smartsheet.com/b/form/a0871a8eb325405fae818df814018099" \
    target="_blank">system administrator</a>'


class LocalConfig(DefaultConfig):
    pass


class DevelopConfig(DefaultConfig):
    # Add dev specific config here
    pass


class TestConfig(DefaultConfig):
    MONGODB_NAME = "test"


class ProdConfig(DefaultConfig):
    DEBUG = False


CONFIGURATIONS = {
    "local": LocalConfig,
    "dev": DevelopConfig,
    "test": TestConfig,
    "prod": ProdConfig,
}
