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

import os
import pandas as pd
from datetime import datetime
from src.logger import logger

class Evaluation_Metrics():
    def __init__(self, prediction, ground_truth):
        """
        Get the evaluated metrics.

        Parameters:
          - prediction: the competitor's prediction DataFrame
          - ground_truth: the answer DataFrame
        """
        self.prediction = prediction
        self.ground_truth = ground_truth
        self.env = os.environ['ENV']

    def check_ans_valid(self, row):
        """
        Check the name list is type str or not.

        Return:
          - if name_list is type str, return name_list
          - if not, return None
        """
        if isinstance(row['name_list'], str):
           return row['name_list']
        return None
    
    def int2str(self, row):
        """
        int change to str.

        Return: row['qid']
        """
        if not isinstance(row['qid'], str):
            return str(row['qid'])
        return row['qid']

    def evaluation(self, answer, ground_truth):
        """
        Calculate score of input answer.
    
        Parameters:
               - answer(pd.DataFrame(columns=['qid', 'answer'])),
               - ground_truth(pd.DataFrame(columns=['qid', 'answer']))
        Return: scores(pd.Series)
        """
        ground_truth = ground_truth.rename(columns={'answer':'true_list'})
        ground_truth['qid'] = ground_truth.apply(self.int2str, axis=1)
        answer = answer.rename(columns={'answer':'name_list'})
        answer['qid'] = answer.apply(self.int2str, axis=1)
        comparison = pd.merge(ground_truth, answer,  how="left", on="qid")
        comparison['name_list'] = comparison.apply(self.check_ans_valid, axis=1)
        comparison['correct'] = comparison['name_list'] == comparison['true_list']
        res_recall = (comparison.groupby(['true_list'])
                .agg({'true_list':'count', 'correct': 'sum'})
                .rename(columns={'true_list':'total'}))
        res_precision = (comparison.groupby(['name_list'])
                .agg({'name_list':'count', 'correct': 'sum'})
                .rename(columns={'name_list':'total'}))
        res_recall = res_recall['correct'] / res_recall['total']
        res_precision = res_precision['correct'] / res_precision['total']
        recall_df = pd.DataFrame({'gt':res_recall.index, 'recall':res_recall.values})
        precision_df = pd.DataFrame({'gt':res_precision.index, 'precision':res_precision.values})
        out_df = pd.merge(recall_df, precision_df,  how='left', on='gt')
        return (2 * (out_df['precision'] * out_df['recall']) / (out_df['precision'] + out_df['recall'])).fillna(0)

    def get_scores(self):
        """
        Calculate score.

        Return:
          - score_series: list
          - total_score: int
        """
        try:
            score_series = self.evaluation(self.prediction, self.ground_truth)
            total_score = score_series.mean()
            return score_series, total_score
        except Exception as error:
            logger.warning({
                "message": "[Leaderboard] This team cannot get scores: {}.".format(error),
                "trigger": "Leaderboard",
                "ENV": self.env,
                "timestamp": str(datetime.now())
            })
            return None, 0

if __name__=='__main__':
    ## Example
    prediction = pd.DataFrame(
        data={
            "qid": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10 , 11, 12],
            "answer": ['玉', '山', '王', '玉', '山', '山', '金', '銓', 'isnull', '融', '智', 'isnull']
        }
    )
    ground_truth = pd.DataFrame(
        data={
            "qid": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10 , 11, 12],
            "answer": ['玉', '玉', '玉', '玉', '山', '山', '金', '金', '融', '融', 'isnull', 'isnull'],
        }
    )
    s = Evaluation_Metrics(prediction, ground_truth)
    score_series, total_score = s.get_scores()
    print("===== scores =====")
    logger.info({
            "message": "[Leaderboard] Score Series: {}".format(score_series),
            "trigger": "Leaderboard",
            "ENV": os.environ['ENV']
            })
    logger.info({
            "message": "[Leaderboard] Total score: {}".format(total_score),
            "trigger": "Leaderboard",
            "ENV": os.environ['ENV']
            })
