# Test Coverage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Increase test coverage from 79% to 85%+ (stretch: 95%)

**Architecture:** Add targeted unit tests for uncovered error handling paths, exception branches, and config loading logic.

**Tech Stack:** pytest, unittest.mock, typer.testing.CliRunner

**Linear Ticket:** ENG-3345

---

## Coverage Gap Analysis

| File | Current | Target | Missing Lines |
|------|---------|--------|---------------|
| `cli.py` | 78% | 95%+ | 56-57, 119, 129, 146-151, 160, 175-180, 185-190, 213, 227, 282-283, 308-310, 338-347, 362-363, 374 |
| `git_detector.py` | 62% | 95%+ | 53-58, 68-98, 147 |
| `logging_config.py` | 76% | 95%+ | 47-51, 67 |
| `dependencies.py` | 81% | 95%+ | 28-31 |
| `collector.py` | 97% | 100% | 96-97 |

---

## Task 1: Test version_callback in CLI

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/hermod/test_cli.py`:

```python
def test_version_flag_shows_version():
    """Test --version flag displays version and exits."""
    from typer.testing import CliRunner
    from hermod.cli import app
    from hermod.__version__ import __version__

    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_version_flag_shows_version -v`
Expected: PASS (this should already work - covers lines 56-57)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add version flag test (cli.py:56-57)"
```

---

