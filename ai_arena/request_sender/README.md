<p align="center">
  <a href="./README.md"> English </a> | <a href="./README.zh-TW.md"> 繁體中文
</p>

## Request sender
This element is the interface between the system and the contestants.
- Before the competition starts: verify whether the client server can receive the request, confirm whether the response information is correct, and
reply to slack.
- When the competition starts: responsible for calling the contestants on the topics from controller pubish to sea topic,
receive the contestant response, and recorded in the DB.
