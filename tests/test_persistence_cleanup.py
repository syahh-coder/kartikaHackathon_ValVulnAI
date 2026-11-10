import json
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from scripts import m6b_persistence_check as runner


VOLUME = "valvuln-m6b-check-"+"a"*32


def test_cleanup_rejects_project_volume_without_any_docker_command(monkeypatch):
    def deny(*args):
        raise AssertionError("No Docker operation permitted")
    monkeypatch.setattr(runner, "command", deny)
    assert runner.cleanup("kartikahackathon_lab_data") == "FAIL"


@pytest.mark.parametrize("damage", [None, "label", "name", "timeout"])
def test_cleanup_requires_matching_identity_and_label(monkeypatch, damage):
    calls = []
    def fake(args):
        calls.append(args)
        if args[:2] == ["container", "inspect"]:
            return CompletedProcess(args, 1, b"", b"")
        if args[:2] == ["volume", "inspect"]:
            if damage == "timeout":
                raise TimeoutExpired("docker", 60)
            info = {"Name": "other" if damage == "name" else VOLUME,
                    "Labels": {"com.valvuln.check": "other" if damage == "label" else "m6b-safe-controls"}}
            return CompletedProcess(args, 0, json.dumps([info]).encode(), b"")
        return CompletedProcess(args, 0, b"removed", b"")
    monkeypatch.setattr(runner, "command", fake)
    assert runner.cleanup(VOLUME) == ("PASS" if damage is None else "FAIL")
    assert any(args[:2] == ["volume", "rm"] for args in calls) == (damage is None)
