"""Run real-window pytest tests after a crash-isolated desktop/Tk preflight."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys


TK_PROBE = """
import tkinter as tk
root = tk.Tk()
root.update()
print('Tk OK:', root.tk.call('info', 'patchlevel'), root.tk.call('tk', 'windowingsystem'), flush=True)
root.destroy()
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Run the full suite including real windows')
    options, pytest_args = parser.parse_known_args(argv)
    project_root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ, TK_SILENCE_DEPRECATION='1')
    try:
        probe = subprocess.run(
            [sys.executable, '-c', TK_PROBE], cwd=project_root, env=environment,
            capture_output=True, text=True, timeout=20,
        )
    except subprocess.TimeoutExpired:
        print('Tk desktop preflight timed out. Pytest was not started.', file=sys.stderr)
        return 2
    if probe.returncode:
        reason = f'exit {probe.returncode}'
        if probe.returncode < 0:
            try:
                reason = signal.Signals(-probe.returncode).name
            except ValueError:
                pass
        print(
            f'Tk desktop preflight failed ({reason}). Pytest was not started.\n'
            'Run this command in a logged-in graphical desktop session; a restricted '
            'sandbox may need desktop execution permission.\n'
            + probe.stdout + probe.stderr,
            file=sys.stderr,
        )
        return 2
    print(probe.stdout.strip(), flush=True)
    command = [sys.executable, '-m', 'pytest']
    if not options.all:
        command.append('tests/gui/test_main_window.py')
    command.extend(['-m', '' if options.all else 'gui', '-p', 'no:cacheprovider'])
    command.extend(pytest_args)
    result = subprocess.run(command, cwd=project_root, env=environment)
    return result.returncode if result.returncode >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
