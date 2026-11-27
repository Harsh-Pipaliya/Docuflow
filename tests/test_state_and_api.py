"""Unit tests for forward-only state guards and API security helpers (offline)."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("EMULATOR_URL", "http://localhost:4588")
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:4588")

from processor_state import begin_attempt
from processor.app import advance


class _FakeSnap:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class ForwardStateTest(unittest.TestCase):
    def test_restart_requires_failed_status(self):
        tx = MagicMock()
        ref = MagicMock()
        ref.get.return_value = _FakeSnap({"status": "Processed", "attempt_count": 1})
        self.assertFalse(begin_attempt.restart.to_wrap(tx, ref, "new-attempt"))
        tx.update.assert_not_called()

    def test_restart_transitions_failed_to_received(self):
        tx = MagicMock()
        ref = MagicMock()
        ref.get.return_value = _FakeSnap({"status": "Failed", "attempt_count": 1})
        self.assertTrue(begin_attempt.restart.to_wrap(tx, ref, "attempt-2"))
        tx.update.assert_called_once()
        tx.set.assert_called_once()

    def test_advance_rejects_stale_attempt_or_wrong_prior_state(self):
        tx = MagicMock()
        ref = MagicMock()
        ref.get.return_value = _FakeSnap(
            {"status": "Processed", "current_attempt_id": "a1"}
        )
        self.assertFalse(
            advance.to_wrap(
                tx, ref, "a1", "Validating", "Validated", "upload-event", {}
            )
        )
        ref.get.return_value = _FakeSnap(
            {"status": "Validating", "current_attempt_id": "a2"}
        )
        self.assertFalse(
            advance.to_wrap(
                tx, ref, "a1", "Validating", "Validated", "upload-event", {}
            )
        )
        tx.update.assert_not_called()

    def test_advance_commits_matching_attempt_and_prior_state(self):
        tx = MagicMock()
        ref = MagicMock()
        ref.get.return_value = _FakeSnap(
            {"status": "Validating", "current_attempt_id": "a1"}
        )
        self.assertTrue(
            advance.to_wrap(
                tx, ref, "a1", "Validating", "Validated", "upload-event", {}
            )
        )
        tx.update.assert_called_once()
        tx.set.assert_called_once()
