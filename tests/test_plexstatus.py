"""
Basic test for the plexstatus module
"""

import unittest
from mock import patch
from unittest.mock import MagicMock
from urllib.request import urlopen
from i3pystatus import plexstatus

# inline xml of stream info from plex server
STREAM = b'''<?xml version="1.0" encoding="UTF-8"?>
<MediaContainer size="1">
  <Video addedAt="1421001383" art="/library/metadata/46/art/1454407842" chapterSource="" contentRating="G" duration="596462" guid="com.plexapp.agents.themoviedb://10378?lang=en" key="/library/metadata/46" librarySectionID="1" originallyAvailableAt="2008-04-10" rating="6.7" ratingKey="46" sessionKey="146" studio="Blender Foundation" summary="Follow a day of the life of Big Buck Bunny when he meets three bullying rodents: Frank, Rinky, and Gamera. The rodents amuse themselves by harassing helpless creatures by throwing fruits, nuts and rocks at them. After the deaths of two of Bunny&apos;s favorite butterflies, and an offensive attack on Bunny himself, Bunny sets aside his gentle nature and orchestrates a complex plan for revenge." thumb="/library/metadata/46/thumb/1454407842" title="Big Buck Bunny" type="movie" updatedAt="1454407842" year="2008">
    <Media aspectRatio="1.78" audioChannels="6" audioCodec="aac" audioProfile="lc" bitrate="9725" container="mov" duration="596462" has64bitOffsets="0" height="1080" id="46" optimizedForStreaming="1" videoCodec="h264" videoFrameRate="24p" videoProfile="main" videoResolution="1080" width="1920">
      <Part audioProfile="lc" container="mov" duration="596462" file="Big Buck Bunny.mov" has64bitOffsets="0" id="46" indexes="sd" key="/library/parts/46/file.mov" optimizedForStreaming="1" size="725106140" videoProfile="main">
        <Stream bitDepth="8" bitrate="9283" cabac="0" chromaSubsampling="4:2:0" codec="h264" codecID="avc1" colorRange="tv" colorSpace="bt709" default="1" duration="596458" frameRate="24.000" frameRateMode="cfr" hasScalingMatrix="0" height="1080" id="315" index="0" language="English" languageCode="eng" level="41" pixelFormat="yuv420p" profile="main" refFrames="2" scanType="progressive" streamIdentifier="1" streamType="1" width="1920" />
        <Stream audioChannelLayout="5.1" bitrate="448" bitrateMode="cbr" channels="6" codec="aac" codecID="40" default="1" duration="596462" id="316" index="2" language="English" languageCode="eng" profile="lc" samplingRate="48000" selected="1" streamIdentifier="3" streamType="2" />
      </Part>
    </Media>
    <Genre count="79" id="124" tag="Animation" />
    <Genre count="209" id="177" tag="Comedy" />
    <Director id="894" tag="Sacha Goedegebure" />
    <Producer id="895" tag="Ton Roosendaal" />
    <Country count="2" id="896" tag="Netherlands" />
    <User id="1" thumb="https://plex.tv/users/a111111111a11111/avatar" title="user" />
    <Player address="1.1.1.1" machineIdentifier="1aa1a11a-a1a1-1a1a-111a-1a1aa11a1111" platform="Chrome" product="Plex Web" state="playing" title="Plex Web (Chrome)" />
    <TranscodeSession key="1aaa1a11aaa1aaa111a1aaaa11" throttled="1" progress="24.200000762939453" speed="0" duration="596000" remaining="2155" context="streaming" videoDecision="copy" audioDecision="transcode" protocol="http" container="mkv" videoCodec="h264" audioCodec="aac" audioChannels="2" />
  </Video>
</MediaContainer>'''

class PlexstatusTest(unittest.TestCase):

    @patch('i3pystatus.plexstatus.urlopen', autospec=True)
    def test_not_stream(self, urlopen):
        """
        Test output when nothing is being streamed
        """
        null_stream = b'<?xml version="1.0" encoding="UTF-8"?>\n<MediaContainer size="0">\n</MediaContainer>'
        plexstatus.urlopen.return_value.read.return_value = null_stream
        plxstat = plexstatus.Plexstatus(apikey='111111', address='127.0.0.1')
        plxstat.run()
        self.assertTrue(plxstat.output == {})

    @patch('i3pystatus.plexstatus.urlopen', autospec=True)
    def test_streaming(self, urlopen):
        """
        Test output from side-loaded xml (generated from a real plex server
        response)
        """
        plexstatus.urlopen.return_value.read.return_value = STREAM
        plxstat = plexstatus.Plexstatus(apikey='111111', address='127.0.0.1')
        plxstat.run()
        self.assertTrue(plxstat.output['full_text'] == 'Chrome: Big Buck Bunny')


if __name__ == '__main__':
    unittest.main()
