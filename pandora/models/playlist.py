from enum import Enum

from ..client import BaseAPIClient
from ._base import Field, SyntheticField, PandoraModel, PandoraListModel


class AdditionalAudioUrl(Enum):
    HTTP_40_AAC_MONO = "HTTP_40_AAC_MONO"
    HTTP_64_AAC = "HTTP_64_AAC"
    HTTP_32_AACPLUS = "HTTP_32_AACPLUS"
    HTTP_64_AACPLUS = "HTTP_64_AACPLUS"
    HTTP_24_AACPLUS_ADTS = "HTTP_24_AACPLUS_ADTS"
    HTTP_32_AACPLUS_ADTS = "HTTP_32_AACPLUS_ADTS"
    HTTP_64_AACPLUS_ADTS = "HTTP_64_AACPLUS_ADTS"
    HTTP_128_MP3 = "HTTP_128_MP3"
    HTTP_32_WMA = "HTTP_32_WMA"


class PandoraType(Enum):

    TRACK = "TR"
    ARTIST = "AR"
    GENRE = "GR"

    @staticmethod
    def from_model(client, value):
        return PandoraType.from_string(value)

    @staticmethod
    def from_string(value):
        types = {
            "TR": PandoraType.TRACK,
            "AR": PandoraType.ARTIST,
        }
        return types.get(value, PandoraType.GENRE)


class AudioField(SyntheticField):
    def formatter(self, api_client, data, newval):
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

        valid_audio_formats = [
            BaseAPIClient.HIGH_AUDIO_QUALITY,
            BaseAPIClient.MED_AUDIO_QUALITY,
            BaseAPIClient.LOW_AUDIO_QUALITY,
        ]

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
    def formatter(self, api_client, data, newval):
        """Parse additional url fields and map them to inputs

        Attempt to create a dictionary with keys being user input, and
        response being the returned URL
        """
        if newval is None:
            return None

        user_param = data["_paramAdditionalUrls"]
        urls = {}
        if isinstance(newval, str):
            urls[user_param[0]] = newval
        else:
            for key, url in zip(user_param, newval):
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

    def thumbs_up(self):
        raise NotImplementedError

    def thumbs_down(self):
        raise NotImplementedError

    def bookmark_song(self):
        raise NotImplementedError

    def bookmark_artist(self):
        raise NotImplementedError

    def sleep(self):
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

    def thumbs_up(self):
        return self._api_client.add_feedback(self.track_token, True)

    def thumbs_down(self):
        return self._api_client.add_feedback(self.track_token, False)

    def bookmark_song(self):
        return self._api_client.add_song_bookmark(self.track_token)

    def bookmark_artist(self):
        return self._api_client.add_artist_bookmark(self.track_token)

    def sleep(self):
        return self._api_client.sleep_song(self.track_token)


class Playlist(PandoraListModel):

    __list_key__ = "items"
    __list_model__ = PlaylistItem
