#!/usr/bin/env python
# Copyright (C) 2022  E.SUN BANK.
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

from psycopg2 import sql
import sqlvalidator
from src.task_wrapper import update_status_sql, get_team_url_sql, get_questions_sql


def as_string(composable):
    if isinstance(composable, sql.Composed):
        return ''.join([as_string(x) for x in composable])
    elif isinstance(composable, sql.SQL):
        return composable.string
    else:
        rv = sql.ext.adapt(composable._wrapped).getquoted()
        return rv.decode() if isinstance(rv, bytes) else rv


def unify_format(string: str) -> str:
    return string.replace(' = ', '=').lower()


def test_update_status_sql():
    sqlstring = update_status_sql(status=2, team_id=13, date='2022-07-01')
    result = unify_format(as_string(sqlstring))
    sqlstring2 = update_status_sql(status=2, team_id='', date='2022-07-02')
    result_without_teamid = unify_format(as_string(sqlstring2))
    assert 'set insert_question_status=2' in result
    assert 'and insert_question_status=1' in result
    assert 'where team_id=' not in result_without_teamid


def test_get_team_url_sql():
    sqlstring = get_team_url_sql(team_id=777)
    result = unify_format(as_string(sqlstring))
    assert 'where status_code_infer=200 and team_id=777' in result
    assert sqlvalidator.parse(result).is_valid() is True


def test_get_questions_sql():
    sqlstring = get_questions_sql('2020-07-01', '')
    result = unify_format(as_string(sqlstring))
    expected_snippet = "where send_date='2020-07-01'"
    assert expected_snippet in result
    assert sqlvalidator.parse(result).is_valid() is True
