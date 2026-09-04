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
