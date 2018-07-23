# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pytest
import os

from odoo.exceptions import ValidationError
from ..subprocess_runner import SubProcessRunner


class TestSubprocessRunner:

    def _get_file_path(self, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return dir_path + '/' + filename

    def test_ifTimeoutIsNotExceeded_thenNoErrorRaised(self):
        command = ['sh', self._get_file_path('sleep_10ms.sh')]
        SubProcessRunner(1).run(command)

    def test_ifTimeoutIsExceeded_thenRaiseValidationError(self):
        command = ['sh', self._get_file_path('sleep_100s.sh')]
        with pytest.raises(ValidationError):
            SubProcessRunner(1).run(command)

    def test_ifTimeoutIsNotExceeded_ButProcessFails_thenRaiseValidationError(self):
        command = ['sh', self._get_file_path('sleep_10ms_and_fail.sh')]
        with pytest.raises(ValidationError):
            SubProcessRunner(1).run(command)
