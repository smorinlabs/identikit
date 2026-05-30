"""Tests for identikit.marker — the one-shot init record."""

from __future__ import annotations

from identikit import marker


def test_write_then_read_round_trips(tmp_path):
    answers = {"package_name": "payments_api", "owner": "acme"}
    marker.write_marker(tmp_path, answers, version="0.1.0", date="2026-05-29")
    assert marker.marker_exists(tmp_path)
    data = marker.read_marker(tmp_path)
    assert data["answers"] == answers
    assert data["meta"]["version"] == "0.1.0"
    assert data["meta"]["date"] == "2026-05-29"


def test_marker_absent_reads_none(tmp_path):
    assert not marker.marker_exists(tmp_path)
    assert marker.read_marker(tmp_path) is None
