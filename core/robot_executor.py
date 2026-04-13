
"""
Robot executor implementation.

Responsibility:
 - Build and run Robot Framework commands using subprocess.
 - Stream stdout lines and forward them to a provided callback (thread-safe via Qt signals).

Usage:
    executor = RobotExecutor()
    executor.run(runner_path, params, callback_output)

The `callback_output` callable is invoked for each stdout line.
"""
from typing import Dict, Any, Callable, List, Optional
import subprocess
import sys
from pathlib import Path


class RobotExecutor:
    def __init__(self, robot_executable: str = "robot"):
        self.robot_executable = robot_executable
        self._proc = None
        self._proc_lock = __import__('threading').Lock()

    def _build_command(self, runner_path: str, params: Dict[str, Any]) -> List[str]:
        # Use python -m robot to ensure execution via the current interpreter
        cmd = [sys.executable, "-m", "robot", "--output", "NONE", "--log", "NONE", "--report", "NONE"]
        # Extract special params (tests) before adding variables to avoid sending them as -v
        tests = None
        if params is not None and isinstance(params, dict):
            tests = params.pop("__tests__", None)
        # Add variables
        for k, v in (params or {}).items():
            # Robot variable format: -v name:value
            cmd.extend(["-v", f"{k}:{v}"])
        # Add tests selectors if provided in params_tests
        if tests:
            for t in tests:
                cmd.extend(["-t", str(t)])
        # Runner path last
        cmd.append(str(runner_path))
        return cmd

    def run(self, runner_path: str, params: Dict[str, Any], callback_output: Callable[[str], None], working_dir: Optional[str] = None) -> int:
        """Run the robot runner and stream output.

        - `runner_path`: path to the .robot file
        - `params`: dict of variables to pass
        - `callback_output`: callable that receives each stdout line (string)

        Returns the process exit code.
        """
        # Copy params to avoid mutating caller's dict
        params_copy = dict(params or {})
        cmd = self._build_command(runner_path, params_copy)

        cwd = None
        if working_dir:
            cwd = str(Path(working_dir))

        # Start the process; set working directory so relative resources are resolved
        proc = None
        with self._proc_lock:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=cwd,
            )
            proc = self._proc

        # Stream stdout line by line
        try:
            if proc.stdout is not None:
                for raw_line in proc.stdout:
                    line = raw_line.rstrip("\n")
                    try:
                        callback_output(line)
                    except Exception:
                        pass
            proc.wait()
            return proc.returncode
        finally:
            with self._proc_lock:
                self._proc = None
    def stop(self) -> None:
        """Attempt to terminate the running Robot process."""
        with self._proc_lock:
            p = self._proc
        if not p:
            return
        try:
            p.terminate()
            # wait a short while
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

