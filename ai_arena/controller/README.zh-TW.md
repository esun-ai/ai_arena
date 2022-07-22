<p align="center">
  <a href="./README.md"> English </a> | <a href="./README.zh-TW.md"> 繁體中文
</p>

## Controller

此元件為負責以下事項：
- ``/verify_url``: 接收 slack_msg_consumer 發的 request，讓參賽者能利用 slack ``verifictaion``的 command驗證一次評分系統機制。
- ``/create_sub``: 參賽者在 slack 使用 ``register``指令時，會在 lake topic 新增一個以 team_id 為名的subscription。
- ``/get_teams`` : 在線上競賽開始前，取得所有有驗證過server的隊伍清單。
