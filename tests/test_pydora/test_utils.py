from unittest import TestCase
from unittest.mock import Mock, patch

from pandora.client import APIClient
from pandora.errors import InvalidAuthToken, ParameterMissing
from pandora.models.pandora import Station, AdItem, PlaylistItem
from pydora.utils import iterate_forever


class TestIterateForever(TestCase):

    def setUp(self):
        self.transport = Mock(side_effect=[InvalidAuthToken(), None])
        self.client = APIClient(self.transport, None, None, None, None)
        self.client._authenticate = Mock()

    def test_handle_missing_params_exception_due_to_missing_ad_tokens(self):
        with patch.object(APIClient, 'get_playlist') as get_playlist_mock:
            admock = patch.object(
                APIClient, 'register_ad',
                side_effect=ParameterMissing("ParameterMissing"))

            with admock:
                station = Station.from_json(
                    self.client, {'stationToken': 'token_mock'})
                ad_mock = AdItem.from_json(
                    self.client, {'station_id': 'id_mock'})
                get_playlist_mock.return_value = iter([ad_mock])

                station_iter = iterate_forever(station.get_playlist)

                next_track = next(station_iter)
                self.assertEqual(ad_mock, next_track)

    def test_reraise_missing_params_exception(self):
        plmock = patch.object(
            APIClient, 'get_playlist',
            side_effect=ParameterMissing("ParameterMissing"))

        with plmock as get_playlist_mock:
                with self.assertRaises(ParameterMissing):
                    station = Station.from_json(
                        self.client, {'stationToken': 'token_mock'})
                    track_mock = PlaylistItem.from_json(
                        self.client, {'token': 'token_mock'})
                    get_playlist_mock.return_value = iter([track_mock])

                    station_iter = iterate_forever(station.get_playlist)
                    next(station_iter)
