import copy
from datetime import date, timedelta
from pathlib import Path

import pytest
import pytz
from prepare_test_data import load_seeds_for_participant_testing

from app import status, utils


class SharedData:
    def __init__(self):
        self.num_coupons = 3
        consent_file = "test-data/sig"
        path = Path(__file__).parent.parent.absolute()
        today = date.today().strftime("%Y-%m-%d")
        self.prev = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        time = utils.current_time().time().strftime("%H:%M")
        consent_sig = open(path / consent_file, "rb").read().decode("utf-8")
        self.consent_1 = {
            "RECORD_ID": 1,
            "CF_VERSION": "1",
            "CF_UPLOAD_DATE": "Wed, 10 Nov 2021 00:56:37 GMT",
            "CONSENTED": "Y",
            "initials": "jd",
            "firstName": "John",
            "lastName": "Doe",
            "email": "undefined",
            "homePhone": "undefined",
            "mobile": "919-555-1212",
            "allow": "y",
            "confirm": "y",
            "date": today,
            "sign": consent_sig,
            "dateSign": today,
            "timeSign": time,
            "contact": "",
            "reasons": "",
            "others": "",
        }
        self.survey_1 = {
            "RECORD_ID": 1,
            "preferred_communication": "Phone call",
            "age": 54,
            "gender": "Male",
            "ethnic": "Black or African American",
            "language": "English",
            "employment": "Currently employed full-time by self or other",
            "insurance": "Yes",
            "education": "4-year college",
            "dwell": "Standalone house",
            "zip": "27713",
            "marital_status": "Married or live-in partner",
            "completed": True,
        }


@pytest.fixture
def p_env():
    return SharedData()


