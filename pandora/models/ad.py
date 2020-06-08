from ..errors import ParameterMissing
from ._base import Field
from .playlist import PlaylistModel, AudioField


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
            raise ParameterMissing(
                "No ad tracking tokens provided for registration."
            )

    def prepare_playback(self):
        try:
            self.register_ad(self.station_id)
        except ParameterMissing as exc:
            if self.tracking_tokens:
                raise exc
        return super().prepare_playback()

    def thumbs_up(self):
        return

    def thumbs_down(self):
        return

    def bookmark_song(self):
        return

    def bookmark_artist(self):
        return

    def sleep(self):
        return
