# -*- coding: utf-8 -*-
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import psutil
import signal
import subprocess
import time

from odoo import _
from odoo.exceptions import ValidationError
from typing import List


class SubProcessRunner:

    def __init__(self, timeout):
        """Initialize the runner.

        :param float timeout: the timeout in seconds
        """
        self._timeout = timeout

    def run(self, command: List[str]):
        """Run the given command.

        When the timeout expires, the process is terminated.

        :param command: the command to execute
        """
        process = subprocess.Popen(command)
        timetaken = 0

        while True:
            status = process.poll()
            if status is 0:
                break
            elif status is not None:
                raise ValidationError(
                    _('Command {command} exited with status {status}.').format(
                        command=command,
                        status=status,
                    ))

            timetaken += 0.1
            time.sleep(0.1)

            if timetaken > self._timeout:
                self._terminate_process(process)
                raise ValidationError(
                    _('Timeout ({timeout} seconds) expired while executing '
                      'the command: {command}').format(
                        command=command,
                        timeout=self._timeout,
                    ))

    def _terminate_process(self, process):
        """Attempt to terminate the process.

        Kill the process if it is still alive after 60 seconds.

        :param string process: the process pid to kill
        """
        process.terminate()
        for i in range(60):
            time.sleep(1)
            if process.poll() is not None:
                return

        parent = psutil.Process(process.pid)
        for child in parent.children(recursive=True):
            child.send_signal(signal.SIGKILL)
        parent.send_signal(signal.SIGKILL)
