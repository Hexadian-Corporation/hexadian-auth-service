from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from auth_cli import (
    cmd_down,
    cmd_lint,
    cmd_logs,
    cmd_ps,
    cmd_seed,
    cmd_setup,
    cmd_start,
    cmd_test,
    cmd_up,
    main,
)


class TestCmdUp:
    @patch("auth_cli.subprocess.run")
    def test_runs_docker_compose_up_build(self, mock_run: MagicMock) -> None:
        cmd_up()
        mock_run.assert_called_once_with(
            ["docker", "compose", "up", "--build", "-d"],
            check=True,
        )


class TestCmdDown:
    @patch("auth_cli.subprocess.run")
    def test_runs_docker_compose_down(self, mock_run: MagicMock) -> None:
        cmd_down()
        mock_run.assert_called_once_with(
            ["docker", "compose", "down"],
            check=True,
        )


class TestCmdSetup:
    @patch("auth_cli.subprocess.run")
    def test_runs_uv_sync_and_npm_install(self, mock_run: MagicMock) -> None:
        cmd_setup()
        assert mock_run.call_count == 3
        mock_run.assert_any_call(["uv", "sync"], check=True)
        mock_run.assert_any_call(["npm", "install", "--prefix", "auth-portal"], check=True)
        mock_run.assert_any_call(["npm", "install", "--prefix", "auth-backoffice"], check=True)


class TestCmdStart:
    @patch("auth_cli.subprocess.run")
    def test_starts_mongo_if_not_running(self, mock_run: MagicMock) -> None:
        # First call checks running services (auth-mongo not listed)
        check_result = MagicMock(stdout="auth-service\n", returncode=0)
        # Subsequent calls succeed normally
        ok_result = MagicMock(returncode=0)
        mock_run.side_effect = [check_result, ok_result, ok_result]

        cmd_start()

        calls = mock_run.call_args_list
        # 1st: check running services
        assert calls[0] == call(
            ["docker", "compose", "ps", "--status", "running", "--services"],
            capture_output=True,
            text=True,
            check=False,
        )
        # 2nd: start auth-mongo
        assert calls[1] == call(["docker", "compose", "up", "-d", "auth-mongo"], check=True)
        # 3rd: start uvicorn
        assert calls[2] == call(
            ["uv", "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8006"],
            check=True,
        )

    @patch("auth_cli.subprocess.run")
    def test_skips_mongo_start_when_already_running(self, mock_run: MagicMock) -> None:
        check_result = MagicMock(stdout="auth-mongo\nauth-service\n", returncode=0)
        ok_result = MagicMock(returncode=0)
        mock_run.side_effect = [check_result, ok_result]

        cmd_start()

        # Should only have 2 calls: check + uvicorn (no mongo start)
        assert mock_run.call_count == 2


class TestCmdLogs:
    @patch("auth_cli.subprocess.run")
    def test_follows_all_logs_without_args(self, mock_run: MagicMock) -> None:
        cmd_logs([])
        mock_run.assert_called_once_with(
            ["docker", "compose", "logs", "-f"],
            check=False,
        )

    @patch("auth_cli.subprocess.run")
    def test_follows_specific_service_logs(self, mock_run: MagicMock) -> None:
        cmd_logs(["auth-mongo"])
        mock_run.assert_called_once_with(
            ["docker", "compose", "logs", "-f", "auth-mongo"],
            check=False,
        )


class TestCmdPs:
    @patch("auth_cli.subprocess.run")
    def test_runs_docker_compose_ps(self, mock_run: MagicMock) -> None:
        cmd_ps()
        mock_run.assert_called_once_with(
            ["docker", "compose", "ps"],
            check=True,
        )


class TestCmdSeed:
    @patch("auth_cli.subprocess.run")
    def test_runs_seed_script(self, mock_run: MagicMock) -> None:
        cmd_seed()
        mock_run.assert_called_once_with(
            ["uv", "run", "python", "-m", "src.infrastructure.seed.seed_rbac"],
            check=True,
        )


