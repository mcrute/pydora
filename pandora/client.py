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

    ALL_QUALITIES = [LOW_AUDIO_QUALITY, MED_AUDIO_QUALITY, HIGH_AUDIO_QUALITY]

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

        self.transport.set_partner(partner)

        return partner

    def login(self, username, password):
        self.username = username
        self.password = password
        return self._authenticate()

    def _authenticate(self):
        self._partner_login()

        try:
            user = self.transport("auth.userLogin",
                                  loginType="user",
                                  username=self.username,
                                  password=self.password,
                                  includePandoraOneInfo=True,
                                  includeSubscriptionExpiration=True,
                                  returnCapped=True,
                                  includeAdAttributes=True,
                                  includeAdvertiserAttributes=True,
                                  xplatformAdCapable=True)
        except errors.InvalidPartnerLogin:
            raise errors.InvalidUserLogin()

        self.transport.set_user(user)

        return user

    @classmethod
    def get_qualities(cls, start_at, return_all_if_invalid=True):
        try:
            idx = cls.ALL_QUALITIES.index(start_at)
            return cls.ALL_QUALITIES[:idx + 1]
        except ValueError:
            if return_all_if_invalid:
                return cls.ALL_QUALITIES[:]
            else:
                return []

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

        playlist = Playlist.from_json(self,
                                      self("station.getPlaylist",
                                           stationToken=station_token,
                                           includeTrackLength=True,
                                           xplatformAdCapable=True,
                                           audioAdPodCapable=True))

        for i, track in enumerate(playlist):
            if track.is_ad:
                track = self.get_ad_item(station_token, track.ad_token)
                playlist[i] = track

        return playlist

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

    def search(self, search_text,
               include_near_matches=False,
               include_genre_stations=False):
        from .models.pandora import SearchResult

        return SearchResult.from_json(
            self,
            self("music.search",
                 searchText=search_text,
                 includeNearMatches=include_near_matches,
                 includeGenreStations=include_genre_stations)
        )

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
        from .models.pandora import GenreStationList

        genres = self("station.getGenreStations")

        genre_stations = GenreStationList.from_json(self, genres)
        genre_stations.checksum = self.get_genre_stations_checksum()
        return genre_stations

    def get_genre_stations_checksum(self):
        return self("station.getGenreStationsChecksum")["checksum"]

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

    def get_ad_item(self, station_id, ad_token):
        from .models.pandora import AdItem

        if not station_id:
            raise errors.ParameterMissing("The 'station_id' param must be "
                                          "defined, got: '{}'"
                                          .format(station_id))

        ad_item = AdItem.from_json(self, self.get_ad_metadata(ad_token))
        ad_item.station_id = station_id
        ad_item.ad_token = ad_token
        return ad_item

    def get_ad_metadata(self, ad_token):
        return self("ad.getAdMetadata",
                    adToken=ad_token,
                    returnAdTrackingTokens=True,
                    supportAudioAds=True)

    def register_ad(self, station_id, tokens):
        return self("ad.registerAd",
                    stationId=station_id,
                    adTrackingTokens=tokens)
