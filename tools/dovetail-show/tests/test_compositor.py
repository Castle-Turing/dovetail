"""Reading Sway's window-event stream."""

from __future__ import annotations

from dovetail_show.compositor import _SwayWindowWatch, detect


class TestDetect:
    def test_no_swaysock_is_no_compositor(self):
        assert detect({}) is None


class TestEventDecoding:
    def _watch(self, text):
        watch = _SwayWindowWatch("swaymsg")
        watch._buffer = text
        return watch

    def test_one_event_per_line(self):
        watch = self._watch('{"change":"new"}\n{"change":"close"}\n')
        assert [event["change"] for event in watch._drain()] == ["new", "close"]

    def test_pretty_printed_events_decode_too(self):
        # Whether a given swaymsg pretty-prints is not worth depending on.
        watch = self._watch('{\n  "change": "new"\n}\n{\n  "change": "focus"\n}\n')
        assert [event["change"] for event in watch._drain()] == ["new", "focus"]

    def test_a_partial_event_is_left_in_the_buffer(self):
        watch = self._watch('{"change":"new"}\n{"change":"clo')
        assert [event["change"] for event in watch._drain()] == ["new"]
        assert watch._buffer == '{"change":"clo'


class TestSubscriptionAcknowledgement:
    """The subscription is not live until Sway says it is.

    Starting `swaymsg -t subscribe` only starts a process. A window that
    maps before Sway has processed the request is never reported, and the
    launch path spawns a terminal immediately after subscribing — so the
    watch waits for the `{"success": true}` reply before returning.
    """

    def _watch(self, text):
        watch = _SwayWindowWatch("swaymsg")
        watch._buffer = text
        return watch

    def test_the_reply_is_consumed_not_treated_as_an_event(self):
        watch = self._watch('{"success":true}\n')
        assert watch._await_acknowledgement(0.0) is True
        assert watch._pending == []

    def test_a_refused_subscription_is_not_acknowledged(self):
        watch = self._watch('{"success":false}\n')
        assert watch._await_acknowledgement(0.0) is False

    def test_events_arriving_with_the_reply_are_kept(self):
        # A window can map between the request and our first read, so the
        # reply and its first events can land in one chunk. Dropping them
        # here would reintroduce the race the acknowledgement closes.
        watch = self._watch('{"success":true}\n{"change":"new","container":{"pid":42,"id":7}}\n')
        assert watch._await_acknowledgement(0.0) is True
        assert [event["change"] for event in watch._pending] == ["new"]
