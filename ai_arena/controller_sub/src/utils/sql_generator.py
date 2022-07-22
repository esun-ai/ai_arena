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
