"""
Pandora API Client

This is a reasonably complete implementation of the Pandora API. It does not
implement any of the undocumented features and does not implement most of the
account management features as they were deemed not terribly useful.

API Spec from: http://6xq.net/playground/pandora-apidoc/
Keys at: http://6xq.net/playground/pandora-apidoc/json/partners/#partners
"""
import time
import json
import base64
import requests
from Crypto.Cipher import Blowfish

from . import errors
from .util import deprecated
from .errors import PandoraException


DEFAULT_API_HOST = "tuner.pandora.com/services/json/"


class APITransport(object):
    """Pandora API Transport

    The transport is responsible for speaking the low-level protocol required
    by the Pandora API. It knows about encryption, TLS and the other API
    details. Once setup the transport acts like a callable.
    """

    API_VERSION = "5"

    NO_ENCRYPT = ("auth.partnerLogin", )
    REQUIRE_TLS = ("auth.partnerLogin", "auth.userLogin",
                   "station.getPlaylist", "user.createUser")

    def __init__(self, cryptor, api_host=DEFAULT_API_HOST, proxy=None):
        self.cryptor = cryptor
        self.api_host = api_host
        self.proxy = proxy

        self.partner_auth_token = None
        self.user_auth_token = None

        self.partner_id = None
        self.user_id = None

        self.start_time = None
        self.server_sync_time = None

        self._http = requests.Session()

        if self.proxy:
            self._http.proxies = {
                'http': self.proxy,
                'https': self.proxy,
            }

    @property
    def auth_token(self):
        if self.user_auth_token:
            return self.user_auth_token

        if self.partner_auth_token:
            return self.partner_auth_token

        return None

    @property
    def sync_time(self):
        if not self.server_sync_time:
            return None

        return int(self.server_sync_time + (time.time() - self.start_time))

    def remove_empty_values(self, data):
        return dict((k, v) for k, v in data.items() if v is not None)

    @sync_time.setter
    def sync_time(self, sync_time):
        self.server_sync_time = self.cryptor.decrypt_sync_time(sync_time)

    def _start_request(self):
        if not self.start_time:
            self.start_time = int(time.time())

    def _make_http_request(self, url, data, params):
        try:
            data = data.encode("utf-8")
        except AttributeError:
            pass

        params = self.remove_empty_values(params)

        r = self._http.post(url, data=data, params=params)
        r.raise_for_status()
        return r.content

    def test_url(self, url):
        return self._http.head(url).status_code == requests.codes.OK

    def _build_params(self, method):
        return {
            "method": method,
            "auth_token": self.auth_token,
            "partner_id": self.partner_id,
            "user_id": self.user_id,
        }

    def _build_url(self, method):
        return "{0}://{1}".format(
            "https" if method in self.REQUIRE_TLS else "http",
            self.api_host)

    def _build_data(self, method, data):
        data["userAuthToken"] = self.user_auth_token
        data["syncTime"] = self.sync_time

        if not self.user_auth_token and self.partner_auth_token:
            data["partnerAuthToken"] = self.partner_auth_token

        data = json.dumps(self.remove_empty_values(data))

        if method not in self.NO_ENCRYPT:
            data = self.cryptor.encrypt(data)

        return data

    def _parse_response(self, result):
        result = json.loads(result.decode("utf-8"))

        if result["stat"] == "ok":
            return result["result"] if "result" in result else None
        else:
            raise PandoraException.from_code(result["code"], result["message"])

    def __call__(self, method, **data):
        self._start_request()

        url = self._build_url(method)
        data = self._build_data(method, data)
        params = self._build_params(method)
        result = self._make_http_request(url, data, params)

        return self._parse_response(result)


class Encryptor(object):
    """Pandora Blowfish Encryptor

    The blowfish encryptor can encrypt and decrypt the relevant parts of the
    API request and response. It handles the formats that the API expects.
    """

    def __init__(self, in_key, out_key):
        self.bf_out = Blowfish.new(out_key, Blowfish.MODE_ECB)
        self.bf_in = Blowfish.new(in_key, Blowfish.MODE_ECB)

    @staticmethod
    def _decode_hex(data):
        return base64.b16decode(data.upper())

    @staticmethod
    def _encode_hex(data):
        return base64.b16encode(data).lower()

    def decrypt(self, data):
        data = self.bf_out.decrypt(self._decode_hex(data))
        return json.loads(self.strip_padding(data))

    def decrypt_sync_time(self, data):
        return int(self.bf_in.decrypt(self._decode_hex(data))[4:-2])

    def add_padding(self, data):
        block_size = Blowfish.block_size
        pad_size = len(data) % block_size
        return data + (chr(pad_size) * (block_size - pad_size))

    def strip_padding(self, data):
        pad_size = int(data[-1])
        if not data[-pad_size:] == bytes((pad_size,)) * pad_size:
            raise ValueError('Invalid padding')
        return data[:-pad_size]

    def encrypt(self, data):
        return self._encode_hex(self.bf_out.encrypt(self.add_padding(data)))


