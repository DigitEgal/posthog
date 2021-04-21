import random

from rest_framework import status

from posthog.api import organization
from posthog.demo import create_demo_team
from posthog.models import EventDefinition
from posthog.models.organization import Organization
from posthog.models.team import Team
from posthog.tasks.calculate_event_property_usage import calculate_event_property_usage_for_team
from posthog.test.base import APIBaseTest


class TestEventDefinitionAPI(APIBaseTest):

    EXPECTED_EVENT_DEFINITIONS = [
        {"name": "installed_app", "volume_30_day": 100, "query_usage_30_day": 0},
        {"name": "rated_app", "volume_30_day": 73, "query_usage_30_day": 0},
        {"name": "purchase", "volume_30_day": 16, "query_usage_30_day": 0},
        {"name": "entered_free_trial", "volume_30_day": 0, "query_usage_30_day": 0},
        {"name": "watched_movie", "volume_30_day": 87, "query_usage_30_day": 0},
    ]

    @classmethod
    def setUpTestData(cls):
        random.seed(900)
        super().setUpTestData()
        cls.demo_team = create_demo_team(cls.organization)
        calculate_event_property_usage_for_team(cls.demo_team.pk)
        cls.user.current_team = cls.demo_team
        cls.user.save()

    def test_list_event_definitions(self):

        response = self.client.get("/api/projects/@current/event_definitions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], len(self.EXPECTED_EVENT_DEFINITIONS))
        self.assertEqual(len(response.json()["results"]), len(self.EXPECTED_EVENT_DEFINITIONS))

        for item in self.EXPECTED_EVENT_DEFINITIONS:
            response_item = next((_i for _i in response.json()["results"] if _i["name"] == item["name"]), None)
            self.assertEqual(response_item["volume_30_day"], item["volume_30_day"])
            self.assertEqual(response_item["query_usage_30_day"], item["query_usage_30_day"])

    def test_pagination_of_event_definitions(self):
        self.demo_team.event_names = self.demo_team.event_names + [f"z_event_{i}" for i in range(1, 301)]
        self.demo_team.save()

        response = self.client.get("/api/projects/@current/event_definitions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 305)
        self.assertEqual(len(response.json()["results"]), 100)  # Default page size
        self.assertEqual(response.json()["results"][0]["name"], "entered_free_trial")  # Order by name (ascending)

        event_checkpoints = [
            185,
            275,
            95,
        ]  # Because Postgres's sorter does this: event_1; event_100, ..., event_2, event_200, ..., it's
        # easier to deterministically set the expected events

        for i in range(0, 3):
            response = self.client.get(response.json()["next"])
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(response.json()["count"], 305)
            self.assertEqual(
                len(response.json()["results"]), 100 if i < 2 else 5
            )  # Each page has 100 except the last one
            self.assertEqual(response.json()["results"][0]["name"], f"z_event_{event_checkpoints[i]}")
