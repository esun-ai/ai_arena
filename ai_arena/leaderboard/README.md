<p align="center">
  <a href="./README.md"> English </a> | <a href="./README.zh-TW.md"> 繁體中文
</p>


## Leaderboard
This component is responsible for calculating the competitors' scores. Once it has finished, it would send scores to slack.

## Docker Instruction
We can use GCP, and you can use try the following commands.
```
docker build -t gcr.io/{{YOUR_PROJECT}}/{{YOUR_IMAGE_NAME}}:{{YOUR_TAG}} -f ./Dockerfile .
docker push gcr.io/{{YOUR_PROJECT}}/{{YOUR_IMAGE_NAME}}:{{YOUR_TAG}}
```