class BaseAPIClient(object):
    """Base Pandora API Client

    The base API client has lower level methods that are composed together to
    provide higher level functionality.
    """

    LOW_AUDIO_QUALITY = "lowQuality"
    MED_AUDIO_QUALITY = "mediumQuality"
    HIGH_AUDIO_QUALITY = "highQuality"

    def __init__(self, transport, partner_user, partner_password, device,
                 default_audio_quality=MED_AUDIO_QUALITY):
        self.transport = transport
        self.partner_user = partner_user
        self.partner_password = partner_password
        self.device = device
        self.default_audio_quality = default_audio_quality
        self.username = None
        self.password = None

    @classmethod
    @deprecated("1.3", "2.0",
                "Replaced by clientbuilder.SettingsDictBuilder")
    def from_settings_dict(cls, settings):
        from .clientbuilder import SettingsDictBuilder
        return SettingsDictBuilder(settings).build()

    @classmethod
    @deprecated("1.3", "2.0",
                "Replaced by clientbuilder.PydoraConfigFileBuilder")
    def from_config_file(cls, path, authenticate=True):
        from .clientbuilder import PydoraConfigFileBuilder
        return PydoraConfigFileBuilder(path, authenticate).build()

    def _partner_login(self):
        partner = self.transport("auth.partnerLogin",
                                 username=self.partner_user,
                                 password=self.partner_password,
                                 deviceModel=self.device,
                                 version=self.transport.API_VERSION)

        self.transport.sync_time = partner["syncTime"]
        self.transport.partner_auth_token = partner["partnerAuthToken"]
        self.transport.partner_id = partner["partnerId"]

        return partner

    def _user_login(self, username, password):
        self.username = username
        self.password = password
        return self._authenticate()

    def _ensure_credentials_available(self):
        if not self.username or not self.password:
            raise errors.AuthenticationRequired()

    def _authenticate(self):
        self._ensure_credentials_available()

        user = self.transport("auth.userLogin",
                              loginType="user",
                              username=self.username,
                              password=self.password,
                              includePandoraOneInfo=True,
                              includeSubscriptionExpiration=True,
                              returnCapped=True)

        self.transport.user_id = user["userId"]
        self.transport.user_auth_token = user["userAuthToken"]

        return user

    def __call__(self, method, **kwargs):
        try:
            return self.transport(method, **kwargs)
        except errors.InvalidAuthToken:
            self._authenticate()
            return self.transport(method, **kwargs)


class APIClient(BaseAPIClient):
    """High Level Pandora API Client

    The high level API client implements the entire functional API for Pandora.
    This is what clients should actually use.
    """

    def login(self, username, password):
        self._partner_login()
        return self._user_login(username, password)

    def get_station_list(self):
        from .models.pandora import StationList

        return StationList.from_json(self,
                                     self("user.getStationList",
                                          includeStationArtUrl=True))

    def get_station_list_checksum(self):
        return self("user.getStationListChecksum")["checksum"]

    def get_playlist(self, station_token):
        from .models.pandora import Playlist

        return Playlist.from_json(self,
                                  self("station.getPlaylist",
                                       stationToken=station_token,
                                       includeTrackLength=True))

    def get_bookmarks(self):
        from .models.pandora import BookmarkList

        return BookmarkList.from_json(self,
                                      self("user.getBookmarks"))

    def get_station(self, station_token):
        from .models.pandora import Station

        return Station.from_json(self,
                                 self("station.getStation",
                                      stationToken=station_token,
                                      includeExtendedAttributes=True))

    def add_artist_bookmark(self, track_token):
        return self("bookmark.addArtistBookmark",
                    trackToken=track_token)

    def add_song_bookmark(self, track_token):
        return self("bookmark.addSongBookmark",
                    trackToken=track_token)

    def delete_song_bookmark(self, bookmark_token):
        return self("bookmark.deleteSongBookmark",
                    bookmarkToken=bookmark_token)

    def delete_artist_bookmark(self, bookmark_token):
        return self("bookmark.deleteArtistBookmark",
                    bookmarkToken=bookmark_token)

    def search(self, search_text):
        from .models.pandora import SearchResult

        return SearchResult.from_json(self,
                                      self("music.search",
                                           searchText=search_text))

    def add_feedback(self, track_token, positive):
        return self("station.addFeedback",
                    trackToken=track_token,
                    isPositive=positive)

    def add_music(self, music_token, station_token):
        return self("station.addMusic",
                    musicToken=music_token,
                    stationToken=station_token)

    def create_station(self, search_token=None, artist_token=None,
                       track_token=None):
        kwargs = {}

        if search_token:
            kwargs = {"musicToken": search_token}
        elif artist_token:
            kwargs = {"trackToken": artist_token, "musicType": "artist"}
        elif track_token:
            kwargs = {"trackToken": track_token, "musicType": "song"}
        else:
            raise KeyError("Must pass a type of token")

        return self("station.createStation", **kwargs)

    def delete_feedback(self, feedback_id):
        return self("station.deleteFeedback",
                    feedbackId=feedback_id)

    def delete_music(self, seed_id):
        return self("station.deleteMusic",
                    seedId=seed_id)

    def delete_station(self, station_token):
        return self("station.deleteStation",
                    stationToken=station_token)

    def get_genre_stations(self):
        from .models.pandora import GenreStations

        categories = self("station.getGenreStations")["categories"]
        return GenreStations.from_json(self, categories)

    def rename_station(self, station_token, name):
        return self("station.renameStation",
                    stationToken=station_token,
                    stationName=name)

    def explain_track(self, track_token):
        return self("track.explainTrack",
                    trackToken=track_token)

    def set_quick_mix(self, *args):
        return self("user.setQuickMix",
                    quickMixStationIds=args)

    def sleep_song(self, track_token):
        return self("user.sleepSong",
                    trackToken=track_token)

    def share_station(self, station_id, station_token, *emails):
        return self("station.shareStation",
                    stationId=station_id,
                    stationToken=station_token,
                    emails=emails)

    def transform_shared_station(self, station_token):
        return self("station.transformSharedStation",
                    stationToken=station_token)

    def share_music(self, music_token, *emails):
        return self("music.shareMusic",
                    musicToken=music_token,
                    email=emails[0])
