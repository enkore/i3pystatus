"""
Basic test for the plexstatus module
"""

import unittest
from unittest.mock import patch, MagicMock
from urllib.request import urlopen
from i3pystatus import lastfm

# inline json of stream info from last.fm APIs
ACTIVE_CONTENT = b'''{"recenttracks":{"track":[{"artist":{"#text":"Tuomas Holopainen","mbid":"ae4c7a2c-fb0f-4bfd-a9be-c815d00030b8"},"name":"The Last Sled","streamable":"0","mbid":"61739f28-42ab-4f5c-88ca-69715fb9f96b","album":{"#text":"Music Inspired by the Life and Times of Scrooge","mbid":"da39ccaf-10af-40c1-a49c-c8ebb95adb2c"},"url":"http://www.last.fm/music/Tuomas+Holopainen/_/The+Last+Sled","image":[{"#text":"http://img2-ak.lst.fm/i/u/34s/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"small"},{"#text":"http://img2-ak.lst.fm/i/u/64s/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"medium"},{"#text":"http://img2-ak.lst.fm/i/u/174s/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"large"},{"#text":"http://img2-ak.lst.fm/i/u/300x300/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"extralarge"}],"@attr":{"nowplaying":"true"}},{"artist":{"#text":"Gungor","mbid":"f68ad842-13b9-4302-8eeb-ade8af70ce96"},"name":"Beautiful Things","streamable":"0","mbid":"f8f52d8f-f934-41ed-92dc-2ea81e708393","album":{"#text":"Beautiful Things","mbid":"f054aca4-b472-42d2-984b-9c52f75da83a"},"url":"http://www.last.fm/music/Gungor/_/Beautiful+Things","image":[{"#text":"http://img2-ak.lst.fm/i/u/34s/e8ba0f40c87040599f1680f04a002d31.png","size":"small"},{"#text":"http://img2-ak.lst.fm/i/u/64s/e8ba0f40c87040599f1680f04a002d31.png","size":"medium"},{"#text":"http://img2-ak.lst.fm/i/u/174s/e8ba0f40c87040599f1680f04a002d31.png","size":"large"},{"#text":"http://img2-ak.lst.fm/i/u/300x300/e8ba0f40c87040599f1680f04a002d31.png","size":"extralarge"}],"date":{"uts":"1458168739","#text":"16 Mar 2016, 22:52"}}],"@attr":{"user":"drwahl","page":"1","perPage":"1","totalPages":"15018","total":"15018"}}}'''

INACTIVE_CONTENT = b'''{"recenttracks":{"track":[{"artist":{"#text":"Tuomas Holopainen","mbid":"ae4c7a2c-fb0f-4bfd-a9be-c815d00030b8"},"name":"The Last Sled","streamable":"0","mbid":"61739f28-42ab-4f5c-88ca-69715fb9f96b","album":{"#text":"Music Inspired by the Life and Times of Scrooge","mbid":"da39ccaf-10af-40c1-a49c-c8ebb95adb2c"},"url":"http://www.last.fm/music/Tuomas+Holopainen/_/The+Last+Sled","image":[{"#text":"http://img2-ak.lst.fm/i/u/34s/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"small"},{"#text":"http://img2-ak.lst.fm/i/u/64s/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"medium"},{"#text":"http://img2-ak.lst.fm/i/u/174s/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"large"},{"#text":"http://img2-ak.lst.fm/i/u/300x300/b3efb95e128e427cc25bbf9d97e9f57c.png","size":"extralarge"}],"date":{"uts":"1458169072","#text":"16 Mar 2016, 22:57"}}],"@attr":{"user":"drwahl","page":"1","perPage":"1","totalPages":"15019","total":"15019"}}}'''


class LastFMTest(unittest.TestCase):

    @patch('i3pystatus.lastfm.urlopen', autospec=True)
    def test_not_stream(self, urlopen):
        """
        Test output when no song is being played
        """
        lastfm.urlopen.return_value.read.return_value = INACTIVE_CONTENT
        i3lastfm = lastfm.LastFM(apikey='111111', user='drwahl')
        i3lastfm.run()
        self.assertTrue(i3lastfm.output['full_text'] == i3lastfm.stopped_format)

    @patch('i3pystatus.lastfm.urlopen', autospec=True)
    def test_streaming(self, urlopen):
        """
        Test output when a song is being played
        """
        lastfm.urlopen.return_value.read.return_value = ACTIVE_CONTENT
        i3lastfm = lastfm.LastFM(apikey='111111', user='drwahl')
        i3lastfm.run()
        self.assertTrue(i3lastfm.output['full_text'] == 'Tuomas Holopainen - The Last Sled')


if __name__ == '__main__':
    unittest.main()
