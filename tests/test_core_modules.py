import time
from unittest.mock import MagicMock

import pytest

from i3pystatus import IntervalModule
from i3pystatus.core.modules import is_method_of

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


@pytest.mark.parametrize("button, stored_value", [
    (left_click, "leftclick"),
    (right_click, "rightclick")
])
def test_callback_handler_method(button, stored_value):
    class TestClicks(IntervalModule):
        def set_action(self, action):
            self._action = action

        on_leftclick = [set_action, "leftclick"]
        on_rightclick = ["set_action", "rightclick"]

    dut = TestClicks()

    dut.on_click(button)
    assert dut._action == stored_value


def test_callback_handler_function():
    callback_mock = MagicMock()

    class TestClicks(IntervalModule):
        on_upscroll = [callback_mock.callback, "upscroll"]

    dut = TestClicks()
    dut.on_click(scroll_up)
    callback_mock.callback.assert_called_once_with("upscroll")


def test_is_method_of():
    class TestClass:
        def method(self):
            pass

        # member assigned functions cannot be distinguished in unbound state
        # by principle from methods, since both are functions. However, in
        # most cases it can still be shown correctly that a member assigned
        # function is not a method, since the member name and function name
        # are different (in this example the assigned member is 'assigned_function',
        # while the name of the function is 'len', hence is_method_of can say for
        # sure that assigned_function isn't a method
        assigned_function = len
        member = 1234
        string_member = "abcd"

    object = TestClass()
    for source_object in [object, TestClass]:
        assert is_method_of(source_object.method, object)
        assert not is_method_of(source_object.assigned_function, object)
        assert not is_method_of(source_object.member, object)
        assert not is_method_of(source_object.string_member, object)