## Task 2: Test JSON error output for invalid developer name

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_invalid_developer_json_output():
    """Test invalid developer name error in JSON output mode."""
    from typer.testing import CliRunner
    from hermod.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["collect", "--developer", "user@invalid.com", "--json"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert "error" in output
    assert "Invalid developer name" in output["error"]
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_invalid_developer_json_output -v`
Expected: PASS (covers line 119)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add JSON error output for invalid developer (cli.py:119)"
```

---

## Task 3: Test JSON error output for missing dependencies

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_missing_deps_json_output():
    """Test missing dependencies error in JSON output mode."""
    from unittest.mock import patch
    from typer.testing import CliRunner
    from hermod.cli import app

    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": False, "ccusage-codex": False}):
        runner = CliRunner()
        result = runner.invoke(app, ["collect", "--developer", "Test", "--json"])

        assert result.exit_code == 1
        output = json.loads(result.stdout)
        assert "error" in output
        assert "Dependencies not installed" in output["error"]
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_missing_deps_json_output -v`
Expected: PASS (covers line 129)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add JSON error output for missing deps (cli.py:129)"
```

---

## Task 4: Test developer detection failure with JSON output

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_developer_detection_failure_json():
    """Test developer auto-detection failure in JSON output mode."""
    from unittest.mock import patch
    from typer.testing import CliRunner
    from hermod.cli import app

    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
        with patch("hermod.cli.detect_developer", side_effect=RuntimeError("Git not configured")):
            runner = CliRunner()
            result = runner.invoke(app, ["collect", "--json"])

            assert result.exit_code == 1
            output = json.loads(result.stdout)
            assert "error" in output
            assert "Failed to detect developer" in output["error"]
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_developer_detection_failure_json -v`
Expected: PASS (covers lines 146-151)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add JSON error for developer detection failure (cli.py:146-151)"
```

---

## Task 5: Test auto-detected invalid developer name with JSON output

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_auto_detect_invalid_name_json():
    """Test auto-detected invalid developer name in JSON output mode."""
    from unittest.mock import patch
    from typer.testing import CliRunner
    from hermod.cli import app

    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
        with patch("hermod.cli.detect_developer", return_value="!!!invalid!!!"):
            runner = CliRunner()
            result = runner.invoke(app, ["collect", "--json"])

            assert result.exit_code == 1
            output = json.loads(result.stdout)
            assert "error" in output
            assert "invalid" in output["error"].lower()
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_auto_detect_invalid_name_json -v`
Expected: PASS (covers line 160)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add JSON error for auto-detected invalid name (cli.py:160)"
```

---

## Task 6: Test collect_usage exception with JSON output

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_usage_collection_failure_json():
    """Test usage collection failure in JSON output mode."""
    from unittest.mock import patch
    from typer.testing import CliRunner
    from hermod.cli import app

    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", side_effect=Exception("ccusage failed")):
                runner = CliRunner()
                result = runner.invoke(app, ["collect", "--json"])

                assert result.exit_code == 1
                output = json.loads(result.stdout)
                assert "error" in output
                assert "Failed to collect usage data" in output["error"]
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_usage_collection_failure_json -v`
Expected: PASS (covers lines 175-180)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add JSON error for usage collection failure (cli.py:175-180)"
```

---

## Task 7: Test save_submission exception with JSON output

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_save_failure_json():
    """Test save submission failure in JSON output mode."""
    from unittest.mock import patch, MagicMock
    from typer.testing import CliRunner
    from hermod.cli import app

    mock_data = {
        "metadata": {"date_range": {"start": "2026-01-01", "end": "2026-01-07"}},
        "claude_code": {},
        "codex": {},
    }

    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", return_value=mock_data):
                with patch("hermod.cli.save_submission", side_effect=Exception("Disk full")):
                    runner = CliRunner()
                    result = runner.invoke(app, ["collect", "--json"])

                    assert result.exit_code == 1
                    output = json.loads(result.stdout)
                    assert "error" in output
                    assert "Failed to save submission" in output["error"]
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_save_failure_json -v`
Expected: PASS (covers lines 185-190)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add JSON error for save submission failure (cli.py:185-190)"
```

---

## Task 8: Test env var timeout display in CLI output

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_shows_env_timeout(monkeypatch):
    """Test that env var timeout is displayed in output."""
    from unittest.mock import patch, MagicMock
    from typer.testing import CliRunner
    from hermod.cli import app
    from pathlib import Path

    monkeypatch.setenv("HERMOD_COMMAND_TIMEOUT_SECONDS", "120")

    mock_data = {
        "metadata": {"date_range": {"start": "2026-01-01", "end": "2026-01-07"}},
        "claude_code": {"totals": {"totalCost": 1.50}},
        "codex": {"totals": {"totalCost": 0.50}},
    }

    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", return_value=mock_data):
                with patch("hermod.cli.save_submission", return_value=Path("/tmp/test.json")):
                    runner = CliRunner()
                    result = runner.invoke(app, ["collect"])

                    assert result.exit_code == 0
                    assert "HERMOD_COMMAND_TIMEOUT_SECONDS" in result.stdout
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_shows_env_timeout -v`
Expected: PASS (covers lines 212-216)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add env var timeout display test (cli.py:212-216)"
```

---

## Task 9: Test codex costUSD fallback in summary

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_collect_command_codex_cost_usd_fallback():
    """Test codex costUSD fallback when totalCost is missing."""
    from unittest.mock import patch
    from typer.testing import CliRunner
    from hermod.cli import app
    from pathlib import Path

    mock_data = {
        "metadata": {"date_range": {"start": "2026-01-01", "end": "2026-01-07"}},
        "claude_code": {"totals": {"totalCost": 1.50}},
        "codex": {"totals": {"costUSD": 0.75}},  # Note: costUSD not totalCost
    }

    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", return_value=mock_data):
                with patch("hermod.cli.save_submission", return_value=Path("/tmp/test.json")):
                    runner = CliRunner()
                    result = runner.invoke(app, ["collect"])

                    assert result.exit_code == 0
                    assert "$0.75" in result.stdout or "0.75" in result.stdout
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_collect_command_codex_cost_usd_fallback -v`
Expected: PASS (covers line 227)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add codex costUSD fallback test (cli.py:227)"
```

---

## Task 10: Test submit command gh auth timeout

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_submit_command_gh_auth_timeout():
    """Test submit command handles gh auth timeout."""
    import subprocess
    from unittest.mock import patch
    from typer.testing import CliRunner
    from hermod.cli import app

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="gh auth status", timeout=10)

            runner = CliRunner()
            result = runner.invoke(app, ["submit"])

            assert result.exit_code == 1
            assert "timed out" in result.stdout.lower()
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_submit_command_gh_auth_timeout -v`
Expected: PASS (covers lines 281-283)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add submit gh auth timeout test (cli.py:281-283)"
```

