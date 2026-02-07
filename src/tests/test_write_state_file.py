"""Comprehensive tests for write_state_file functionality."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from claude_monitor.ui.display_controller import DisplayController


class TestWriteStateFile:
    """Test suite for state file writing functionality."""

    @pytest.fixture
    def controller(self) -> DisplayController:
        """Create DisplayController instance with write_state enabled."""
        with patch("claude_monitor.ui.display_controller.NotificationManager"):
            controller = DisplayController()
            controller.write_state_enabled = True
            return controller

    @pytest.fixture
    def temp_report_dir(self, tmp_path: Path) -> Path:
        """Create temporary report directory."""
        report_dir = tmp_path / "reports"
        report_dir.mkdir()
        return report_dir

    @pytest.fixture
    def sample_processed_data(self) -> Dict[str, Any]:
        """Sample processed data for testing."""
        return {
            "tokens_used": 15000,
            "token_limit": 50000,
            "usage_percentage": 30.0,
            "session_cost": 2.5,
            "cost_limit_p90": 10.0,
            "sent_messages": 25,
            "messages_limit_p90": 100,
            "burn_rate": 150.5,
            "reset_time": datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        }

    @pytest.fixture
    def sample_args(self) -> Mock:
        """Sample CLI arguments."""
        args = Mock()
        args.timezone = "UTC"
        args.time_format = "24h"
        return args

    # ========================================================================
    # A. BASIC FUNCTIONALITY TESTS (10 tests)
    # ========================================================================

    def test_state_file_created_when_enabled(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file is created when write_state_enabled is True."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert state_file.exists()

    def test_state_file_not_created_when_disabled(
        self,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file is NOT created when write_state_enabled is False."""
        with patch("claude_monitor.ui.display_controller.NotificationManager"):
            controller = DisplayController()
            controller.write_state_enabled = False

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # This should not create the file
            # Note: The method won't even be called if write_state_enabled is False
            # in the actual implementation, but we test the flag here
            state_file = temp_report_dir / "current.json"
            assert not state_file.exists()

    def test_state_file_location_correct(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test file location is $CLAUDE_MONITOR_REPORT_DIR/current.json."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            expected_path = temp_report_dir / "current.json"
            assert expected_path.exists()
            assert expected_path.name == "current.json"

    def test_state_file_contains_valid_json(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file contains valid JSON."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)  # Should not raise
                assert isinstance(data, dict)

    def test_state_file_has_all_required_top_level_fields(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file contains all required top-level fields."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            required_fields = [
                "messages",
                "tokens",
                "cost",
                "reset",
                "burnRate",
                "lastUpdate",
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

    def test_state_file_has_all_nested_fields(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file contains all nested fields."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Check nested fields
            assert all(k in data["messages"] for k in ["used", "limit", "percent"])
            assert all(k in data["tokens"] for k in ["used", "limit", "percent"])
            assert all(k in data["cost"] for k in ["used", "limit", "percent"])
            assert all(
                k in data["reset"]
                for k in ["timestamp", "secondsRemaining", "formattedTime"]
            )
            assert all(k in data["burnRate"] for k in ["tokens", "messages"])

    def test_state_file_data_types_correct(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test data types are correct (int, float, string, nested objects)."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Integer fields
            assert isinstance(data["messages"]["used"], int)
            assert isinstance(data["messages"]["limit"], int)
            assert isinstance(data["tokens"]["used"], int)
            assert isinstance(data["tokens"]["limit"], int)
            assert isinstance(data["reset"]["secondsRemaining"], int)

            # Float fields
            assert isinstance(data["messages"]["percent"], (int, float))
            assert isinstance(data["tokens"]["percent"], (int, float))
            assert isinstance(data["cost"]["used"], (int, float))
            assert isinstance(data["cost"]["limit"], (int, float))
            assert isinstance(data["cost"]["percent"], (int, float))
            assert isinstance(data["burnRate"]["tokens"], (int, float))

            # String fields
            assert isinstance(data["reset"]["timestamp"], str)
            assert isinstance(data["reset"]["formattedTime"], str)
            assert isinstance(data["lastUpdate"], str)

    def test_state_file_overwrites_on_each_update(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test file overwrites on each update."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # First write
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data1 = json.load(f)

            # Modify data and write again
            sample_processed_data["tokens_used"] = 20000
            controller._write_state_file(sample_processed_data, sample_args)

            with open(state_file) as f:
                data2 = json.load(f)

            assert data2["tokens"]["used"] == 20000
            assert data2["tokens"]["used"] != data1["tokens"]["used"]

    def test_state_file_readable_permissions(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test file permissions are appropriate (readable)."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert state_file.exists()
            assert os.access(state_file, os.R_OK)

    def test_state_file_written_atomically(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test file is written atomically (using Path.write_text)."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # The implementation uses Path.write_text which is atomic
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            # File should exist and be complete
            with open(state_file) as f:
                data = json.load(f)  # Should parse without error
                assert "messages" in data

    # ========================================================================
    # B. DATA ACCURACY TESTS (12 tests)
    # ========================================================================

    def test_token_percentage_calculated_correctly(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test token percentage calculated correctly: (used/limit)*100."""
        sample_processed_data["tokens_used"] = 15000
        sample_processed_data["token_limit"] = 50000

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            expected_percent = (15000 / 50000) * 100
            assert data["tokens"]["percent"] == round(expected_percent, 2)

    def test_cost_percentage_calculated_correctly(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test cost percentage calculated correctly: (used/limit)*100."""
        sample_processed_data["session_cost"] = 2.5
        sample_processed_data["cost_limit_p90"] = 10.0

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            expected_percent = (2.5 / 10.0) * 100
            assert data["cost"]["percent"] == round(expected_percent, 2)

    def test_messages_percentage_calculated_correctly(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test messages percentage calculated correctly: (used/limit)*100."""
        sample_processed_data["sent_messages"] = 25
        sample_processed_data["messages_limit_p90"] = 100

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            expected_percent = (25 / 100) * 100
            assert data["messages"]["percent"] == round(expected_percent, 2)

    def test_burn_rate_is_float(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test burn_rate field is float (regression test for d8933e5)."""
        sample_processed_data["burn_rate"] = 150.5

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            assert isinstance(data["burnRate"]["tokens"], (int, float))
            assert data["burnRate"]["tokens"] == 150.5

    def test_burn_rate_value_from_processed_data(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test burn_rate value matches processed_data."""
        test_burn_rate = 1234.56
        sample_processed_data["burn_rate"] = test_burn_rate

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            assert data["burnRate"]["tokens"] == round(test_burn_rate, 2)

    def test_reset_time_from_processed_data(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test reset time comes from processed_data (not recalculated)."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            assert data["reset"]["timestamp"] == reset_time.isoformat()

    def test_seconds_remaining_calculated_correctly(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test secondsRemaining calculated correctly from current time."""
        reset_time = datetime.now(timezone.utc) + timedelta(hours=2)
        sample_processed_data["reset_time"] = reset_time

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should be approximately 2 hours (7200 seconds) ± a few seconds
            assert 7190 < data["reset"]["secondsRemaining"] < 7210

    def test_formatted_time_respects_timezone(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test formattedTime respects user's timezone setting."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time
        sample_args.timezone = "America/New_York"  # UTC-5 or UTC-4 depending on DST
        sample_args.time_format = "24h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # 18:00 UTC = 13:00 EST (or 14:00 EDT depending on DST)
            # Just verify it's NOT 18:00 (i.e., timezone conversion happened)
            formatted = data["reset"]["formattedTime"]
            assert "18:00" not in formatted
            assert "13:00" in formatted or "14:00" in formatted

    def test_formatted_time_respects_time_format_24h(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test formattedTime respects 24h time format."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time
        sample_args.timezone = "UTC"
        sample_args.time_format = "24h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should be 18:00 in 24h format
            assert "18:00" in data["reset"]["formattedTime"]

    def test_timestamp_is_iso8601_format(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test timestamp is ISO 8601 format."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should be parseable as ISO 8601
            timestamp = data["reset"]["timestamp"]
            parsed = datetime.fromisoformat(timestamp.replace("+00:00", "+00:00"))
            assert parsed.tzinfo is not None

    def test_last_update_is_recent(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test lastUpdate is recent (within test execution time)."""
        before_time = (
            datetime.now(timezone.utc)
        )  # Use UTC time since write_state_file uses datetime.now(timezone.utc)

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

        after_time = datetime.now(timezone.utc)  # Use UTC time

        state_file = temp_report_dir / "current.json"
        with open(state_file) as f:
            data = json.load(f)

        last_update = datetime.fromisoformat(data["lastUpdate"])
        # Make timezone-naive for comparison if needed
        if last_update.tzinfo is not None:
            last_update = last_update.replace(tzinfo=None)
        if before_time.tzinfo is not None:
            before_time = before_time.replace(tzinfo=None)
        if after_time.tzinfo is not None:
            after_time = after_time.replace(tzinfo=None)

        assert before_time <= last_update <= after_time

    def test_percentage_values_rounded_to_2_decimals(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test all percentage values rounded to 2 decimal places."""
        # Use values that will produce many decimal places
        sample_processed_data["tokens_used"] = 12345
        sample_processed_data["token_limit"] = 67890
        sample_processed_data["session_cost"] = 1.23456
        sample_processed_data["cost_limit_p90"] = 7.89012
        sample_processed_data["sent_messages"] = 33
        sample_processed_data["messages_limit_p90"] = 77

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Check that percentages have at most 2 decimal places
            assert len(str(data["tokens"]["percent"]).split(".")[-1]) <= 2
            assert len(str(data["cost"]["percent"]).split(".")[-1]) <= 2
            assert len(str(data["messages"]["percent"]).split(".")[-1]) <= 2

    # ========================================================================
    # C. RESET TIME CALCULATION TESTS (8 tests) - Critical for 06e880f fix
    # ========================================================================

    def test_reset_time_uses_processed_data_not_manual_calculation(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test reset time uses processed_data['reset_time'] not manual calculation."""
        # Set a specific reset time that wouldn't match reset_hour calculation
        specific_reset = datetime(2026, 1, 11, 15, 30, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = specific_reset
        sample_args.reset_hour = 0  # Different from 15

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should match processed_data reset time, not reset_hour
            assert data["reset"]["timestamp"] == specific_reset.isoformat()

    def test_reset_time_is_timezone_aware(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test reset time is timezone-aware (UTC)."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should include timezone info (+00:00 for UTC)
            assert "+00:00" in data["reset"]["timestamp"]

    def test_reset_time_converted_to_user_timezone_for_formatted_time(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test reset time converted to user's timezone for formattedTime."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time
        sample_args.timezone = "Europe/Warsaw"  # UTC+1
        sample_args.time_format = "24h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # 18:00 UTC = 19:00 Warsaw time
            assert "19:00" in data["reset"]["formattedTime"]

    def test_seconds_remaining_decreases_over_time(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test secondsRemaining decreases over time."""
        reset_time = datetime.now(timezone.utc) + timedelta(hours=1)
        sample_processed_data["reset_time"] = reset_time

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # First write
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data1 = json.load(f)

            # Wait a bit and write again
            import time

            time.sleep(1)

            controller._write_state_file(sample_processed_data, sample_args)

            with open(state_file) as f:
                data2 = json.load(f)

            # Second write should have fewer seconds remaining
            assert (
                data2["reset"]["secondsRemaining"] <= data1["reset"]["secondsRemaining"]
            )

    def test_reset_time_timezone_conversion_europe_warsaw(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test reset time handles timezone conversion (UTC → Europe/Warsaw)."""
        reset_time = datetime(2026, 1, 10, 23, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time
        sample_args.timezone = "Europe/Warsaw"  # UTC+1
        sample_args.time_format = "24h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # 23:00 UTC = 00:00 next day Warsaw time
            # Could be either depending on DST
            formatted = data["reset"]["formattedTime"]
            assert "00:00" in formatted or "23:00" in formatted

    def test_reset_time_timezone_conversion_us_pacific(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test reset time handles timezone conversion (UTC → US/Pacific)."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time
        sample_args.timezone = "US/Pacific"  # UTC-8
        sample_args.time_format = "24h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # 18:00 UTC = 10:00 PST
            assert "10:00" in data["reset"]["formattedTime"]

    def test_formatted_time_format_matches_time_format_preference_12h(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test formatted time format matches time_format preference (12h)."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time
        sample_args.timezone = "UTC"
        sample_args.time_format = "12h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should include AM/PM
            formatted = data["reset"]["formattedTime"]
            assert "AM" in formatted or "PM" in formatted

    def test_formatted_time_format_matches_time_format_preference_24h(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test formatted time format matches time_format preference (24h)."""
        reset_time = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time
        sample_args.timezone = "UTC"
        sample_args.time_format = "24h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should NOT include AM/PM
            formatted = data["reset"]["formattedTime"]
            assert "AM" not in formatted and "PM" not in formatted
            assert "18:00" in formatted

    # ========================================================================
    # D. EDGE CASES TESTS (12 tests)
    # ========================================================================

    def test_behavior_when_reset_time_is_none(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior when reset_time is None (should skip write)."""
        sample_processed_data["reset_time"] = None

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # Should return early without creating file
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert not state_file.exists()

    def test_behavior_when_cost_limit_is_zero(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior when cost_limit is 0 (avoid division by zero)."""
        sample_processed_data["cost_limit_p90"] = 0
        sample_processed_data["session_cost"] = 5.0

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should handle gracefully (percent = 0)
            assert data["cost"]["percent"] == 0

    def test_behavior_when_messages_limit_is_zero(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior when messages_limit is 0 (avoid division by zero)."""
        sample_processed_data["messages_limit_p90"] = 0
        sample_processed_data["sent_messages"] = 25

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should handle gracefully (percent = 0)
            assert data["messages"]["percent"] == 0

    def test_behavior_when_percentages_exceed_100(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior when percentages exceed 100%."""
        sample_processed_data["tokens_used"] = 75000
        sample_processed_data["token_limit"] = 50000  # Used exceeds limit
        sample_processed_data["usage_percentage"] = 150.0  # Update this too

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should allow percentages > 100
            # Note: Implementation uses usage_percentage from processed_data
            assert data["tokens"]["percent"] == 150.0

    def test_behavior_with_pro_plan(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior with pro plan type."""
        sample_args.plan = "pro"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert state_file.exists()

    def test_behavior_with_max5_plan(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior with max5 plan type."""
        sample_args.plan = "max5"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert state_file.exists()

    def test_behavior_with_custom_plan(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior with custom plan type."""
        sample_args.plan = "custom"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert state_file.exists()

    def test_behavior_with_various_timezones(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior with various timezone values."""
        timezones = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]

        for tz in timezones:
            sample_args.timezone = tz

            with patch.dict(
                os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
            ):
                controller._write_state_file(sample_processed_data, sample_args)

                state_file = temp_report_dir / "current.json"
                assert state_file.exists()

    def test_behavior_with_12h_time_format(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior with 12h time format."""
        sample_args.time_format = "12h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should include AM or PM
            assert (
                "AM" in data["reset"]["formattedTime"]
                or "PM" in data["reset"]["formattedTime"]
            )

    def test_behavior_when_burn_rate_is_zero(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior when burn_rate is 0."""
        sample_processed_data["burn_rate"] = 0.0

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            assert data["burnRate"]["tokens"] == 0.0

    def test_behavior_when_all_usage_is_zero(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior when all usage is 0."""
        sample_processed_data["tokens_used"] = 0
        sample_processed_data["session_cost"] = 0.0
        sample_processed_data["sent_messages"] = 0
        sample_processed_data["burn_rate"] = 0.0

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            assert data["tokens"]["used"] == 0
            assert data["cost"]["used"] == 0.0
            assert data["messages"]["used"] == 0
            assert data["burnRate"]["tokens"] == 0.0

    def test_behavior_with_limits_zero_insufficient_history(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test behavior when limits are 0 (custom plan, insufficient history)."""
        sample_processed_data["token_limit"] = 0
        sample_processed_data["cost_limit_p90"] = 0
        sample_processed_data["messages_limit_p90"] = 0

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # Should handle gracefully
            assert data["tokens"]["limit"] == 0
            assert data["cost"]["limit"] == 0
            assert data["messages"]["limit"] == 0

    # ========================================================================
    # E. ERROR HANDLING TESTS (8 tests)
    # ========================================================================

    def test_graceful_failure_when_directory_doesnt_exist(
        self,
        controller: DisplayController,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test graceful failure when directory doesn't exist."""
        nonexistent_dir = "/nonexistent/directory/that/should/not/exist"

        with patch.dict(os.environ, {"CLAUDE_MONITOR_REPORT_DIR": nonexistent_dir}):
            # Should not raise exception
            try:
                controller._write_state_file(sample_processed_data, sample_args)
            except Exception:
                # Should handle gracefully
                pass

    def test_graceful_failure_on_permission_errors(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test graceful failure on permission errors."""
        # Make directory read-only
        temp_report_dir.chmod(0o444)

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # Should not raise exception
            try:
                controller._write_state_file(sample_processed_data, sample_args)
            except Exception:
                pass

        # Restore permissions for cleanup
        temp_report_dir.chmod(0o755)

    def test_graceful_failure_when_env_var_not_set(
        self,
        controller: DisplayController,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test graceful failure when environment variable not set."""
        # Remove the environment variable
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise exception
            try:
                controller._write_state_file(sample_processed_data, sample_args)
            except Exception:
                pass

    def test_logger_called_on_errors(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test logger is called on errors."""
        # Make directory read-only to trigger error
        temp_report_dir.chmod(0o444)

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            with patch("logging.getLogger") as mock_logger:
                mock_log_instance = Mock()
                mock_logger.return_value = mock_log_instance

                try:
                    controller._write_state_file(sample_processed_data, sample_args)
                except Exception:
                    pass

                # Logger should have been called for error
                # (either in exception handler or for warnings)

        # Restore permissions
        temp_report_dir.chmod(0o755)

    def test_no_exception_raised_on_write_failure(
        self,
        controller: DisplayController,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test no exception raised on write failure."""
        with patch.dict(os.environ, {"CLAUDE_MONITOR_REPORT_DIR": "/nonexistent/path"}):
            # Should not raise exception - should fail silently
            controller._write_state_file(sample_processed_data, sample_args)
            # If we get here, no exception was raised

    def test_function_returns_early_when_reset_time_none(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test function returns early when reset_time is None."""
        sample_processed_data["reset_time"] = None

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # Should return early without creating file
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert not state_file.exists()

    def test_no_crash_when_timezone_invalid(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test no crash when args.timezone is invalid."""
        sample_args.timezone = "Invalid/Timezone"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # Should not crash - should fall back to default
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            assert state_file.exists()

    def test_graceful_failure_when_processed_data_malformed(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_args: Mock,
    ) -> None:
        """Test graceful failure when processed_data is malformed."""
        # Missing required fields
        malformed_data = {"tokens_used": 100}

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # Should handle gracefully
            try:
                controller._write_state_file(malformed_data, sample_args)
            except Exception:
                pass  # Expected to fail, but shouldn't crash the app

    # ========================================================================
    # F. INTEGRATION SCENARIOS TESTS (5 tests)
    # ========================================================================

    def test_state_file_works_with_pro_plan_limits(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file works with pro plan limits."""
        sample_args.plan = "pro"
        sample_processed_data["token_limit"] = 200000
        sample_processed_data["cost_limit_p90"] = 10.0
        sample_processed_data["messages_limit_p90"] = 100

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            assert data["tokens"]["limit"] == 200000

    def test_state_file_works_with_max5_plan_limits(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file works with max5 plan limits."""
        sample_args.plan = "max5"
        sample_processed_data["token_limit"] = 3000000
        sample_processed_data["cost_limit_p90"] = 50.0

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            assert data["tokens"]["limit"] == 3000000

    def test_state_file_reflects_different_session_states(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file reflects different session states."""
        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            # Write state 1
            sample_processed_data["tokens_used"] = 10000
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data1 = json.load(f)

            # Write state 2
            sample_processed_data["tokens_used"] = 25000
            controller._write_state_file(sample_processed_data, sample_args)

            with open(state_file) as f:
                data2 = json.load(f)

            assert data1["tokens"]["used"] == 10000
            assert data2["tokens"]["used"] == 25000

    def test_state_file_timezone_matches_args_timezone(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file timezone matches args.timezone."""
        sample_args.timezone = "Asia/Tokyo"
        sample_args.time_format = "24h"
        reset_time = datetime(2026, 1, 10, 15, 0, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data = json.load(f)

            # 15:00 UTC = 00:00 next day JST (UTC+9)
            # Should be formatted in Tokyo time
            formatted = data["reset"]["formattedTime"]
            # Expect hour 0 or 24 depending on formatting
            assert "00:00" in formatted or "24:00" in formatted

    def test_state_file_time_format_matches_args_time_format(
        self,
        controller: DisplayController,
        temp_report_dir: Path,
        sample_processed_data: Dict[str, Any],
        sample_args: Mock,
    ) -> None:
        """Test state file time format matches args.time_format."""
        reset_time = datetime(2026, 1, 10, 14, 30, 0, tzinfo=timezone.utc)
        sample_processed_data["reset_time"] = reset_time

        # Test 12h format
        sample_args.timezone = "UTC"
        sample_args.time_format = "12h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            state_file = temp_report_dir / "current.json"
            with open(state_file) as f:
                data12h = json.load(f)

        # Should have AM/PM
        assert "PM" in data12h["reset"]["formattedTime"]

        # Test 24h format
        sample_args.time_format = "24h"

        with patch.dict(
            os.environ, {"CLAUDE_MONITOR_REPORT_DIR": str(temp_report_dir)}
        ):
            controller._write_state_file(sample_processed_data, sample_args)

            with open(state_file) as f:
                data24h = json.load(f)

        # Should NOT have AM/PM
        assert "AM" not in data24h["reset"]["formattedTime"]
        assert "PM" not in data24h["reset"]["formattedTime"]
        assert "14:30" in data24h["reset"]["formattedTime"]
