# stock-helper

stock-helper 是一個結合股票資料抓取、處理與推播通知的工具。此專案主要功能包括：

- 從證交所、櫃買中心下載股票資料與投信買賣超資訊
- 透過資料庫記錄與比對資訊，計算出符合條件的股票
- 將結果用 LINE Bot 推播通知訂閱者

## 本地端開發安裝流程

1. **Clone 專案**

```bash
git clone <repository-url>
cd stock-helper
```

2. **建立與啟動虛擬環境**
   在 Windows 下使用 PowerShell：

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **安裝套件**

```bash
pip install -r requirements.txt
```

4. **設定環境變數**
   設定環境變數
   本專案需要如下環境變數 (例如透過系統環境變數或在啟動虛擬環境後於命令列設定)：

- DBHOST：資料庫主機位址
- DBNAME：資料庫名稱
- DBUSER：資料庫使用者
- DBPASSWORD：資料庫密碼
- SSLMODE：Postgres 資料庫連線的 ssl 模式
- LINE_CHANNEL_ACCESS_TOKEN：LINE Channel Access Token
- LINE_CHANNEL_SECRET：LINE Channel Secret
- ADMIN_USER_ID：管理員 LINE 使用者 ID (用於推送全體訊息)

範例在 Windows cmd 中設定

```bash
set DBHOST=<your_db_host>
set DBNAME=<postgres>
set DBUSER=<your_db_user>
set DBPASSWORD=<your_db_password>
set SSLMODE=require
set LINE_CHANNEL_ACCESS_TOKEN=<your_line_access_token>
set LINE_CHANNEL_SECRET=<your_line_channel_secret>
set ADMIN_USER_ID=<your_ADMIN_user_id>
```

## 功能說明

- LINE Bot 使用
  - 使用者可透過與 Bot 傳送特定關鍵字(例如：「訂閱」、「取消」、「推送給所有人」)進行訂閱與取消訂閱以及推播操作。
  - 當系統判斷符合股票條件時，會由 Bot 主動推送最新的股票資訊給訂閱者。
- 資料庫操作
  - database.py 提供連線、關閉連線、以及訂閱者和股票資料的新增、刪除、查詢函式。
  - 請確認資料庫中已正確建立所需的表格，例如 linebot、stock_info 與 compute_history。
- 股票資料抓取與處理
  - stock_info.py 負責從證券交易所與櫃買中心抓取資料、清洗資料以及計算相關指標。
  - 資料會儲存在 /data 資料夾中，部分檔案會在每次執行中更新。

## 開發進度

- 資料抓取：已完成證交所與櫃買中心 API 的資料下載與原始資料清洗。
- 資料處理：可計算並更新投信買賣超金額及股票資訊。
- Line Bot 整合：已實作訂閱、取消訂閱和推送訊息功能。
- 部署運行：部屬在 Azure Function 上。

## 預計開發功能

- 更多樣篩選條件設定
- 處理大量使用者使用情況
- 加入 Line GUI 介面
