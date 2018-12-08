from enum import Enum

from ..client import BaseAPIClient
from ..errors import ParameterMissing
from . import Field, DateField, SyntheticField
from . import PandoraModel, PandoraListModel, PandoraDictListModel


class AdditionalAudioUrl(Enum):
    HTTP_40_AAC_MONO = 'HTTP_40_AAC_MONO'
    HTTP_64_AAC = 'HTTP_64_AAC'
    HTTP_32_AACPLUS = 'HTTP_32_AACPLUS'
    HTTP_64_AACPLUS = 'HTTP_64_AACPLUS'
    HTTP_24_AACPLUS_ADTS = 'HTTP_24_AACPLUS_ADTS'
    HTTP_32_AACPLUS_ADTS = 'HTTP_32_AACPLUS_ADTS'
    HTTP_64_AACPLUS_ADTS = 'HTTP_64_AACPLUS_ADTS'
    HTTP_128_MP3 = 'HTTP_128_MP3'
    HTTP_32_WMA = 'HTTP_32_WMA'


class PandoraType(Enum):

    TRACK = "TR"
    ARTIST = "AR"
    GENRE = "GR"

    @staticmethod
    def from_model(client, value):
        return PandoraType.from_string(value)

    @staticmethod
    def from_string(value):
        return {
            "TR": PandoraType.TRACK,
            "AR": PandoraType.ARTIST,
        }.get(value, PandoraType.GENRE)


class Icon(PandoraModel):

    dominant_color = Field("dominantColor")
    art_url = Field("artUrl")


class StationSeed(PandoraModel):

    seed_id = Field("seedId")
    music_token = Field("musicToken")
    pandora_id = Field("pandoraId")
    pandora_type = Field("pandoraType", formatter=PandoraType.from_model)

    genre_name = Field("genreName")
    song_name = Field("songName")
    artist_name = Field("artistName")
    art_url = Field("artUrl")
    icon = Field("icon", model=Icon)


class StationSeeds(PandoraModel):

    genres = Field("genres", model=StationSeed)
    songs = Field("songs", model=StationSeed)
    artists = Field("artists", model=StationSeed)


class SongFeedback(PandoraModel):

    feedback_id = Field("feedbackId")
    song_identity = Field("songIdentity")
    is_positive = Field("isPositive")
    pandora_id = Field("pandoraId")
    album_art_url = Field("albumArtUrl")
    music_token = Field("musicToken")
    song_name = Field("songName")
    artist_name = Field("artistName")
    pandora_type = Field("pandoraType", formatter=PandoraType.from_model)
    date_created = DateField("dateCreated")


class StationFeedback(PandoraModel):

    total_thumbs_up = Field("totalThumbsUp")
    total_thumbs_down = Field("totalThumbsDown")
    thumbs_up = Field("thumbsUp", model=SongFeedback)
    thumbs_down = Field("thumbsDown", model=SongFeedback)


class Station(PandoraModel):

    can_add_music = Field("allowAddMusic")
    can_delete = Field("allowDelete")
    can_rename = Field("allowRename")
    can_edit_description = Field("allowEditDescription")
    process_skips = Field("processSkips")
    is_shared = Field("isShared")
    is_quickmix = Field("isQuickMix")
    is_genre_station = Field("isGenreStation")
    is_thumbprint_station = Field("isThumbprint")

    art_url = Field("artUrl")
    date_created = DateField("dateCreated")
    detail_url = Field("stationDetailUrl")
    id = Field("stationId")
    name = Field("stationName")
    sharing_url = Field("stationSharingUrl")
    thumb_count = Field("thumbCount")
    token = Field("stationToken")

    genre = Field("genre", [])
    quickmix_stations = Field("quickMixStationIds", [])

    seeds = Field("music", model=StationSeeds)
    feedback = Field("feedback", model=StationFeedback)

    def get_playlist(self, additional_urls=None):
        return iter(self._api_client.get_playlist(self.token,
                                                  additional_urls))


class GenreStation(PandoraModel):

    id = Field("stationId")
    name = Field("stationName")
    token = Field("stationToken")
    category = Field("categoryName")

    def get_playlist(self):  # pragma: no cover
        raise NotImplementedError("Genre stations do not have playlists. "
                                  "Create a real station using the token.")


class StationList(PandoraListModel):

    checksum = Field("checksum")

    __index_key__ = "id"
    __list_key__ = "stations"
    __list_model__ = Station

    def has_changed(self):
        checksum = self._api_client.get_station_list_checksum()
        return checksum != self.checksum