class TestParticipants:
    def test_redeem_consent_survey(self, client, p_env, request):
        # load test data, created 2 participants
        test_data = load_seeds_for_participant_testing()
        update = {"MRN": test_data[0]["MRN"], "STATUS": "INCLUDE"}
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK
        update["MRN"] = test_data[1]["MRN"]
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK

        # Test redeem
        response = client.get("/api/cohort")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        coupon = records[0].get("COUPON")
        response = client.get(f"/api/redeem?coupon={coupon}")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert records.get("RECORD_ID") == 1
        assert test_data[0]["EMAIL_ADDRESS"] == records.get("EMAIL_ADDRESS")

        data = {"RECORD_ID": "1"}
        response = client.post("/api/redeem", json=data)
        assert response.status_code == status.HTTP_200_OK

        data = {"RECORD_ID": "2"}
        response = client.post("/api/redeem", json=data)
        assert response.status_code == status.HTTP_200_OK

        response = client.post("/api/consent", data=p_env.consent_1)
        assert response.status_code == status.HTTP_200_OK

        data = copy.deepcopy(p_env.consent_1)
        data["RECORD_ID"] = 2
        data["initials"] = "as"
        data["firstName"] = "Alison"
        data["lastName"] = "Smith"
        data["mobile"] = "919-111-2222"
        data["date"] = p_env.prev
        response = client.post("/api/consent", data=data)
        assert response.status_code == status.HTTP_200_OK

        # Test survey
        response = client.post("/api/survey", json=p_env.survey_1)
        assert response.status_code == status.HTTP_200_OK
        survey = copy.deepcopy(p_env.survey_1)
        survey["preferred_communication"] = "Email"
        survey["age"] = 32
        survey["gender"] = "Femal"
        survey["ethnic"] = "Hispanic Other"
        survey["language"] = "Spanish"
        survey["RECORD_ID"] = 2
        response = client.post("/api/survey", json=survey)
        assert response.status_code == status.HTTP_200_OK

        today = date.today().strftime("%a, %d %b %Y")
        response = client.get("/api/cohort")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert today in records[0].get("COUPON_REDEEM_DATE")
        assert today in records[0].get("CONSENT_DATE")
        assert today in records[0].get("SURVEY_COMPLETION_DATE")
        assert today in records[1].get("COUPON_REDEEM_DATE")
        assert today in records[1].get("CONSENT_DATE")
        assert today in records[1].get("SURVEY_COMPLETION_DATE")
        request.config.cache.set(
            "coupons", [records[0]["COUPON"], records[1]["COUPON"]]
        )

        # Test contacts
        contacts = {
            "contacts": [
                {
                    "FIRST_NAME": "Jane",
                    "LAST_NAME": "Doe",
                    "PAT_SEX": "Female",
                    "PAT_AGE": "50",
                    "CONTACT_ID": "001",
                },
                {
                    "FIRST_NAME": "Mike",
                    "LAST_NAME": "Doe",
                    "PAT_SEX": "Male",
                    "PAT_AGE": "19",
                    "CONTACT_ID": "002",
                },
            ],
            "RECORD_ID": 1,
            "ENROLLMENT_COMPLETED": "Y",
        }
        response = client.post("/api/participants", json=contacts)
        assert response.status_code == status.HTTP_200_OK

    def test_redeem_consent_survey_again(self, client, p_env, request):
        coupons = request.config.cache.get("coupons", None)
        # redeem again
        response = client.get(f"/api/redeem?coupon={coupons[0]}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert f"Coupon {coupons[0]} was redeemed already" == response.json.get(
            "reason"
        )
        # redeem should work for record id 2 as contacts were not provided
        response = client.get(f"/api/redeem?coupon={coupons[1]}")
        assert response.status_code == status.HTTP_200_OK

        # consent shortcut
        response = client.post("/api/consent", data=p_env.consent_1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Consent was already completed for record 1" == response.json.get(
            "reason"
        )

        # survey shortcut
        response = client.post("/api/survey", json=p_env.survey_1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Survey was already completed for record 1" == response.json.get(
            "reason"
        )

    def test_peer_coupon_page(self, client, p_env):
        # Test get
        response = client.get("/api/participants?contacts=y")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 2
        assert all(record["RECORD_ID"] == 1 for record in records)

        response = client.get("/api/participants?contacts=n")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert all(record["RECORD_ID"] == 2 for record in records)

        # Test setting alternative email
        alt_email = "snowball@duketest.com"
        update = {"RECORD_ID": "1", "ALTERNATIVE_EMAIL": alt_email}
        response = client.post("/api/participants", json=update)
        assert response.status_code == status.HTTP_200_OK
        response = client.get("/api/participants?contacts=y")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 2
        assert all(record["RECORD_ID"] == 1 for record in records)
        assert all(record["ALTERNATIVE_EMAIL"] == alt_email for record in records)

        # Test setting num_coupons
        # num_coupons = 3
        update = {"RECORD_ID": "2", "NUM_COUPONS": p_env.num_coupons}
        response = client.post("/api/participants", json=update)
        assert response.status_code == status.HTTP_200_OK
        response = client.get("/api/participants")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert records[0]["RECORD_ID"] == 2
        assert records[0]["NUM_COUPONS"] == 3

    def test_invite_peers(self, client, p_env):
        data = {"RECORD_ID": 1}
        response = client.post("/api/invitepeer", json=data)
        assert response.status_code == status.HTTP_200_OK
        assert b"Successfully sent 1 coupons" in response.data

        data = {"RECORD_ID": 2}
        response = client.post("/api/invitepeer", json=data)
        assert response.status_code == status.HTTP_200_OK
        assert f"Successfully sent {p_env.num_coupons} coupons" in response.json.get(
            "reason"
        )

        response = client.get("/api/participants?contacts=y")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 2
        assert all(record["RECORD_ID"] == 1 for record in records)
        assert all(record["COUPON_SENT"] == 1 for record in records)

        response = client.get("/api/participants")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert records[0]["RECORD_ID"] == 2
        assert records[0]["COUPON_SENT"] == p_env.num_coupons

    def test_schedule_test_for_peers(self, client, p_env):
        # First redeem/consent/complete survey for a peer
        data = {
            "RECORD_ID": 3,
            "FIRST_NAME": "Jane",
            "LAST_NAME": "Doe",
            "ZIP": "27713",
            "MOBILE_NUM": "9195551213",
            "EMAIL_ADDRESS": "jane.doe@duketest.com",
            "GUIDED": "no",
        }
        response = client.post("/api/redeem", json=data)
        assert response.status_code == status.HTTP_200_OK

        data = copy.deepcopy(p_env.consent_1)
        data["RECORD_ID"] = 3
        data["initials"] = "jd"
        data["firstName"] = "Jane"
        data["lastName"] = "Doe"
        data["email"] = "jane.doe@duketest.com"
        data["mobile"] = "919-555-1213"
        response = client.post("/api/consent", data=data)
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/api/testschedule")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert records[0]["EMAIL_ADDRESS"] == data["email"]

        update = {"RECORD_ID": 3, "TEST_DATE": date.today().strftime("%a, %d %b %Y")}
        response = client.post("/api/testschedule", json=update)
        assert response.status_code == status.HTTP_200_OK
        update["TEST_RESULT"] = "NEGATIVE"
        update["RESULT_DATE"] = utils.current_time() + timedelta(days=1)
        update["RESULT_NOTIFIED"] = "Yes"
        response = client.post("/api/testschedule", json=update)
        assert response.status_code == status.HTTP_200_OK
        response = client.get("/api/testschedule")
        records = response.json.get("records")
        assert len(records) == 1
        assert records[0]["TEST_RESULT"] == update["TEST_RESULT"]
        assert (
            update["RESULT_DATE"].astimezone(pytz.utc).strftime("%a, %d %b %Y %H:%M:%S")
            in records[0]["RESULT_DATE"]
        )
        assert records[0]["RESULT_NOTIFIED"] == update["RESULT_NOTIFIED"]
