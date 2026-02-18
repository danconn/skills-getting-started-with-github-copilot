"""
Tests for the Mergington High School Activities API
"""
import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_has_soccer_team(self, client):
        """Test that Soccer Team activity exists"""
        response = client.get("/activities")
        activities = response.json()
        assert "Soccer Team" in activities


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant to an activity"""
        response = client.post(
            "/activities/Soccer%20Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up newstudent@mergington.edu for Soccer Team"

    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Soccer%20Team/signup?email={email}")

        # Verify participant was added
        response = client.get("/activities")
        soccer_team = response.json()["Soccer Team"]
        assert email in soccer_team["participants"]

    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up the same email twice fails"""
        email = "alex@mergington.edu"  # Already registered for Soccer Team

        response = client.post(f"/activities/Soccer%20Team/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post("/activities/Fake%20Activity/signup?email=test@mergington.edu")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "newstudent@mergington.edu"

        # Sign up for Soccer Team
        response1 = client.post(f"/activities/Soccer%20Team/signup?email={email}")
        assert response1.status_code == 200

        # Sign up for Basketball Club
        response2 = client.post(f"/activities/Basketball%20Club/signup?email={email}")
        assert response2.status_code == 200

        # Verify student is in both activities
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Soccer Team"]["participants"]
        assert email in activities["Basketball Club"]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        email = "alex@mergington.edu"  # Already registered for Soccer Team

        response = client.post(f"/activities/Soccer%20Team/unregister?email={email}")
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from Soccer Team"

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "alex@mergington.edu"

        client.post(f"/activities/Soccer%20Team/unregister?email={email}")

        # Verify participant was removed
        response = client.get("/activities")
        soccer_team = response.json()["Soccer Team"]
        assert email not in soccer_team["participants"]

    def test_unregister_nonexistent_participant_fails(self, client, reset_activities):
        """Test that unregistering a participant who isn't registered fails"""
        response = client.post(
            "/activities/Soccer%20Team/unregister?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity_fails(self, client, reset_activities):
        """Test that unregistering from a nonexistent activity fails"""
        response = client.post(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after unregistering"""
        email = "alex@mergington.edu"

        # Unregister
        response1 = client.post(f"/activities/Soccer%20Team/unregister?email={email}")
        assert response1.status_code == 200

        # Sign up again
        response2 = client.post(f"/activities/Soccer%20Team/signup?email={email}")
        assert response2.status_code == 200

        # Verify participant is back
        response = client.get("/activities")
        soccer_team = response.json()["Soccer Team"]
        assert email in soccer_team["participants"]


class TestIntegration:
    """Integration tests for multiple operations"""

    def test_full_signup_and_unregister_workflow(self, client, reset_activities):
        """Test a complete workflow of signup and unregister"""
        email = "workflow@mergington.edu"
        activity = "Drama%20Club"

        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Drama Club"]["participants"])

        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200

        # Verify count increased
        response = client.get("/activities")
        assert len(response.json()["Drama Club"]["participants"]) == initial_count + 1

        # Unregister
        response2 = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200

        # Verify count decreased
        response = client.get("/activities")
        assert len(response.json()["Drama Club"]["participants"]) == initial_count

    def test_multiple_students_signup_to_same_activity(self, client, reset_activities):
        """Test that multiple students can sign up to the same activity"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]

        for email in emails:
            response = client.post(f"/activities/Chess%20Club/signup?email={email}")
            assert response.status_code == 200

        # Verify all students are registered
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        for email in emails:
            assert email in chess_club["participants"]

    def test_activity_details_consistency(self, client):
        """Test that activity details remain consistent"""
        response = client.get("/activities")
        activities = response.json()

        # Check specific activity details
        soccer = activities["Soccer Team"]
        assert soccer["description"] == "Join the varsity soccer team and compete in regional tournaments"
        assert "Tuesdays and Thursdays" in soccer["schedule"]
        assert soccer["max_participants"] == 25
