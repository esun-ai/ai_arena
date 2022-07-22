<p align="center">
  <a href="./README.md"> English </a> | <a href="./README.zh-TW.md"> 繁體中文
</p>


## Leaderboard
此元件是負責處理計算參賽者成績，若計算完成，則將計算後的資料寄送至 slack 發佈。

## Docker Instruction
我們可以使用 GCP，您可以使用嘗試以下的指令。
```
docker build -t gcr.io/{{YOUR_PROJECT}}/{{YOUR_IMAGE_NAME}}:{{YOUR_TAG}} -f ./Dockerfile .
docker push gcr.io/{{YOUR_PROJECT}}/{{YOUR_IMAGE_NAME}}:{{YOUR_TAG}}
```
