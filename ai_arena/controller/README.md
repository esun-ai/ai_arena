<p align="center">
  <a href="./README.md"> English </a> | <a href="./README.zh-TW.md"> 繁體中文
</p>

## Controller

This component is responsible for the following:
- ``/verify_url``: Receive the request sent by slack_msg_consumer, so that the contestant can use the slack ``verifictaion`` command to verify the scoring system mechanism.
- ``/create_sub``: When a contestant uses the ``register`` command in slack, a subscription named team_id will be added to the lake topic.
- ``/get_teams`` : Get a list of all teams with verified servers before the online competition starts.

