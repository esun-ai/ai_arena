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

import datetime
import os
import json
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import psycopg2
import pytz
import requests
import six
from google.cloud import storage
from psycopg2 import sql
from src.evaluation_metric import Evaluation_Metrics
from src.logger import logger


tw = pytz.timezone('Asia/Taipei')
utc = pytz.utc

fm.fontManager.addfont('src/NotoSansCJKtc-Regular.otf')
matplotlib.rc('font', family='Noto Sans CJK TC')

class Send_Leaderboard():
    """
    Calculate score and send leaderboard to slack.
    """
    def __init__(self, cal_date=None):
        logger.info({
            "message": "[Leaderboard] Initialize leaderboard object, start to calculate score.",
            "trigger": "Leaderboard",
            "ENV": os.environ['ENV']
            })
        self.link_info = {
            'dbname': os.environ['DB_NAME'],
            'user': os.environ['DB_USER'],
            'host': os.environ['DB_HOST'],
            'password': os.environ['DB_PASS'],
            'competition': os.environ['COMPETITION'],
            'competition_channel': os.environ['SLACK_PUBLIC_CHANNEL'],
            'gcp_bucket_name': os.environ['GCP_BUCKET_NAME'],
            'bot_token': os.environ['SLACK_BOT_TOKEN'],
            'env': os.environ['ENV']
        }
        self.register_list = {}
        self.img_name = ''
        self.csv_name = ''
        self.slack_url = 'https://slack.com/api/chat.postMessage'
        self.json_filepath = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        self.official_start_date = os.environ['OFFICIAL_START_DATE']
        self.cal_date = cal_date
    
    def render_mpl_table(self, data, col_width=10.0, row_height=1.0, font_size=15,
                     header_color='#4F9D9D', row_colors=['#A3D1D1', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
        """
        Create a template figure for leaderboard.

        Parameters:
               - data: competitor score dataframe
               - col_width
               - row_height
               - font_size
               - header_color
               - row_colors
               - edge_color
               - bbox
               - header_columns
               - ax

        Return: ax
        """
        temp = data.copy(deep=True)
        temp['隊伍名稱'] = temp.apply(lambda x: x['隊伍名稱'][:18] + '...' if len(x['隊伍名稱'])>18 else x['隊伍名稱'], axis=1)
        if ax is None:
            size = (np.array(temp.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
            fig, ax = plt.subplots(figsize=size)
            ax.axis('off')

        temp['目前總分'] = temp['目前總分'].round(6)
        mpl_table = ax.table(cellText=temp.values, bbox=bbox, colLabels=temp.columns, **kwargs)

        mpl_table.auto_set_font_size(False)
        mpl_table.set_fontsize(font_size)

        for k, cell in six.iteritems(mpl_table._cells):
            cell.set_edgecolor(edge_color)
            if k[0] == 0 or k[1] < header_columns:
                cell.set_text_props(weight='bold', color='w')
                cell.set_facecolor(header_color)
            else:
                cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
        return ax
        
    def upload_blob(self, bucket_name, source_file_name, destination_blob_name):
        """
        Uploads a file to the bucket.

        Parameters:
            - bucket_name: GCS storage bucket name
            - source_file_name
            - destination_blob_name

        Return: get the blob url
        """
        storage_client = storage.Client.from_service_account_json(self.json_filepath)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info({
            "message": "[Leaderboard] File {} uploaded to gcp. ".format(source_file_name),
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "filename": source_file_name,
            "calculate_date": str(self.cal_date)})

        blob.make_public()
        logger.info({
            "message": "[Leaderboard] Blob {} is publicly accessible at {}".format(blob.name, blob.public_url),
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "blob_name": blob.name,
            "blob_public_url": blob.public_url,
            "filename": source_file_name,
            "calculate_date": str(self.cal_date)})
        return blob.public_url
    
    def create_connection(self):
        """
        Create a database connection to the POSTGRES database.

        Return: Connection object or None
        """
        conn = None
        try:
            logger.debug("Database connection starts.")
            conn = psycopg2.connect(host=os.environ['DB_HOST'],
                        database=os.environ['DB_NAME'],
                        user=os.environ['DB_USER'],
                        password=os.environ['DB_PASS'])
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB connection Error: {} ".format(error))
        return conn
        
    
    def get_register_list(self):
        """
        Get register list from DB

        Return: the team id list
        """
        team_id_list = {} 
        with self.create_connection() as conn:
            sql = ''' select team_id, team_name from register where competition = '%s' and status_code = 1 '''%self.link_info['competition']
            df = pd.read_sql(sql, conn)
            for _ , row in df.iterrows():
                team_id_list[str(row['team_id'])] = row['team_name']
        logger.info({
            "message": "[Leaderboard] Successfully get registered list.",
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "num_of_register_team": str(len(team_id_list.keys())),
            "calculate_date": str(self.cal_date)})
        return team_id_list

    def get_latest_date(self):
        """
        Get latest date from table healthcheck_log.

        Return: query latest date
        """
        date_for_query = None
        with self.create_connection() as conn:
            with conn.cursor() as cur:
                sql = '''
                        with cte1 as
                            (select qid 
                                from healthcheck_log where server_timestamp::timestamp::date = 
                                    (select max(server_timestamp)::timestamp::date
                                    from healthcheck_log))
                        select a.send_date::date
                        from questions a inner join cte1 b on a.qid=b.qid
                    '''
                cur.execute(sql)
                date_for_query = cur.fetchone()[0]
                if date_for_query:
                    date_for_query = str(date_for_query)
                    date_for_query = pd.to_datetime(date_for_query).date()
        return date_for_query

    def get_now_timestamp(self):
        """
        Get current timestamp.
        """
        dt = datetime.datetime.now()
        return dt
    
    def get_leaderboard(self):
        """
        Get answers from table questions and calculate the scores

        Return: leaderboard DataFrame
        """
        logger.info({
            "message": "[Leaderboard] Start to get answers of registered lists.",
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "num_of_register_team": str(len(self.register_list.keys())),
            "calculate_date": str(self.cal_date)})
        scores = []
        with self.create_connection() as conn:
            sql = ''' select qid, answer 
                      from questions 
                      where competition = '%s' 
                            and send_date::date is not null 
                            and send_date::date >= '%s'::date
                            and send_date::date <= '%s'::date
                    '''%(self.link_info['competition'], str(self.official_start_date), str(self.cal_date))
            questions = pd.read_sql(sql, conn)
            qid_list = questions.qid.tolist()
            qid_query_str = "'" + "','".join(qid_list) + "'"
            sql = '''
                    select b.*
                    from (select team_id, qid, min(post_time) as min_post_time from answers where status_code=200 and qid in (%s) group by team_id, qid) a
                        inner join (select team_id, qid, post_time, answer from answers where status_code=200 and qid in (%s)) b
                        on a.team_id=b.team_id and a.qid=b.qid and a.min_post_time=b.post_time;
                '''%(qid_query_str, qid_query_str)

            answers = pd.read_sql(sql, conn)

            for team in self.register_list.keys():
                score = {}
                score['team_id'] = team
                score['team_name'] = self.register_list[team]
                team_answer = answers[answers.team_id == int(team)][['qid', 'answer']]
                logger.info({
                    "message": "[Leaderboard] Start to call evaluation metrics to calculate team {}'s scores".format(team),
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env'],
                    "team_id": str(team),
                    "num_of_register_team": str(len(self.register_list.keys())),
                    "calculate_date": str(self.cal_date)})
                logger.info({
                    "message": "[Leaderboard] Start to call evaluation metrics to calculate team {}'s scores".format(team),
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env'],
                    "team_id": str(team),
                    "num_of_register_team": str(len(self.register_list.keys())),
                    "calculate_date": str(self.cal_date)})
                logger.info({
                    "message": "[Leaderboard] DF team_answer:{}".format(team_answer),
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env'],
                    "team_id": str(team),
                    "num_of_register_team": str(len(self.register_list.keys())),
                    "calculate_date": str(self.cal_date)})
                logger.info({
                    "message": "[Leaderboard] DF ground_truth:{}".format(questions[['qid', 'answer']]),
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env'],
                    "team_id": str(team),
                    "num_of_register_team": str(len(self.register_list.keys())),
                    "calculate_date": str(self.cal_date)})
                s = Evaluation_Metrics(team_answer, questions[['qid', 'answer']])
                _ , total_score = s.get_scores()
                logger.info({
                    "message": "[Leaderboard] team {}'s scores {}".format(team, total_score),
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env'],
                    "team_id": str(team),
                    "num_of_register_team": str(len(self.register_list.keys())),
                    "calculate_date": str(self.cal_date)})
                score['score'] = total_score
                scores.append(score)
        leaderboard = pd.DataFrame(scores)
        logger.info({
                    "message": "[Leaderboard] DF Leaderboard {}".format(leaderboard),
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env']})
        leaderboard['Rank'] = leaderboard['score'].rank(method='min', ascending=False)
        leaderboard['Rank'] = leaderboard.apply(lambda x: int(x['Rank']), axis=1)
        leaderboard = leaderboard.sort_values(by=['Rank'])
        logger.info({
            "message": "[Leaderboard] Finish calculate scores.",
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "rank_list":str(leaderboard['Rank']),
            "num_of_register_team": str(len(self.register_list.keys())),
            "calculate_date": str(self.cal_date)})
        return leaderboard

    def save_to_image(self, leaderboard):
        """
        Save leaderboard to image file.

        Parameters: leaderboard DataFrame
        """
        logger.debug({
            "message": "[Leaderboard] Start save leaderboard to local img file",
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "num_of_register_team": str(len(self.register_list.keys())),
            "calculate_date": str(self.cal_date)})
            
        now_h_s = self.get_now_timestamp().strftime("-%H:%M:%S")
        self.img_name = self.cal_date.strftime("top10-leaderboard-%Y-%m-%d" + now_h_s + ".png")
        self.csv_name = self.cal_date.strftime("all-leaderboard-%Y-%m-%d" + now_h_s + ".csv")
        show_leaderboard = leaderboard[['Rank', 'team_name', 'score']].rename(columns={'Rank':'名次', 'team_name':'隊伍名稱', 'score':'目前總分'})
        ax = self.render_mpl_table(show_leaderboard.iloc[:10], header_columns=0, col_width=5)
        fig = ax.get_figure()
        fig.savefig('/tmp/' + self.img_name)
        logger.debug({
            "message": "[Leaderboard] Finish save leaderboard img at local. Start to upload to gcp bucket",
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "local_file_name": '/tmp/' + self.img_name,
            "num_of_register_team": str(len(self.register_list.keys())),
            "calculate_date": str(self.cal_date)})

        public_img_url = self.upload_blob(self.link_info['gcp_bucket_name'], '/tmp/' + self.img_name, self.img_name)
        show_leaderboard.to_csv('/tmp/' + self.csv_name, index=False)
        logger.debug({
            "message": "[Leaderboard] Finish save leaderboard csv at local. Start to upload to gcp bucket",
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "local_file_name": '/tmp/' + self.csv_name,
            "num_of_register_team": str(len(self.register_list.keys())),
            "calculate_date": str(self.cal_date)})
            
        public_csv_url = self.upload_blob(self.link_info['gcp_bucket_name'], '/tmp/' + self.csv_name, self.csv_name)
        return public_img_url, public_csv_url

    def send(self):
        """
        Send leaderboard to channel.
        """
        if self.cal_date is None:
            self.cal_date = self.get_latest_date()
        else:
            self.cal_date = pd.to_datetime(self.cal_date).date()
        logger.info({
            "message": "[Leaderboard] Calculate date is {}".format(self.cal_date),
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "calculate_date": str(self.cal_date)
            })

        self.register_list = self.get_register_list()
        leaderboard = self.get_leaderboard()
        public_img_url, public_csv_url = self.save_to_image(leaderboard)
        logger.info({
            "message": "[Leaderboard] Finish public leaderboard img and csv, start to post to public channel.",
            "trigger": "Leaderboard",
            "ENV": self.link_info['env'],
            "public_img_url": public_img_url,
            "public_csv_url": public_csv_url,
            "num_of_register_team": str(len(self.register_list.keys())),
            "calculate_date": str(self.cal_date)})
        
        myobj2 = {
            "token":self.link_info['bot_token'],
            "channel":self.link_info['competition_channel'],
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "各位參賽者好，圖片顯示截至今日積分前十名的參賽者，圖片下方連結可檢視全部的排名，恭喜目前前十名的參賽者！"
                    }
                },
                {
                    "type": "image",
                    "title": {
                        "type": "plain_text",
                        "text": ":star2: Top 10 of the day",
                        "emoji": True
                    },
                    "image_url": public_img_url,
                    "alt_text": "Top 10 of the day"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "完整的 leaderboard 看這邊 👉 <" + public_csv_url + "|Leaderboard of the Day>"
                    }
                }
            ]
        }

        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer ' + self.link_info['bot_token']    
        }
        r = requests.post(self.slack_url, data=json.dumps(myobj2), headers=headers)
        if r.status_code == 200:
            logger.info({
                "message": "[E.SUN Reply Success!] Send leaderboard to channel ",
                "trigger": "Leaderboard",
                "ENV": self.link_info['env'],
                "slack_channel": self.link_info['competition_channel'],
                "posted_data": json.dumps(myobj2),
                "calculate_date": str(self.cal_date)})
        else:
            logger.critical({
                "message": "[E.SUN Reply Failed!] Failed sending leaderboard to channel",
                "trigger": "Leaderboard",
                "ENV": self.link_info['env'],
                "slack_channel": self.link_info['competition_channel'],
                "posted_data": json.dumps(myobj2),
                "response": str(r),
                "calculate_date": str(self.cal_date) })

        sqlstring = sql.SQL(
            """
                Update daily_task_status SET status=0 where status=1;
            """
        )
        try:
            with self.create_connection() as conn:
                with conn.cursor() as source_cur:
                    source_cur.execute(sqlstring)
                    conn.commit()
            logger.info({
                    "message":"[Leaderboard] Update daily task control table status to 0 success",
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env']})
        except Exception as error:
            logger.error({
                    "message":"[Leaderboard] DB update status code Error: {} ".format(error),
                    "trigger": "Leaderboard",
                    "ENV": self.link_info['env']})

def main():
    sender = Send_Leaderboard()
    sender.send()

if __name__ == '__main__':
    main()
