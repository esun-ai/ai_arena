#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import json
from flask import abort
from flask import Flask
from flask import request

from src.utils.logger import logger
from src.api_base import APIBase

project_id = os.environ['PROJECT_ID']
env = os.environ['ENV']

# set flask
app = Flask(__name__)
logger.info(f"[Controller] Start controller server at {env}...") 


@app.route("/create_sub", methods=["POST"])
def create_sub():
    """
    Create subscription for team
    Args:
        request body(json):
                team_id(string): team id
    Return:
        status code
    Raises:
        510 error: summary of runtime error message
    """
    data = json.loads(request.get_data().decode("utf-8"))
    try:
        logger.info({'message':f'[Controller] Create subscription for team_{data["team_id"]}',
                           'team_id': data["team_id"],
                           'ENV': env})
        API.create_sub(data["team_id"])
        return f'Create subscription for team {data["team_id"]} succeeded.'
    except Exception as error:
        logger.error({'message':'[Controller] create sub failed',
                           'team_id':data["team_id"],
                           'error_message': str(error),
                           'ENV': env})    
        abort(510, description = str(error))

@app.route("/list_sub", methods=["GET"])
def list_sub():
    """
    Get subscriptions in lake topic
    Args:
        None
    Return:
        subscriptions(list): all subscription in lake topic 
    Raises:
        510 error: summary of runtime error message
    """
    try:
        logger.info({'message':f'[Controller] Get subscription',
                           'ENV': env})
        return API.get_sub()
    except Exception as error:
        logger.error({'message':'[Controller] Get sub failed',
                           'error_message': str(error),
                           'ENV': env})    
        abort(510, description = str(error))

@app.route("/delete_sub", methods=["POST"])
def delete_sub():
    """
    Delete subscription for team
    Args:
        request body(json):
                team_id(string): team id
    Return:
        status code
    Raises:
        510 error: summary of runtime error message
    """
    data = json.loads(request.get_data().decode("utf-8"))
    try:
        logger.info({'message':f'[Controller] Delete subscription for team_{data["team_id"]}',
                           'team_id': data["team_id"],
                           'ENV': env})
        API.delete_sub(data['team_id'])
        return f'delete subscription for team_{data["team_id"]} succeeded'
    except Exception as error:
        logger.error({'message':'[Controller] Delete sub failed',
                           'error_message': str(error),
                           'ENV': env})
        abort(510, description = str(error))
    

@app.route("/verify_url", methods=["POST"])
def verify_url():
    """
    Verify team's api service
    Args:
        request body(json):
                team_id(string): team id
                team_url(string): team api url e.g. 10.0.0.1:8080
    Return:
        status code
    Raises:
        510 error: summary of runtime error message
    """
    data = json.loads(request.get_data().decode("utf-8"))
    try:
        logger.info({'message':f'[Controller] Verify url for team_{data["team_id"]}',
                           'team_id':data["team_id"],
                           'team_url':data["team_url"],
                           'ENV': env})
        API.verify_team_url(data)
        return f"published verify task succeeded"
    except Exception as error:
        logger.error({'message':'[Controller] Verify_team_url failed',
                           'error_message': str(error),
                           'ENV': env})
        abort(510, description = str(error))


@app.route('/get_teams', methods=['POST'])
def get_teams():
    """
    Update daily task status
    Get all verified team before start competition
    Publish all verified team to generator
    Args:
        request body(json):
                date(string, optional): competition date
    Return:
        status code
    Raises:
        510 error: summary of runtime error message
    """
    logger.info(f'[Controller] Start get teams at {env}')
    data = json.loads(request.get_data().decode("utf-8"))
    try:
        API.update_daily_task_status_table()
        result = API.pub_teams(data['date'])
    except Exception as error:
        abort(510,description=f'run daily job failed: {error}')
    
    logger.info(f'[Controller] All teams task sent at {env}')

    return "generate task succeeded"

@app.route('/unit_team', methods=['POST'])
def unit_teams():
    """
    Get Specified verified team
    Publish Specified verified team to generator
    Args:
        request body(json):
                team_id(string): team id
                date(string, optional): competition date
    Return:
        status code
    Raises:
        510 error: summary of runtime error message
    """
    data = json.loads(request.get_data().decode("utf-8"))
    logger.info(f'[Controller] start unit_team for team_{data["team_id"]}')
    try:
        result = API.pub_unit_teams(data['team_id'],data['date'])
    except Exception as error:
        abort(510,description=f'generate questions failed: {error}')
    
    logger.info(f'[Controller] All task sent at for team_{data["team_id"]}, date: {data["date"]}')

    return "generate task succeeded"

@app.route('/warmup')
def warmup():
    # Handle your warmup logic here, e.g. set up a database connection pool
    return '', 200, {}


if __name__ == '__main__':
    API = APIBase()
    app.run(host = '0.0.0.0', port = 8080, debug = True)
