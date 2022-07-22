#!/usr/bin/env python
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

def get_verified_teams_sql():
    sqlstring = sql.SQL("""
                        SELECT
                                DISTINCT(b.team_id :: VARCHAR),
                                b.api_url
                          FROM (
                                SELECT
                                        team_id,
                                        MAX(verification_time) AS ver_time
                                  FROM public.verification
                                 WHERE status_code_infer = 200
                                 GROUP BY team_id) a
                         INNER JOIN(
                                SELECT
                                        team_id,
                                        verification_time,
                                        api_url
                                  FROM public.verification) b 
                            ON a.team_id = b.team_id 
                               AND a.ver_time = b.verification_time
                        """)
    return sqlstring
