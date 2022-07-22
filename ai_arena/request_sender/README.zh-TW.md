<p align="center">
  <a href="./README.md"> English </a> | <a href="./README.zh-TW.md"> 繁體中文
</p>

## Request sender
此元件是系統與參賽者接口。
- 比賽開打前: verify 參賽者 server 是否可以接收 request，並確認 response 訊息是否正確，
回覆至 slack。
- 比賽開打: 負責將 controller pubish 到 sea topic的題目打給參賽者，
並接收參賽者 response，記錄在DB中。
