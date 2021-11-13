import json
from pathlib import Path

from app import db_utils, status, utils

# from app.services import logger


class TestSeeds:
    def test_uploadcsv(self, client):
        # remove all existing seeds first
        db_utils.remove_collection("seeds")
        file = "test-data/seeds.csv"
        path = Path(__file__).parent.parent.absolute()
        data = {"csv": open(path / file, "rb")}
        response = client.post(
            "/api/uploadcsv", content_type="multipart/form-data", data=data
        )
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert records.get("totalLines") == 178
        assert records.get("columnsFound") == 32
        assert records.get("totalDataLinesInserted") == 177
        assert records.get("rejectedLines") == 0
        # Next test get seed report
        response = client.get("/api/seedreport")
        result = response.json.get("records")
        assert response.status_code == status.HTTP_200_OK
        assert len(result) == 177

    def test_addseed(self, client):
        # remove all existing seeds first
        db_utils.remove_collection("seeds")
        file = "test-data/addseed.json"
        path = Path(__file__).parent.parent.absolute()
        with open(path / file) as f:
            data = json.load(f)
            response = client.post("/api/addseed", json=data)
            assert response.status_code == status.HTTP_200_OK
            assert b"Successfully inserted a new seed" in response.data
        response = client.get("/api/seedreport")
        result = response.json.get("records")
        assert response.status_code == status.HTTP_200_OK
        assert len(result) == 1
        assert any(d["MRN"] == "TEST9189" for d in result)

    def test_update_seeds(self, client):
        # remove all existing seeds first
        db_utils.remove_collection("seeds")
        file = "test-data/seeds_10.csv"
        path = Path(__file__).parent.parent.absolute()
        data = {"csv": open(path / file, "rb")}
        response = client.post(
            "/api/uploadcsv", content_type="multipart/form-data", data=data
        )
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert records.get("totalLines") == 11
        assert records.get("columnsFound") == 32
        assert records.get("totalDataLinesInserted") == 10
        assert records.get("rejectedLines") == 0

        # Test update email
        update = {
            "MRN": "MRN0000008",
            "TEST_RESULT": "POSITIVE",
            "EMAIL_ADDRESS": "snowballgr@duketest.com",
        }
        response = client.post("/api/updateseed", json=update)
        # print(response.json.get("reason"))
        assert response.status_code == status.HTTP_200_OK
        assert "MRN0000008: information successfully updated." == response.json.get(
            "reason"
        )

        # Test update test reulst and mobile number
        update = {
            "MRN": "MRN0000007",
            "TEST_RESULT": "POSITIVE",
            "MOBILE_NUM": "919-555-1212",
        }
        response = client.post("/api/updateseed", json=update)
        assert response.status_code == status.HTTP_200_OK
        assert "MRN0000007: information successfully updated." == response.json.get(
            "reason"
        )

        # Test update seed name, expect no change
        update = {"MRN": "MRN0000009", "PAT_NAME": "John Smith"}
        response = client.post("/api/updateseed", json=update)
        assert response.status_code == status.HTTP_200_OK
        assert "Nothing updated for MRN MRN0000009" == response.json.get("reason")

        # Test defer
        update = {"MRN": "MRN0000009", "STATUS": "DEFER"}
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK
        assert "success" == response.json.get("reason")
        assert b"Invitation successfully sent to: " not in response.data

        # Test exclude
        update = {"MRN": "MRN0000010", "STATUS": "EXCLUDE"}
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK
        assert "success" == response.json.get("reason")
        assert b"Invitation successfully sent to: " not in response.data

        # Test invite with email
        update = {"MRN": "MRN0000008", "STATUS": "INCLUDE"}
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK
        assert b"Successfully sent coupon " in response.data
        assert b"snowballgr@duketest.com" in response.data

        # Test invite with sms
        update = {"MRN": "MRN0000007", "STATUS": "INCLUDE"}
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK
        assert b"Successfully sent coupon " in response.data
        assert b"919-555-1212" in response.data

    def test_seed_report_filters(self, client):
        # assume this case is run after above one, add a new seed
        file = "test-data/addseed.json"
        path = Path(__file__).parent.parent.absolute()
        with open(path / file) as f:
            data = json.load(f)
            data["RESULT_DATE"] = utils.current_time().strftime("%m-%d-%Y %H:%M")
            client.post("/api/addseed", json=data)

        # Test no filter
        response = client.get("/api/seedreport")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 9

        # Test filter days
        response = client.get("/api/seedreport?date_range=3")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert data["MRN"] == records[0]["MRN"]

        # Test filter status
        response = client.get("/api/seedreport?status=ELIGIBLE")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 7
        assert any(record["MRN"] == "TEST9189" for record in records)
        assert any(record["MRN"] == "MRN0000006" for record in records)
        assert any(record["MRN"] == "MRN0000005" for record in records)
        assert any(record["MRN"] == "MRN0000004" for record in records)
        assert any(record["MRN"] == "MRN0000003" for record in records)
        assert any(record["MRN"] == "MRN0000002" for record in records)
        assert any(record["MRN"] == "MRN0000001" for record in records)

        # Test filter age
        response = client.get("/api/seedreport?age=81-130")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 2
        assert any(record["MRN"] == "MRN0000006" for record in records)
        assert any(record["MRN"] == "MRN0000004" for record in records)

        # Test combination of filters
        response = client.get(
            "/api/seedreport?status=ELIGIBLE&age=21-40&race=Other&sex=Male&ethnic=Hispanic Mexican"
        )
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert any(record["MRN"] == "MRN0000003" for record in records)
