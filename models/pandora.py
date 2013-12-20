from models import Field, PandoraModel


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
        return self._api_client.get_playlist(self.token)
