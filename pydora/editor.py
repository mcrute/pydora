import os
import sys
from pandora import clientbuilder

from .utils import Screen


class EditorApp(object):
    def __init__(self):
        self.client = None
        self.screen = Screen()

    def get_client(self):
        cfg_file = os.environ.get("PYDORA_CFG", "")
        builder = clientbuilder.PydoraConfigFileBuilder(cfg_file)
        if builder.file_exists:
            return builder.build()

        builder = clientbuilder.PianobarConfigFileBuilder()
        if builder.file_exists:
            return builder.build()

        if not self.client:
            self.screen.print_error("No valid config found")
            sys.exit(1)

    # Search (music.search)
    # Create Station (station.createStation)
    # List Stations (user.getStationList)
    # Describe Station (station.getStation)
    # - View Info
    # - View Feedback
    # - View Seeds
    # - Get Share Link
    # Modify Station
    # - Change Name (station.renameStation)
    # - Change Description (???)
    # - Remove Feedback (station.deleteFeedback)
    # - Add Seed (station.addMusic)
    # - Remove Seed (station.deleteMusic)
    # - Enable/Disable Artist Messages (???)
    # Delete Station
    # List Feedback
    # List Bookmarks (Album, Track, Artist) (user.getBookmarks)
    # Delete Bookmarks
    #   (bookmark.deleteArtistBookmark, bookmark.deleteSongBookmark)
    def run(self):
        self.client = self.get_client()


def main():
    EditorApp().run()
