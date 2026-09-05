"""The Neovim provider seam: socket listing and the launch command line."""

from __future__ import annotations

from pathlib import Path

from dovetail_seams.editor import launch_argv, list_instances, socket_directory


class TestSocketDirectory:
    def test_the_documented_path(self):
        assert socket_directory({"XDG_RUNTIME_DIR": "/run/user/1000"}) == Path(
            "/run/user/1000/dovetail"
        )

    def test_no_runtime_directory_is_no_directory(self):
        assert socket_directory({}) is None


class TestListInstances:
    def test_reads_the_pid_out_of_each_socket_name(self, tmp_path):
        directory = tmp_path / "dovetail"
        directory.mkdir()
        (directory / "nvim-140.sock").touch()
        (directory / "nvim-1500.sock").touch()
        # Anything that is not the documented scheme is not an instance.
        (directory / "notes.txt").touch()
        (directory / "nvim-.sock").touch()

        found = list_instances({"XDG_RUNTIME_DIR": str(tmp_path)})
        assert {instance.pid for instance in found} == {140, 1500}
        assert all(instance.socket.startswith(str(directory)) for instance in found)

    def test_a_missing_directory_is_no_instances(self, tmp_path):
        assert list_instances({"XDG_RUNTIME_DIR": str(tmp_path)}) == []


class TestLaunchArgv:
    def test_just_the_file(self):
        assert launch_argv("nvim", Path("/home/resident/notes.md"), None) == [
            "nvim",
            "/home/resident/notes.md",
        ]

    def test_with_a_line(self):
        assert launch_argv("nvim", Path("/home/resident/notes.md"), 42) == [
            "nvim",
            "+42",
            "/home/resident/notes.md",
        ]