class TestCmdTest:
    @patch("auth_cli.subprocess.run")
    def test_runs_pytest(self, mock_run: MagicMock) -> None:
        cmd_test([])
        mock_run.assert_called_once_with(["uv", "run", "pytest"], check=True)

    @patch("auth_cli.subprocess.run")
    def test_forwards_extra_args(self, mock_run: MagicMock) -> None:
        cmd_test(["-v", "--tb=short"])
        mock_run.assert_called_once_with(
            ["uv", "run", "pytest", "-v", "--tb=short"],
            check=True,
        )


class TestCmdLint:
    @patch("auth_cli.subprocess.run")
    def test_runs_ruff_check(self, mock_run: MagicMock) -> None:
        cmd_lint()
        mock_run.assert_called_once_with(
            ["uv", "run", "ruff", "check", "."],
            check=True,
        )


class TestMain:
    @patch("auth_cli.cmd_up")
    def test_no_args_shows_help(self, mock_up: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sys.argv", ["auth"]):
            main()
        output = capsys.readouterr().out
        assert "Usage:" in output
        mock_up.assert_not_called()

    @patch("auth_cli.cmd_up")
    def test_help_flag(self, mock_up: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sys.argv", ["auth", "--help"]):
            main()
        output = capsys.readouterr().out
        assert "Usage:" in output

    @patch("auth_cli.cmd_up")
    def test_dispatches_up(self, mock_up: MagicMock) -> None:
        with patch("sys.argv", ["auth", "up"]):
            main()
        mock_up.assert_called_once()

    @patch("auth_cli.cmd_down")
    def test_dispatches_down(self, mock_down: MagicMock) -> None:
        with patch("sys.argv", ["auth", "down"]):
            main()
        mock_down.assert_called_once()

    @patch("auth_cli.cmd_setup")
    def test_dispatches_setup(self, mock_setup: MagicMock) -> None:
        with patch("sys.argv", ["auth", "setup"]):
            main()
        mock_setup.assert_called_once()

    @patch("auth_cli.cmd_start")
    def test_dispatches_start(self, mock_start: MagicMock) -> None:
        with patch("sys.argv", ["auth", "start"]):
            main()
        mock_start.assert_called_once()

    @patch("auth_cli.cmd_logs")
    def test_dispatches_logs(self, mock_logs: MagicMock) -> None:
        with patch("sys.argv", ["auth", "logs", "auth-mongo"]):
            main()
        mock_logs.assert_called_once_with(["auth-mongo"])

    @patch("auth_cli.cmd_ps")
    def test_dispatches_ps(self, mock_ps: MagicMock) -> None:
        with patch("sys.argv", ["auth", "ps"]):
            main()
        mock_ps.assert_called_once()

    @patch("auth_cli.cmd_seed")
    def test_dispatches_seed(self, mock_seed: MagicMock) -> None:
        with patch("sys.argv", ["auth", "seed"]):
            main()
        mock_seed.assert_called_once()

    @patch("auth_cli.cmd_test")
    def test_dispatches_test_with_args(self, mock_test: MagicMock) -> None:
        with patch("sys.argv", ["auth", "test", "-v"]):
            main()
        mock_test.assert_called_once_with(["-v"])

    @patch("auth_cli.cmd_lint")
    def test_dispatches_lint(self, mock_lint: MagicMock) -> None:
        with patch("sys.argv", ["auth", "lint"]):
            main()
        mock_lint.assert_called_once()

    def test_unknown_command_exits_with_error(self) -> None:
        with patch("sys.argv", ["auth", "foobar"]), pytest.raises(SystemExit, match="1"):
            main()

    @patch("auth_cli.cmd_up")
    def test_h_flag_shows_help(self, mock_up: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sys.argv", ["auth", "-h"]):
            main()
        output = capsys.readouterr().out
        assert "Usage:" in output