---

## Task 11: Test submit command invalid JSON file

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_submit_command_invalid_json_file(tmp_path):
    """Test submit command handles invalid JSON in submission file."""
    from unittest.mock import patch, MagicMock
    from typer.testing import CliRunner
    from hermod.cli import app

    # Create invalid JSON file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    invalid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    invalid_file.write_text("not valid json {{{")

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 1
            assert "Invalid submission file format" in result.stdout
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_submit_command_invalid_json_file -v`
Expected: PASS (covers lines 308-310)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add submit invalid JSON file test (cli.py:308-310)"
```

---

## Task 12: Test submit command workflow trigger failure

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_submit_command_workflow_trigger_failure(tmp_path):
    """Test submit command handles workflow trigger failure."""
    from unittest.mock import patch, MagicMock
    from typer.testing import CliRunner
    from hermod.cli import app

    # Create valid submission file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    valid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    valid_file.write_text('{"metadata": {"developer": "TestDev"}}')

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            # First call: gh auth status succeeds
            # Second call: gh workflow run fails
            mock_run.side_effect = [
                MagicMock(returncode=0),  # auth status
                MagicMock(returncode=1, stderr=b"workflow not found"),  # workflow run
            ]

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 1
            assert "Failed to submit" in result.stdout
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_submit_command_workflow_trigger_failure -v`
Expected: PASS (covers lines 338-343)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add submit workflow trigger failure test (cli.py:338-343)"
```

---

## Task 13: Test submit command workflow timeout

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_submit_command_workflow_timeout(tmp_path):
    """Test submit command handles workflow trigger timeout."""
    import subprocess
    from unittest.mock import patch, MagicMock
    from typer.testing import CliRunner
    from hermod.cli import app

    # Create valid submission file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    valid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    valid_file.write_text('{"metadata": {"developer": "TestDev"}}')

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            # First call: gh auth status succeeds
            # Second call: gh workflow run times out
            mock_run.side_effect = [
                MagicMock(returncode=0),  # auth status
                subprocess.TimeoutExpired(cmd="gh workflow run", timeout=30),  # workflow run
            ]

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 1
            assert "timed out" in result.stdout.lower()
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_submit_command_workflow_timeout -v`
Expected: PASS (covers lines 345-347)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add submit workflow timeout test (cli.py:345-347)"
```

---

## Task 14: Test submit command repo view failure fallback

**Files:**
- Test: `tests/hermod/test_cli.py`

**Step 1: Write the failing test**

```python
def test_submit_command_repo_view_failure_fallback(tmp_path):
    """Test submit command handles repo view failure gracefully."""
    import subprocess
    from unittest.mock import patch, MagicMock
    from typer.testing import CliRunner
    from hermod.cli import app

    # Create valid submission file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    valid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    valid_file.write_text('{"metadata": {"developer": "TestDev"}}')

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),  # auth status
                MagicMock(returncode=0),  # workflow run
                subprocess.CalledProcessError(1, "gh repo view"),  # repo view fails
            ]

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 0
            assert "Submitted" in result.stdout
            assert "GitHub Actions" in result.stdout  # Fallback text
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_cli.py::test_submit_command_repo_view_failure_fallback -v`
Expected: PASS (covers lines 362-363)

**Step 3: Commit**

```bash
git add tests/hermod/test_cli.py
git commit -m "test: add submit repo view failure fallback test (cli.py:362-363)"
```

---

## Task 15: Test get_git_user_name timeout exception

