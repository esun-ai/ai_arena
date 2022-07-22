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

import pandas as pd

prediction = pd.DataFrame(
    data={
        "qid": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "answer": [
            {'answer':'玉'}, {'answer':'山'},
            {'answer':'王'}, {'answer':'玉'},
            {'answer':'山'}, {'answer':'山'},
            {'answer':'金'}, {'answer':'銓'},
            {'answer':'isnull'}, {'answer':'融'},
            {'answer':'智'}, {'answer':'isnull'}
        ]
    }
)
ground_truth = pd.DataFrame(
    data={
        "qid": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "answer": ['玉', '玉', '玉', '玉', '山', '山', '金', '金', '融', '融', 'isnull', 'isnull'],
    }
)
test_case = [([prediction, ground_truth], 0.6)]