class AudioField(SyntheticField):

    def formatter(self, api_client, data, value):
        """Get audio-related fields

        Try to find fields for the audio url for specified preferred quality
        level, or next-lowest available quality url otherwise.
        """
        url_map = data.get("audioUrlMap")
        audio_url = data.get("audioUrl")

        # Only an audio URL, not a quality map. This happens for most of the
        # mobile client tokens and some of the others now. In this case
        # substitute the empirically determined default values in the format
        # used by the rest of the function so downstream consumers continue to
        # work.
        if audio_url and not url_map:
            url_map = {
                BaseAPIClient.HIGH_AUDIO_QUALITY: {
                    "audioUrl": audio_url,
                    "bitrate": 64,
                    "encoding": "aacplus",
                }
            }
        elif not url_map:  # No audio url available (e.g. ad tokens)
            return None

        valid_audio_formats = [BaseAPIClient.HIGH_AUDIO_QUALITY,
                               BaseAPIClient.MED_AUDIO_QUALITY,
                               BaseAPIClient.LOW_AUDIO_QUALITY]

        # Only iterate over sublist, starting at preferred audio quality, or
        # from the beginning of the list if nothing is found. Ensures that the
        # bitrate used will always be the same or lower quality than was
        # specified to prevent audio from skipping for slow connections.
        preferred_quality = api_client.default_audio_quality
        if preferred_quality in valid_audio_formats:
            i = valid_audio_formats.index(preferred_quality)
            valid_audio_formats = valid_audio_formats[i:]

        for quality in valid_audio_formats:
            audio_url = url_map.get(quality)

            if audio_url:
                return audio_url[self.field]

        return audio_url[self.field] if audio_url else None


class AdditionalUrlField(SyntheticField):

    def formatter(self, api_client, data, value):
        """Parse additional url fields and map them to inputs

        Attempt to create a dictionary with keys being user input, and
        response being the returned URL
        """
        if value is None:
            return None

        user_param = data['_paramAdditionalUrls']
        urls = {}
        if isinstance(value, str):
            urls[user_param[0]] = value
        else:
            for key, url in zip(user_param, value):
                urls[key] = url
        return urls


class PlaylistModel(PandoraModel):

    def get_is_playable(self):
        if not self.audio_url:
            return False
        return self._api_client.transport.test_url(self.audio_url)

    def prepare_playback(self):
        """Prepare Track for Playback

        This method must be called by clients before beginning playback
        otherwise the track recieved may not be playable.
        """
        return self

    def thumbs_up(self):  # pragma: no cover
        raise NotImplementedError

    def thumbs_down(self):  # pragma: no cover
        raise NotImplementedError

    def bookmark_song(self):  # pragma: no cover
        raise NotImplementedError

    def bookmark_artist(self):  # pragma: no cover
        raise NotImplementedError

    def sleep(self):  # pragma: no cover
        raise NotImplementedError


class PlaylistItem(PlaylistModel):

    artist_name = Field("artistName")
    album_name = Field("albumName")
    song_name = Field("songName")
    song_rating = Field("songRating")
    track_gain = Field("trackGain")
    track_length = Field("trackLength")
    track_token = Field("trackToken")
    audio_url = AudioField("audioUrl")
    bitrate = AudioField("bitrate")
    encoding = AudioField("encoding")
    album_art_url = Field("albumArtUrl")
    allow_feedback = Field("allowFeedback")
    station_id = Field("stationId")

    ad_token = Field("adToken")

    album_detail_url = Field("albumDetailUrl")
    album_explore_url = Field("albumExplorerUrl")

    amazon_album_asin = Field("amazonAlbumAsin")
    amazon_album_digital_asin = Field("amazonAlbumDigitalAsin")
    amazon_album_url = Field("amazonAlbumUrl")
    amazon_song_digital_asin = Field("amazonSongDigitalAsin")

    artist_detail_url = Field("artistDetailUrl")
    artist_explore_url = Field("artistExplorerUrl")

    itunes_song_url = Field("itunesSongUrl")

    song_detail_url = Field("songDetailUrl")
    song_explore_url = Field("songExplorerUrl")

    additional_audio_urls = AdditionalUrlField("additionalAudioUrl")

    @property
    def is_ad(self):
        return self.ad_token is not None

    def thumbs_up(self):  # pragma: no cover
        return self._api_client.add_feedback(self.track_token, True)

    def thumbs_down(self):  # pragma: no cover
        return self._api_client.add_feedback(self.track_token, False)

    def bookmark_song(self):  # pragma: no cover
        return self._api_client.add_song_bookmark(self.track_token)

    def bookmark_artist(self):  # pragma: no cover
        return self._api_client.add_artist_bookmark(self.track_token)

    def sleep(self):  # pragma: no cover
        return self._api_client.sleep_song(self.track_token)


