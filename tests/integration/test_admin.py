import os
from base64 import b64decode
from pathlib import Path

from app import db_utils, status
from app.services import api

# import pytest


class TestAdmin:
    def test_healthcheck(self, client):
        response = client.get("/api/healthcheck")
        expected = {
            "app env": api.app.config["APP_ENV"],
            "mongodb": "status: Database connection is successful.",
        }
        assert response.json == expected

    def test_consent_form(self, client):
        db_utils.remove_collection("consentform")
        # upload the consent form again
        file = "test-data/Consent.pdf"
        path = Path(__file__).parent.parent.absolute()
        newdata = {"comments": "test version 2", "form": open(path / file, "rb")}
        response = client.post("/api/consentform", data=newdata)
        assert response.status_code == status.HTTP_200_OK
        assert (
            b"Successfully saved new version (2) of consent form into db"
            in response.data
        )

        # next test get latest
        response = client.get("/api/consentform")
        path = Path(__file__).parent.parent.absolute()
        file = path / "test-data/consent_downloaded.pdf"
        if os.path.exists(file):
            os.remove(file)
        with open(file, "wb") as f:
            f.write(b64decode(response.json.get("form").encode("utf-8")))
        assert response.status_code == status.HTTP_200_OK
        assert response.json.get("version") == 2
        assert "uploadDate" in response.json

    def test_download_from_url(self, client):
        url = "https://raw.githubusercontent.com/duke-crucible/snowballgr-api/master/tests/test-data/seeds_10.csv"
        response = client.get(f"/api/downloadfile?url={url}")
        assert response.status_code == status.HTTP_200_OK
