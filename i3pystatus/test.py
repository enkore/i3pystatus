from i3pystatus import Status
status = Status(standalone=True)
import mpd
status.register(mpd.MPD, format="[({song_elapsed}/{song_length})] [{artist} - ]{title} {status} ♪{volume}", status={"pause": "▷", "play": "▶", "stop": "◾",})
status.run()

