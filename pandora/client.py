"""
Pandora API Client

This module contains the top level API client that is responsible for calling
the API and returing the results in model format. There is a base API client
that is useful for lower level programming such as calling methods that aren't
directly supported by the higher level API client.

The high level API client is what most clients should use and provides API
calls that map directly to the Pandora API and return model objects with
mappings from the raw JSON structures to Python objects.

For simplicity use a client builder from pandora.clientbuilder to create an
instance of a client.
"""
from . import errors
from .util import deprecated


class BaseAPIClient(object):
    """Base Pandora API Client

    The base API client has lower level methods that are composed together to
    provide higher level functionality.
    """

    LOW_AUDIO_QUALITY = "lowQuality"
    MED_AUDIO_QUALITY = "mediumQuality"
    HIGH_AUDIO_QUALITY = "highQuality"

    def __init__(self, transport, partner_user, partner_password, device,
                 ad_support_enabled=False, default_audio_quality=MED_AUDIO_QUALITY):
        self.transport = transport
        self.partner_user = partner_user
        self.partner_password = partner_password
        self.device = device
        self.default_audio_quality = default_audio_quality
        self.ad_support_enabled = ad_support_enabled
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

        self.transport.set_partner(partner)

        return partner

    def login(self, username, password):
        self.username = username
        self.password = password
        return self._authenticate()

    def _authenticate(self):
        self._partner_login()

        parameters = dict("auth.userLogin",
                          loginType="user",
                          username=self.username,
                          password=self.password,
                          includePandoraOneInfo=True,
                          includeSubscriptionExpiration=True,
                          returnCapped=True)

        ad_parameters = dict(includeAdAttributes=True,
                             includeAdvertiserAttributes=True,
                             xplatformAdCapable=True)

        if self.ad_support_enabled:
            parameters = parameters + ad_parameters

        user = self.transport(parameters)

        self.transport.set_user(user)

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

    def get_station_list(self):
        from .models.pandora import StationList

        return StationList.from_json(self,
                                     self("user.getStationList",
                                          includeStationArtUrl=True))

    def get_station_list_checksum(self):
        return self("user.getStationListChecksum")["checksum"]

    def get_playlist(self, station_token):
        from .models.pandora import Playlist

        parameters = dict("station.getPlaylist",
                          stationToken=station_token,
                          includeTrackLength=True)

        ad_parameters = dict(xplatformAdCapable=True,
                             audioAdPodCapable=True,)

        if self.ad_support_enabled:
            parameters = parameters + ad_parameters

        return Playlist.from_json(self,
                                  self(parameters))

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

    def get_ad_item(self, ad_token):
        from .models.pandora import AdItem

        return AdItem.from_json(self, self.get_ad_metadata(ad_token))

    def get_ad_metadata(self, ad_token):
        return self("ad.getAdMetadata",
                    adToken=ad_token,
                    returnAdTrackingTokens=True,
                    supportAudioAds=True,
                    includeBannerAd=True)

    def register_ad(self, station_id, tokens):
        return self("ad.registerAd",
            stationId=station_id,
            adTrackingTokens=tokens)