**Files:**
- Test: `tests/hermod/test_git_detector.py`

**Step 1: Write the failing test**

```python
def test_get_git_user_name_timeout():
    """Test handling when git user.name command times out."""
    import subprocess
    from unittest.mock import patch
    from hermod.git_detector import get_git_user_name

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git config user.name", timeout=5)

        result = get_git_user_name()
        assert result is None
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_git_detector.py::test_get_git_user_name_timeout -v`
Expected: PASS (covers lines 53-55)

**Step 3: Commit**

```bash
git add tests/hermod/test_git_detector.py
git commit -m "test: add git user.name timeout test (git_detector.py:53-55)"
```

---

## Task 16: Test get_git_user_name file not found exception

**Files:**
- Test: `tests/hermod/test_git_detector.py`

**Step 1: Write the failing test**

```python
def test_get_git_user_name_git_not_found():
    """Test handling when git is not installed."""
    from unittest.mock import patch
    from hermod.git_detector import get_git_user_name

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")

        result = get_git_user_name()
        assert result is None
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_git_detector.py::test_get_git_user_name_git_not_found -v`
Expected: PASS (covers lines 56-58)

**Step 3: Commit**

```bash
git add tests/hermod/test_git_detector.py
git commit -m "test: add git not found test (git_detector.py:56-58)"
```

---

## Task 17: Test load_developer_mappings with config file

**Files:**
- Test: `tests/hermod/test_git_detector.py`

**Step 1: Write the failing test**

```python
def test_load_developer_mappings_with_config_file(tmp_path):
    """Test loading developer mappings from config file."""
    from unittest.mock import patch
    from hermod.git_detector import load_developer_mappings
    import json

    config_data = {
        "developers": [
            {
                "canonical_name": "Alice",
                "git_emails": ["alice@example.com"],
                "git_names": ["Alice Smith"],
                "linear_names": ["alice@linear.com"],
            },
            {
                "canonical_name": "Bob",
                "git_emails": ["bob@example.com"],
                "linear_names": [],
            },
        ]
    }

    config_file = tmp_path / "config" / "developer_names.json"
    config_file.parent.mkdir(parents=True)
    config_file.write_text(json.dumps(config_data))

    with patch("hermod.git_detector.Path") as mock_path:
        mock_path.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = config_file
        mock_path.return_value.parent.parent.parent / "config" / "developer_names.json"

        # Direct test with actual file
        from pathlib import Path

        original_load = load_developer_mappings.__wrapped__ if hasattr(load_developer_mappings, '__wrapped__') else None

        # Patch the path construction
        with patch.object(Path, '__truediv__', side_effect=lambda self, other: config_file.parent / other if other == "config" else config_file if other == "developer_names.json" else Path.__truediv__(self, other)):
            pass

    # Simpler approach: patch Path(__file__) chain
    with patch("hermod.git_detector.Path") as MockPath:
        mock_config_path = tmp_path / "config" / "developer_names.json"
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_config_path
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value.exists.return_value = True

        # Just test directly by creating the file structure
        pass

    # Actually, let's test this more directly
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "developer_names.json"
    config_file.write_text(json.dumps(config_data))

    # Patch __file__ to point to tmp_path structure
    with patch("hermod.git_detector.__file__", str(tmp_path / "src" / "hermod" / "git_detector.py")):
        # This won't work because Path uses the actual __file__
        pass

    # Best approach: test the function with a real temp config
    import hermod.git_detector as gd
    original_file = gd.__file__

    # Create proper directory structure
    src_dir = tmp_path / "src" / "hermod"
    src_dir.mkdir(parents=True)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "developer_names.json"
    config_file.write_text(json.dumps(config_data))

    with patch.object(gd, '__file__', str(src_dir / "git_detector.py")):
        mappings = load_developer_mappings()

    assert "alice@example.com" in mappings["email_to_canonical"]
    assert mappings["email_to_canonical"]["alice@example.com"] == "Alice"
    assert "alice smith" in mappings["name_to_canonical"]
    assert "alice@linear.com" in mappings["email_to_canonical"]
```

