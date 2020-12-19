from ._base import Field, PandoraModel


class SearchResultItem(PandoraModel):

    score = Field("score")
    token = Field("musicToken")

    @property
    def is_song(self):
        return isinstance(self, SongSearchResultItem)

    @property
    def is_artist(self):
        return isinstance(
            self, ArtistSearchResultItem
        ) and self.token.startswith("R")

    @property
    def is_composer(self):
        return isinstance(
            self, ArtistSearchResultItem
        ) and self.token.startswith("C")

    @property
    def is_genre_station(self):
        return isinstance(self, GenreStationSearchResultItem)

    def create_station(self):
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
            raise NotImplementedError(
                "Unknown result token type '{}'".format(data["musicToken"])
            )


class ArtistSearchResultItem(SearchResultItem):

    score = Field("score")
    token = Field("musicToken")
    artist = Field("artistName")
    likely_match = Field("likelyMatch", default=False)

    def create_station(self):
        return self._api_client.create_station(artist_token=self.token)

    @classmethod
    def from_json(cls, api_client, data):
        return super(SearchResultItem, cls).from_json(api_client, data)


class SongSearchResultItem(SearchResultItem):

    score = Field("score")
    token = Field("musicToken")
    artist = Field("artistName")
    song_name = Field("songName")

    def create_station(self):
        return self._api_client.create_station(track_token=self.token)

    @classmethod
    def from_json(cls, api_client, data):
        return super(SearchResultItem, cls).from_json(api_client, data)


class GenreStationSearchResultItem(SearchResultItem):

    score = Field("score")
    token = Field("musicToken")
    station_name = Field("stationName")

    def create_station(self):
        return self._api_client.create_station(search_token=self.token)

    @classmethod
    def from_json(cls, api_client, data):
        return super(SearchResultItem, cls).from_json(api_client, data)


class SearchResult(PandoraModel):

    nearest_matches_available = Field("nearMatchesAvailable")
    explanation = Field("explanation")
    songs = Field("songs", model=SongSearchResultItem)
    artists = Field("artists", model=ArtistSearchResultItem)
    genre_stations = Field("genreStations", model=GenreStationSearchResultItem)
