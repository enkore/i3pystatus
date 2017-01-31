from i3pystatus import Status
from i3pystatus.mail import maildir
from i3pystatus.weather import wunderground

status = Status(standalone=True)


status.register("reddit",
                #on_leftclick="google-chrome-stable reddit.com/message/inbox && \
                #i3-msg workspace 1:www",
                username="stay_at_home_daddy",
                format="{comment_karma}"
                )



status.run()