This test is complex. Let me simplify:

```python
def test_load_developer_mappings_with_config_file(tmp_path, monkeypatch):
    """Test loading developer mappings from config file."""
    import json
    import hermod.git_detector as gd

    config_data = {
        "developers": [
            {
                "canonical_name": "Alice",
                "git_emails": ["alice@example.com"],
                "git_names": ["Alice Smith"],
                "linear_names": ["alice@linear.com"],
            },
        ]
    }

    # Create directory structure matching the code's expectation
    # Path(__file__).parent.parent.parent / "config" / "developer_names.json"
    src_dir = tmp_path / "src" / "hermod"
    src_dir.mkdir(parents=True)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "developer_names.json"
    config_file.write_text(json.dumps(config_data))

    # Patch __file__ to our temp structure
    monkeypatch.setattr(gd, "__file__", str(src_dir / "git_detector.py"))

    mappings = gd.load_developer_mappings()

    assert mappings["email_to_canonical"]["alice@example.com"] == "Alice"
    assert mappings["name_to_canonical"]["alice smith"] == "Alice"
    assert mappings["email_to_canonical"]["alice@linear.com"] == "Alice"
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_git_detector.py::test_load_developer_mappings_with_config_file -v`
Expected: PASS (covers lines 68-98)

**Step 3: Commit**

```bash
git add tests/hermod/test_git_detector.py
git commit -m "test: add config file loading test (git_detector.py:68-98)"
```

---

## Task 18: Test detect_developer raises when no valid fallback

**Files:**
- Test: `tests/hermod/test_git_detector.py`

**Step 1: Write the failing test**

```python
def test_detect_developer_raises_when_no_valid_fallback():
    """Test detect_developer raises RuntimeError when email username is invalid."""
    from unittest.mock import patch
    import pytest
    from hermod.git_detector import detect_developer

    mock_mappings = {"email_to_canonical": {}, "name_to_canonical": {}}

    with patch("hermod.git_detector.load_developer_mappings", return_value=mock_mappings):
        with patch("hermod.git_detector.get_git_user_email", return_value="123@example.com"):
            with patch("hermod.git_detector.get_git_user_name", return_value=None):
                with pytest.raises(RuntimeError, match="Could not auto-detect developer"):
                    detect_developer()
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_git_detector.py::test_detect_developer_raises_when_no_valid_fallback -v`
Expected: PASS (covers line 147)

**Step 3: Commit**

```bash
git add tests/hermod/test_git_detector.py
git commit -m "test: add detect_developer RuntimeError test (git_detector.py:147)"
```

---

## Task 19: Test setup_logging with log file

**Files:**
- Test: `tests/hermod/test_logging_config.py` (new file)

**Step 1: Write the failing test**

Create `tests/hermod/test_logging_config.py`:

```python
"""Tests for logging configuration."""

import logging
from pathlib import Path


def test_setup_logging_with_file(tmp_path):
    """Test setup_logging creates file handler when log_file specified."""
    from hermod.logging_config import setup_logging

    log_file = tmp_path / "logs" / "test.log"

    setup_logging(level="DEBUG", log_file=log_file)

    # Verify log file parent directory was created
    assert log_file.parent.exists()

    # Log something and verify file is created
    logger = logging.getLogger("hermod.test")
    logger.debug("Test message")

    # File handler should have been added
    root_logger = logging.getLogger()
    file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0


def test_get_logger():
    """Test get_logger returns a logger instance."""
    from hermod.logging_config import get_logger

    logger = get_logger("test.module")

    assert logger is not None
    assert logger.name == "test.module"
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_logging_config.py -v`
Expected: PASS (covers lines 47-51, 67)

**Step 3: Commit**

```bash
git add tests/hermod/test_logging_config.py
git commit -m "test: add logging_config tests (logging_config.py:47-51,67)"
```

