import pytest

from i3pystatus import IntervalModule
import time

left_click = 1
right_click = 3
scroll_up = 4
scroll_down = 5


@pytest.mark.parametrize("events, expected", [
    # Fast click
    (((0, left_click),),
     'no action'),

    # Slow click
    (((0.4, left_click),),
     'leftclick'),

    # Slow double click
    (((0.4, left_click),
      (0.4, left_click),),
     'leftclick'),

    # Fast double click
    (((0.2, left_click),
      (0, left_click),),
     'doubleleftclick'),

    # Fast double click + Slow click
    (((0.2, left_click),
      (0, left_click),
      (0.3, left_click),),
     'leftclick'),

    # Alternate double click
    (((0.2, left_click),
      (0, right_click),),
     'leftclick'),

    # Slow click, no callback
    (((0.4, right_click),),
     'no action'),

    # Fast double click
    (((0.2, right_click),
      (0, right_click),),
     'doublerightclick'),

    # Fast double click
    (((0, scroll_down),
      (0, scroll_down),),
     'downscroll'),

    # Slow click
    (((0.4, scroll_up),),
     'upscroll'),

    # Fast double click
    (((0, scroll_up),
      (0, scroll_up),),
     'doubleupscroll'),
])
def test_clicks(events, expected):
    class TestClicks(IntervalModule):
        def set_action(self, action):
            self._action = action

        on_leftclick = [set_action, "leftclick"]
        on_doubleleftclick = [set_action, "doubleleftclick"]

        # on_rightclick = [set_action, "rightclick"]
        on_doublerightclick = [set_action, "doublerightclick"]

        on_upscroll = [set_action, "upscroll"]
        on_doubleupscroll = [set_action, "doubleupscroll"]

        on_downscroll = [set_action, "downscroll"]
        # on_doubledownscroll = [set_action, "doubledownscroll"]

        _action = 'no action'

    # Divide all times by 10 to make the test run faster
    TestClicks.multi_click_timeout /= 10

    m = TestClicks()
    for sl, ev in events:
        m.on_click(ev)
        time.sleep(sl / 10)
    assert m._action == expected
