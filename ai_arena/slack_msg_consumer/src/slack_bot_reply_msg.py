#!/usr/bin/env python
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
class ReplyMessage:

    # general usage
    SYSTEM_ERROR = """主辦單位系統內部錯誤，可私訊 Slack bot 與主辦單位聯繫，\n
並提供您於 T-Brain 註冊的 email，謝謝"""
    USAGE_GUIDE = """Usage:\n
forget_token [email_of_team_leader]\t重發手機認證碼\n
register [email_of_team_leader] [phone_token_of_team_leader]\t註冊正式賽\n
verification [email_of_team_leader] [phone_token_of_team_leader] http://[external_IP_of_your_VM]:[port_of_your_API]\t測試並驗證 API\n
get_status [email_of_team_leader] [phone_token_of_team_leader]\t查詢最後一次驗證 API 狀態\n
get_log [email_of_team_leader] [phone_token_of_team_leader] [date_for_query]\t測試賽後開放查詢比賽 log\n
若想看詳細說明請參照 <放競賽說明連結>"""
    CONTACT_INFO = "，若仍有疑問可私訊 Slack bot 與主辦單位聯繫，並提供您於 T-Brain 註冊的 email 與 API URL，謝謝"
    EMAIL_FORMAT_ERROR = "請輸入正確的 email 格式"
    TOKEN_FORMAT_ERROR = "請輸入正確的手機驗證碼格式：手機驗證碼為 6 碼數字"
    TOKEN_ERROR = "驗證失敗：手機驗證碼錯誤"
    # get_log
    GET_LOG_FORMAT_ERROR = "請輸入正確的 get_log 格式：get_log [email_of_team_leader] [phone_token_of_team_leader] [date_for_query]\ndate_for_query 為 optional"
    GET_LOG_CLOSED = "比賽進行中，get_log 功能關閉"
    DATE_FORMAT_ERROR = "請輸入正確的日期格式：YYYY-MM-DD"
    # verification
    VERIFY_FAILED = "驗證失敗，請再次檢查您所輸入的 email、手機驗證碼或 API URL 是否正確" + CONTACT_INFO
    API_URL_FROMAT_ERROR = "此 API URL 不符規定，請再檢查 API URL 是否正確" + CONTACT_INFO
    VERIFICATION_SUCCESS_RES = """已發送驗證題目給您，將於驗證完成時告知驗證結果，請稍候...\n 
若於 1 分鐘後仍無收到驗證結果通知可私訊 Slack bot 與主辦單位聯繫"""

    @staticmethod
    def get_no_log_res(date_for_query):
        return f"於您所查詢的日期：{date_for_query} 中並沒有發送題目給您的紀錄，請用 get_status 指令確認您的隊伍是否並未驗證過 API URL{ReplyMessage.CONTACT_INFO}"

    @staticmethod
    def get_no_qid_res(date_for_query):
        res = f"於您所查詢的日期：{date_for_query} 中並沒有測試賽或正式賽發題的紀錄，測試賽期間為 5/24 - 5/26，正式賽期間為 6/15 - 6/18{ReplyMessage.CONTACT_INFO}"
        return res