---

## Task 20: Test check_ccusage_codex_installed

**Files:**
- Test: `tests/hermod/test_dependencies.py`

**Step 1: Write the failing test**

Add to `tests/hermod/test_dependencies.py`:

```python
def test_check_ccusage_codex_installed_success():
    """Test ccusage-codex installed check when available."""
    from unittest.mock import patch
    from hermod.dependencies import check_ccusage_codex_installed

    with patch("shutil.which", return_value="/usr/local/bin/ccusage-codex"):
        is_installed = check_ccusage_codex_installed()
        assert is_installed is True


def test_check_ccusage_codex_installed_missing():
    """Test ccusage-codex installed check when not available."""
    from unittest.mock import patch
    from hermod.dependencies import check_ccusage_codex_installed

    with patch("shutil.which", return_value=None):
        is_installed = check_ccusage_codex_installed()
        assert is_installed is False
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_dependencies.py::test_check_ccusage_codex_installed_success tests/hermod/test_dependencies.py::test_check_ccusage_codex_installed_missing -v`
Expected: PASS (covers lines 28-31)

**Step 3: Commit**

```bash
git add tests/hermod/test_dependencies.py
git commit -m "test: add ccusage-codex dependency tests (dependencies.py:28-31)"
```

---

## Task 21: Test collector CalledProcessError branch

**Files:**
- Test: `tests/hermod/test_collector.py`

**Step 1: Write the failing test**

Add to `tests/hermod/test_collector.py`:

```python
def test_run_command_called_process_error():
    """Test run_command handles CalledProcessError."""
    import subprocess
    from unittest.mock import patch
    from hermod.collector import run_command

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "ccusage")

        result = run_command(["ccusage", "daily", "--json"])
        assert result == {}
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/hermod/test_collector.py::test_run_command_called_process_error -v`
Expected: PASS (covers lines 96-97)

**Step 3: Commit**

```bash
git add tests/hermod/test_collector.py
git commit -m "test: add CalledProcessError test (collector.py:96-97)"
```

---

## Task 22: Run full test suite and verify coverage

**Step 1: Run all tests with coverage**

Run: `uv run pytest tests/ -v --cov=hermod --cov-report=term-missing`

**Step 2: Verify coverage meets target**

Expected: Coverage ≥ 85%

**Step 3: Update CI threshold**

If coverage ≥ 85%, update `.github/workflows/ci.yml`:

```yaml
- name: Run tests with coverage
  run: uv run pytest tests/ -v --cov=hermod --cov-report=term-missing --cov-fail-under=85
```

**Step 4: Commit CI update**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: restore CI coverage threshold to 85%"
```

---

## Task 23: Final verification and PR

**Step 1: Run full CI checks locally**

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest tests/ -v --cov=hermod --cov-report=term-missing --cov-fail-under=85
```

**Step 2: Push and create PR**

```bash
gt submit --stack
```

---

## Summary

| Task | File | Lines Covered |
|------|------|---------------|
| 1 | cli.py | 56-57 |
| 2 | cli.py | 119 |
| 3 | cli.py | 129 |
| 4 | cli.py | 146-151 |
| 5 | cli.py | 160 |
| 6 | cli.py | 175-180 |
| 7 | cli.py | 185-190 |
| 8 | cli.py | 212-216 |
| 9 | cli.py | 227 |
| 10 | cli.py | 281-283 |
| 11 | cli.py | 308-310 |
| 12 | cli.py | 338-343 |
| 13 | cli.py | 345-347 |
| 14 | cli.py | 362-363 |
| 15 | git_detector.py | 53-55 |
| 16 | git_detector.py | 56-58 |
| 17 | git_detector.py | 68-98 |
| 18 | git_detector.py | 147 |
| 19 | logging_config.py | 47-51, 67 |
| 20 | dependencies.py | 28-31 |
| 21 | collector.py | 96-97 |
