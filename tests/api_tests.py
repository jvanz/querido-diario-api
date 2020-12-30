from datetime import date
from unittest.mock import MagicMock
from unittest import TestCase, expectedFailure

from fastapi.testclient import TestClient

from api import app, configure_api_app
from gazettes import GazetteAccessInterface, GazetteRequest


@GazetteAccessInterface.register
class MockGazetteAccessInterface:
    pass


class ApiGazettesEndpointTests(TestCase):
    def create_mock_gazette_interface(self, return_value=None):
        interface = MockGazetteAccessInterface()
        interface.get_gazettes = MagicMock(return_value=return_value)
        return interface

    def test_api_should_fail_when_try_to_set_any_object_as_gazettes_interface(self):
        with self.assertRaises(Exception):
            configure_api_app(MagicMock())

    def test_api_should_not_fail_when_try_to_set_any_object_as_gazettes_interface(self):
        configure_api_app(MockGazetteAccessInterface())

    def test_gazettes_endpoint_should_accept_territory_id_in_the_path(self):
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get("/gazettes/4205902")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            "4205902", interface.get_gazettes.call_args.args[0].territory_id
        )
        self.assertIsNone(interface.get_gazettes.call_args.args[0].since)
        self.assertIsNone(interface.get_gazettes.call_args.args[0].until)
        self.assertIsNone(interface.get_gazettes.call_args.args[0].keywords)
        self.assertIsNotNone(interface.get_gazettes.call_args.args[0].page)
        self.assertIsNotNone(interface.get_gazettes.call_args.args[0].page_size)

    def test_gazettes_endpoint_should_accept_query_since_date(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get(
            "/gazettes/4205902", params={"since": date.today().strftime("%Y-%m-%d")}
        )
        self.assertEqual(response.status_code, 200)

    def test_gazettes_endpoint_should_accept_query_until_date(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get(
            "/gazettes/4205902", params={"until": date.today().strftime("%Y-%m-%d")}
        )
        self.assertEqual(response.status_code, 200)

    def test_gazettes_endpoint_should_fail_with_invalid_since_value(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get("/gazettes/4205902", params={"since": "foo-bar-2222"})
        self.assertEqual(response.status_code, 422)

    def test_gazettes_endpoint_should_fail_with_invalid_until_value(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get("/gazettes/4205902", params={"until": "foo-bar-2222"})
        self.assertEqual(response.status_code, 422)

    def test_gazettes_endpoint_should_fail_with_invalid_pagination_data(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get(
            "/gazettes/4205902", params={"page": "asfasdasd", "page_size": "10"}
        )
        self.assertEqual(response.status_code, 422)
        response = client.get(
            "/gazettes/4205902", params={"page": "1", "page_size": "ssddsfds"}
        )
        self.assertEqual(response.status_code, 422)
        response = client.get(
            "/gazettes/4205902", params={"page": "x", "page_size": "asdasdas"}
        )
        self.assertEqual(response.status_code, 422)

    def test_get_gazettes_without_territory_id_should_be_fine(self):
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get("/gazettes/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(interface.get_gazettes.call_args.args[0].territory_id)
        self.assertIsNone(interface.get_gazettes.call_args.args[0].since)
        self.assertIsNone(interface.get_gazettes.call_args.args[0].until)
        self.assertIsNone(interface.get_gazettes.call_args.args[0].keywords)
        self.assertIsNotNone(interface.get_gazettes.call_args.args[0].page)
        self.assertIsNotNone(interface.get_gazettes.call_args.args[0].page_size)

    def test_get_gazettes_should_request_gazettes_to_interface_object(self):
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get("/gazettes/4205902")
        self.assertEqual(response.status_code, 200)
        interface.get_gazettes.assert_called_once()

    def test_get_gazettes_should_forward_gazettes_filters_to_interface_object(self):
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get(
            "/gazettes/4205902",
            params={
                "since": date.today().strftime("%Y-%m-%d"),
                "until": date.today().strftime("%Y-%m-%d"),
                "page": 10,
                "page_size": 100,
            },
        )
        self.assertEqual(response.status_code, 200)
        interface.get_gazettes.assert_called_once()
        self.assertEqual(
            interface.get_gazettes.call_args.args[0].territory_id, "4205902"
        )
        self.assertEqual(
            interface.get_gazettes.call_args.args[0].since, date.today(),
        )
        self.assertEqual(interface.get_gazettes.call_args.args[0].until, date.today())
        self.assertEqual(interface.get_gazettes.call_args.args[0].page, 9)
        self.assertEqual(interface.get_gazettes.call_args.args[0].page_size, 100)

    def test_get_gazettes_should_return_json_with_items(self):
        today = date.today()
        interface = self.create_mock_gazette_interface(
            [
                {
                    "territory_id": "4205902",
                    "date": today,
                    "url": "https://queridodiario.ok.org.br/",
                    "territory_name": "My city",
                    "state_code": "My state",
                }
            ]
        )
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get("/gazettes/4205902")
        interface.get_gazettes.assert_called_once()
        self.assertEqual(
            interface.get_gazettes.call_args.args[0].territory_id, "4205902"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "territory_id": "4205902",
                    "date": today.strftime("%Y-%m-%d"),
                    "url": "https://queridodiario.ok.org.br/",
                    "territory_name": "My city",
                    "state_code": "My state",
                }
            ],
        )

    def test_get_gazettes_should_return_empty_list_when_no_gazettes_is_found(self):
        today = date.today()
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get("/gazettes/4205902")
        interface.get_gazettes.assert_called_once()
        self.assertEqual(
            interface.get_gazettes.call_args.args[0].territory_id, "4205902"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_gazettes_endpoint_should_accept_query_keywords_date(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get(
            "/gazettes/4205902", params={"keywords": ["keyword1" "keyword2"]}
        )
        self.assertEqual(response.status_code, 200)
        response = client.get("/gazettes/4205902", params={"keywords": []})
        self.assertEqual(response.status_code, 200)

    def test_get_gazettes_should_forwards_keywords_to_interface_object(self):
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)

        response = client.get(
            "/gazettes/4205902", params={"keywords": ["keyword1", 1, True]}
        )
        interface.get_gazettes.assert_called_once()
        self.assertEqual(
            interface.get_gazettes.call_args.args[0].keywords, ["keyword1", "1", "True"]
        )

        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        response = client.get("/gazettes/4205902", params={"keywords": []})
        interface.get_gazettes.assert_called_once()
        self.assertIsNone(interface.get_gazettes.call_args.args[0].keywords)

    def test_gazettes_without_territory_endpoint__should_accept_query_since_date(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get(
            "/gazettes", params={"since": date.today().strftime("%Y-%m-%d")}
        )
        self.assertEqual(response.status_code, 200)

    def test_gazettes_without_territory_endpoint__should_accept_query_until_date(self):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get(
            "/gazettes", params={"until": date.today().strftime("%Y-%m-%d")}
        )
        self.assertEqual(response.status_code, 200)

    def test_gazettes_without_territory_endpoint__should_fail_with_invalid_since_value(
        self,
    ):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get("/gazettes", params={"since": "foo-bar-2222"})
        self.assertEqual(response.status_code, 422)

    def test_gazettes_without_territory_endpoint__should_fail_with_invalid_until_value(
        self,
    ):
        configure_api_app(self.create_mock_gazette_interface())
        client = TestClient(app)
        response = client.get("/gazettes", params={"until": "foo-bar-2222"})
        self.assertEqual(response.status_code, 422)

    def test_get_gazettes_without_territory_id_should_forward_gazettes_filters_to_interface_object(
        self,
    ):
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get(
            "/gazettes",
            params={
                "since": date.today().strftime("%Y-%m-%d"),
                "until": date.today().strftime("%Y-%m-%d"),
                "page": 10,
                "page_size": 100,
            },
        )
        self.assertEqual(response.status_code, 200)
        interface.get_gazettes.assert_called_once()
        self.assertIsNone(interface.get_gazettes.call_args.args[0].territory_id)
        self.assertEqual(
            interface.get_gazettes.call_args.args[0].since, date.today(),
        )
        self.assertEqual(interface.get_gazettes.call_args.args[0].until, date.today())
        self.assertEqual(interface.get_gazettes.call_args.args[0].page, 9)
        self.assertEqual(interface.get_gazettes.call_args.args[0].page_size, 100)

    def test_api_should_decrease_one_from_page_number_for_internal_use(self):
        interface = self.create_mock_gazette_interface()
        configure_api_app(interface)
        client = TestClient(app)
        response = client.get("/gazettes", params={"page": 1,},)
        self.assertEqual(response.status_code, 200)
        interface.get_gazettes.assert_called_once()
        self.assertEqual(interface.get_gazettes.call_args.args[0].page, 0)

    @expectedFailure
    def test_configure_api_should_failed_with_invalid_root_path(self):
        configure_api_app(MockGazetteAccessInterface(), api_root_path=1)

    def test_configure_api_root_path(self):
        configure_api_app(MockGazetteAccessInterface(), api_root_path="/api/v1")
        self.assertEqual("/api/v1", app.root_path)