class AdItem(PlaylistModel):

    title = Field("title")
    company_name = Field("companyName")
    tracking_tokens = Field("adTrackingTokens")
    audio_url = AudioField("audioUrl")
    image_url = Field("imageUrl")
    click_through_url = Field("clickThroughUrl")
    station_id = None
    ad_token = None

    @property
    def is_ad(self):
        return True

    def register_ad(self, station_id=None):
        if not station_id:
            station_id = self.station_id
        if self.tracking_tokens:
            self._api_client.register_ad(station_id, self.tracking_tokens)
        else:
            raise ParameterMissing('No ad tracking tokens provided for '
                                   'registration.')

    def prepare_playback(self):
        try:
            self.register_ad(self.station_id)
        except ParameterMissing as exc:
            if self.tracking_tokens:
                raise exc
        return super(AdItem, self).prepare_playback()


class Playlist(PandoraListModel):

    __list_key__ = "items"
    __list_model__ = PlaylistItem


class Bookmark(PandoraModel):

    music_token = Field("musicToken")
    artist_name = Field("artistName")
    art_url = Field("artUrl")
    bookmark_token = Field("bookmarkToken")
    date_created = DateField("dateCreated")

    # song only
    sample_url = Field("sampleUrl")
    sample_gain = Field("sampleGain")
    album_name = Field("albumName")
    song_name = Field("songName")

    @property
    def is_song_bookmark(self):
        return self.song_name is not None

    def delete(self):
        if self.is_song_bookmark:
            self._api_client.delete_song_bookmark(self.bookmark_token)
        else:
            self._api_client.delete_artist_bookmark(self.bookmark_token)


class BookmarkList(PandoraModel):

    songs = Field("songs", model=Bookmark)
    artists = Field("artists", model=Bookmark)


class SearchResultItem(PandoraModel):

    score = Field("score")
    token = Field("musicToken")

    @property
    def is_song(self):
        return isinstance(self, SongSearchResultItem)

    @property
    def is_artist(self):
        return isinstance(self, ArtistSearchResultItem) and \
               self.token.startswith("R")

    @property
    def is_composer(self):
        return isinstance(self, ArtistSearchResultItem) and \
               self.token.startswith("C")

    @property
    def is_genre_station(self):
        return isinstance(self, GenreStationSearchResultItem)

    def create_station(self):  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def from_json(cls, api_client, data):
        if data["musicToken"].startswith("S"):
            return SongSearchResultItem.from_json(api_client, data)
        elif data["musicToken"].startswith(("R", "C")):
            return ArtistSearchResultItem.from_json(api_client, data)
        elif data["musicToken"].startswith("G"):
            return GenreStationSearchResultItem.from_json(api_client, data)
        else:
            raise NotImplementedError("Unknown result token type '{}'"
                                      .format(data["musicToken"]))


class ArtistSearchResultItem(SearchResultItem):

    score = Field("score")
    token = Field("musicToken")
    artist = Field("artistName")
    likely_match = Field("likelyMatch", default=False)

    def create_station(self):
        self._api_client.create_station(artist_token=self.token)

    @classmethod
    def from_json(cls, api_client, data):
        return super(SearchResultItem, cls).from_json(api_client, data)


class SongSearchResultItem(SearchResultItem):

    score = Field("score")
    token = Field("musicToken")
    artist = Field("artistName")
    song_name = Field("songName")

    def create_station(self):
        self._api_client.create_station(track_token=self.token)

    @classmethod
    def from_json(cls, api_client, data):
        return super(SearchResultItem, cls).from_json(api_client, data)


class GenreStationSearchResultItem(SearchResultItem):

    score = Field("score")
    token = Field("musicToken")
    station_name = Field("stationName")

    def create_station(self):
        self._api_client.create_station(search_token=self.token)

    @classmethod
    def from_json(cls, api_client, data):
        return super(SearchResultItem, cls).from_json(api_client, data)


class SearchResult(PandoraModel):

    nearest_matches_available = Field("nearMatchesAvailable")
    explanation = Field("explanation")
    songs = Field("songs", model=SongSearchResultItem)
    artists = Field("artists", model=ArtistSearchResultItem)
    genre_stations = Field("genreStations", model=GenreStationSearchResultItem)


class GenreStationList(PandoraDictListModel):

    checksum = Field("checksum")

    __dict_list_key__ = "categories"
    __dict_key__ = "categoryName"
    __list_key__ = "stations"
    __list_model__ = GenreStation

    def has_changed(self):
        checksum = self._api_client.get_station_list_checksum()
        return checksum != self.checksum
