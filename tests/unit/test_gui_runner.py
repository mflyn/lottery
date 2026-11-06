"""A native Tk abort must be reported without launching/aborting pytest."""
import importlib.util
from pathlib import Path
import subprocess

import pytest


@pytest.fixture
def runner():
    path = Path(__file__).resolve().parents[1] / 'gui' / 'run_gui_tests.py'
    spec = importlib.util.spec_from_file_location('lottery_gui_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_abort_stops_before_pytest(runner, monkeypatch, capsys):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, -6, stdout='', stderr='native Tk abort')

    monkeypatch.setattr(runner.subprocess, 'run', run)
    assert runner.main([]) == 2
    assert len(calls) == 1
    error = capsys.readouterr().err
    assert 'SIGABRT' in error and 'native Tk abort' in error


def test_preflight_timeout_stops_before_pytest(runner, monkeypatch, capsys):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        raise subprocess.TimeoutExpired(command, kwargs['timeout'])

    monkeypatch.setattr(runner.subprocess, 'run', run)
    assert runner.main([]) == 2
    assert len(calls) == 1
    assert 'timed out' in capsys.readouterr().err


@pytest.mark.parametrize('args, marker', [([], 'gui'), (['--all'], '')])
def test_desktop_success_runs_selected_suite_and_preserves_failure(runner, monkeypatch, args, marker):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0 if len(calls) == 1 else 1, stdout='Tk OK', stderr='')

    monkeypatch.setattr(runner.subprocess, 'run', run)
    assert runner.main(args + ['-q']) == 1
    command, options = calls[1]
    assert command[1:3] == ['-m', 'pytest']
    assert command[command.index('-m', 3) + 1] == marker
    assert command[-1] == '-q'
    assert options['cwd'] == Path(__file__).resolve().parents[2]
