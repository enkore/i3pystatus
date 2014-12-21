import unittest


from i3pystatus.core.modules import Module


class CallbacksMetaTest(unittest.TestCase):

    valid_msg_count = "hello world"
    notmuch_config = "notmuch-config"

    @staticmethod
    def send_clicks(module):
        # simulate click events for buttons 1 to 10
        for button in range(1, 10):
            module.on_click(button)

    class NoDefaultCounter(Module):

        counter = 0

        def update_counter(self, step=1):
            self.counter = self.counter + step

    class WithDefaultsCounter(NoDefaultCounter):
        on_leftclick = "update_counter"
        on_rightclick = ["update_counter", 2]
        on_upscroll = ["callable_callback", "i3 is", "awesome"]
        on_downscroll = ["update_counter", -1]

    def test_count_is_correct(self):
        """Checks module works in the intended way, ie increase correctly
        a counter"""
        counter = self.NoDefaultCounter()
        self.assertEqual(counter.counter, 0)
        counter.update_counter(1)
        self.assertEqual(counter.counter, 1)
        counter.update_counter(2)
        self.assertEqual(counter.counter, 3)
        counter.update_counter(-2)
        self.assertEqual(counter.counter, 1)

        CallbacksMetaTest.send_clicks(counter)

        # retcode, out, err = run_through_shell("notmuch --config=%s new" % (self.notmuch_config), enable_shell=True)

        # self.assertEqual(out.strip(), self.valid_output)
    def test_callback_set_post_instanciation(self):

        counter = self.NoDefaultCounter()

        # set callbacks
        counter.on_leftclick = "update_counter"
        counter.on_rightclick = ["update_counter", 2]
        counter.on_upscroll = [print, "i3 is", "awesome"]
        counter.on_downscroll = ["update_counter", -1]

        self.assertEqual(counter.counter, 0)
        counter.on_click(1)  # left_click
        self.assertEqual(counter.counter, 1)
        counter.on_click(2)  # middle button
        self.assertEqual(counter.counter, 1)
        counter.on_click(3)  # right click
        self.assertEqual(counter.counter, 3)
        counter.on_click(4)  # upscroll
        self.assertEqual(counter.counter, 3)
        counter.on_click(5)  # downscroll
        self.assertEqual(counter.counter, 2)
