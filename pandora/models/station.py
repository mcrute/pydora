from ._base import Field, DateField
from ._base import PandoraModel, PandoraListModel, PandoraDictListModel
from .playlist import PandoraType


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
        return iter(self._api_client.get_playlist(self.token, additional_urls))


class StationList(PandoraListModel):

    checksum = Field("checksum")

    __index_key__ = "id"
    __list_key__ = "stations"
    __list_model__ = Station

    def has_changed(self):
        checksum = self._api_client.get_station_list_checksum()
        return checksum != self.checksum


class GenreStation(PandoraModel):

    id = Field("stationId")
    name = Field("stationName")
    token = Field("stationToken")
    category = Field("categoryName")

    def get_playlist(self):
        raise NotImplementedError(
            "Genre stations do not have playlists. "
            "Create a real station using the token."
        )


class GenreStationList(PandoraDictListModel):

    checksum = Field("checksum")

    __dict_list_key__ = "categories"
    __dict_key__ = "categoryName"
    __list_key__ = "stations"
    __list_model__ = GenreStation

    def has_changed(self):
        checksum = self._api_client.get_station_list_checksum()
        return checksum != self.checksum
