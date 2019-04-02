from ._base import PandoraModel, Field, DateField


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
