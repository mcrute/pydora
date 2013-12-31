from . import Field, PandoraModel


class Station(PandoraModel):

    can_add_music = Field('allowAddMusic', False)
    can_delete = Field('allowDelete', True)
    can_rename = Field('allowRename', True)
    is_shared = Field('isShared', False)

    art_url = Field('artUrl')
    date_created = Field('dateCreated', formatter=PandoraModel.json_to_date)
    detail_url = Field('stationDetailUrl')
    id = Field('stationId')
    name = Field('stationName')
    sharing_url = Field('stationSharingUrl')
    token = Field('stationToken')

    genre = Field('genre', [])
    quickmix_stations = Field('quickMixStationIds', [])

    def get_playlist(self):
        for station in self._api_client.get_playlist(self.token)['items']:
            yield PlaylistItem.from_json(self._api_client, station)


class PlaylistItem(PandoraModel):

    artist_name = Field('artistName')
    album_name = Field('albumName')
    song_name = Field('songName')
    song_rating = Field('songRating')
    track_gain = Field('trackGain')
    track_token = Field('trackToken')
    audio_url = Field('audioUrl')
    album_art_url = Field('albumArtUrl')
    allow_feedback = Field('allowFeedback', True)
    station_id = Field('stationId')

    album_detail_url = Field('albumDetailUrl')
    album_explore_url = Field('albumExplorerUrl')

    amazon_album_asin = Field('amazonAlbumAsin')
    amazon_album_digital_asin = Field('amazonAlbumDigitalAsin')
    amazon_album_url = Field('amazonAlbumUrl')
    amazon_song_digital_asin = Field('amazonSongDigitalAsin')

    artist_detail_url = Field('artistDetailUrl')
    artist_explore_url = Field('artistExplorerUrl')

    itunes_song_url = Field('itunesSongUrl')

    song_detail_url = Field('songDetailUrl')
    song_explore_url = Field('songExplorerUrl')

    def thumbs_up(self):
        self._api_client.add_feedback(self.track_token, True)

    def thumbs_down(self):
        self._api_client.add_feedback(self.track_token, False)

    def bookmark_song(self):
        self._api_client.add_song_bookmark(self.track_token)

    def bookmark_artist(self):
        self._api_client.add_artist_bookmark(self.track_token)

    def sleep(self):
        self._api_client.sleep_song(self.track_token)


class Bookmark(PandoraModel):

    music_token = Field('musicToken')
    artist_name = Field('artistName')
    art_url = Field('artUrl')
    bookmark_token = Field('bookmarkToken')
    date_created = Field('dateCreated', formatter=PandoraModel.json_to_date)

    # song only
    sample_url = Field('sampleUrl')
    sample_gain = Field('sampleGain')
    album_name = Field('albumName')
    song_name = Field('songName')

    @property
    def is_song_bookmark(self):
        return self.song_name is not None

    def delete(self):
        if self.is_song_bookmark:
            self._api_client.delete_song_bookmark(self.bookmark_token)
        else:
            self._api_client.delete_artist_bookmark(self.bookmark_token)
