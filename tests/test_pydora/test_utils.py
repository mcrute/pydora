from unittest import TestCase
from pandora import errors

from pandora.client import APIClient
from pandora.errors import InvalidAuthToken
from pandora.models.pandora import Station, AdItem
from pandora.py2compat import Mock, patch
from pydora.utils import iterate_forever
from tests.test_pandora.test_models import TestAdItem


class TestIterateForever(TestCase):

    def setUp(self):
        transport = Mock(side_effect=[InvalidAuthToken(), None])
        client = APIClient(transport, None, None, None, None)
        client._authenticate = Mock()
        self.result = AdItem.from_json(client, TestAdItem.JSON_DATA)

    def test_handle_missing_params_exception_due_to_missing_ad_tokens(self):
        with patch.object(APIClient, 'register_ad', side_effect=errors.ParameterMissing("ParameterMissing")):

            station = Mock(spec=Station)
            station.token = 'mock_token'

            self.result.tracking_tokens = []

            station.get_playlist.return_value = iter([self.result])
            station_iter = iterate_forever(station.get_playlist)

            next_track = station_iter.next()
            self.assertEqual(self.result, next_track)
