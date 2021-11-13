from prepare_test_data import load_seeds_for_participant_testing

from app import status


class TestCRM:
    def test_cohort_filters(self, client):
        # load test data, created 2 participants
        test_data = load_seeds_for_participant_testing()
        update = {"MRN": test_data[0]["MRN"], "STATUS": "INCLUDE"}
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK
        update["MRN"] = test_data[1]["MRN"]
        response = client.post("/api/seedstatus", json=update)
        assert response.status_code == status.HTTP_200_OK

        # Test no filters
        response = client.get("/api/cohort")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 2
        assert any(record["MRN"] == test_data[0]["MRN"] for record in records)
        assert any(record["MRN"] == test_data[1]["MRN"] for record in records)

        # Test filter days
        response = client.get("/api/cohort?date_range=5")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert test_data[0]["MRN"] == records[0]["MRN"]

        # Test filter age
        response = client.get("/api/cohort?age=21-40")
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert test_data[1]["MRN"] == records[0]["MRN"]

        # Test combination of filters
        race = test_data[0]["RACE"]
        sex = test_data[0]["PAT_SEX"]
        ethnic = test_data[0]["ETHNIC_GROUP"]
        response = client.get(
            f"/api/cohort?date_range=3&age=41-60&race={race}&sex={sex}&ethnic={ethnic}"
        )
        assert response.status_code == status.HTTP_200_OK
        records = response.json.get("records")
        assert len(records) == 1
        assert test_data[0]["MRN"] == records[0]["MRN"]

    def test_download_report(self, client):
        response = client.get("/api/download?type=participants")
        assert response.status_code == status.HTTP_200_OK
        assert b"TEST2582" in response.data
        assert b"TEST2657" in response.data

    def test_crm_report(self, client):
        # Test get CRM
        response = client.get("/api/crm?record_id=1")
        assert response.status_code == status.HTTP_200_OK
        assert b"Successfully sent coupon" in response.data

        # Test creating a new comment
        comment = "A test comment by integration test"
        update = {"RECORD_ID": "1", "comment": comment}
        response = client.post("/api/crm", json=update)
        assert response.status_code == status.HTTP_200_OK

        # Verify post above
        response = client.get("/api/crm?record_id=1")
        assert response.status_code == status.HTTP_200_OK
        comments = response.json.get("records").get("comments")
        assert comment == comments[0].get("comment")
