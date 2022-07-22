# -*- coding:utf-8 -*-
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
from case import test_case
from src.evaluation_metric import Evaluation_Metrics

@pytest.mark.parametrize("test_input, expected", test_case)
def test_metric(test_input, expected):
    _ , total_score = Evaluation_Metrics(test_input[0], test_input[1]).get_scores()
    assert total_score == expected