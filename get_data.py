import requests
import json
import pandas as pd
from io import StringIO
import csv
import os
import time
import yfinance as yf
from bs4 import BeautifulSoup

TWSE_investmentbanks = 'https://www.twse.com.tw/rwd/zh/fund/TWT44U?date={TIME}&response=json'

TPEX_investmentbanks  = 'https://www.tpex.org.tw/www/zh-tw/insti/sitcStat?type=Daily&date={TIME}&searchType={BUYorSELL}&id=&response=csv'

TWSE_price = 'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL'

TPEX_price = 'https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes'

def caluate_date():
    with open('./data/TWSEandTPEX_opendate.csv', 'r+', encoding='utf-8') as file:
        reader = csv.reader(file)
        opendate_past = list(reader)
        opendate_FromToday = call_yfinance(ticker="0050.TW").index.strftime('%Y-%m-%d')[::-1][:10]
        if len(opendate_past) == 0 :
            return 10,opendate_FromToday

        opendate_tensago = opendate_FromToday[9]
        position = None
        for i, sublist in enumerate(opendate_past[0]):
            if opendate_tensago in sublist:
                position = i +1
                break
        print(f"有{10 if position == None else 10-position}天的資料未下載")
        return 10 if position == None else 10-position , opendate_FromToday

def update_CHECKandDATA(howManyDaysNeedToGet,opendate_FromToday):
    # update data(remove old data)
    folder_path = "./data/untreated_data"
    date_list = {date.replace('-','') for date in opendate_FromToday}

    for filename in os.listdir(folder_path):
        parts = filename.split("_")
        if parts and parts[-1].endswith(".csv"):
            date_part = parts[-1].replace(".csv", "")
            if date_part not in date_list:
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)
                print(f"已刪除: {filename}")
    print("完成-刪除舊資料")
    # update TWSEandTPEX_opendate
    file_path = "./data/TWSEandTPEX_opendate.csv"
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"已刪除: {file_path}")
    df = pd.DataFrame(columns=list(opendate_FromToday))
    df.to_csv(file_path, index=False, encoding="utf-8")
    print("完成-更新資料")

def caluate_investmentbanks_avgBS(howManyDaysNeedToGet,opendate_FromToday):
    all_data = pd.read_csv('./data/all.csv')
    all_data["前9日加總買賣超"] = 0
    all_data["當日投信買賣超"] = 0

    for i in range(howManyDaysNeedToGet):
        time_today = opendate_FromToday[i].replace('-', '')
        index_str = "當日投信買賣超" if i == 0 else "前9日加總買賣超"
        byorsell_data = pd.read_csv(f"./data/untreated_data/twse_investmentbanks_{time_today}.csv")
        for j,company_name in enumerate(byorsell_data[byorsell_data.columns[1]]):
            stock_code = str(company_name).strip()
            matching_rows = all_data[all_data['股票代號'].astype(str).str.strip() == stock_code]
            
            if not matching_rows.empty:
                index_val = matching_rows.index[0]
                all_data.loc[index_val, index_str] += round(int(str(byorsell_data[byorsell_data.columns[5]][j]).replace(',', '')) /1000)
        print(f"已計算{time_today}的上市投信買賣超")

        byorsell_data = pd.read_csv(f"./data/untreated_data/tpex_investmentbanks_buy_{time_today}.csv")
        for j,company_name in enumerate(byorsell_data[byorsell_data.columns[2]]):
            stock_code = str(company_name).strip()[:4]
            matching_rows = all_data[all_data['股票代號'].astype(str).str.strip() == stock_code]
            if not matching_rows.empty:
                index_val = matching_rows.index[0]
                all_data.loc[index_val, index_str] += int(float(str(byorsell_data[byorsell_data.columns[6]][j]).replace(',', '')))
        print(f"已計算{time_today}的上櫃投信買超")

        byorsell_data = pd.read_csv(f"./data/untreated_data/tpex_investmentbanks_sell_{time_today}.csv")
        for j,company_name in enumerate(byorsell_data[byorsell_data.columns[2]]):
            stock_code = str(company_name).strip()[:4]
            matching_rows = all_data[all_data['股票代號'].astype(str).str.strip() == stock_code]
            if not matching_rows.empty:
                index_val = matching_rows.index[0]
                all_data.loc[index_val, index_str] += int(float(str(byorsell_data[byorsell_data.columns[6]][j]).replace(',', '')))
        print(f"已計算{time_today}的上櫃投信賣超")
        
    all_data.to_csv('./data/all.csv', index=False, encoding='utf-8')

def get_rail_data(howManyDaysNeedToGet,opendate_FromToday):
    
    # TWSE_investmentbanks TPEX_investmentbanks
    for i in range(howManyDaysNeedToGet):
        time_str = opendate_FromToday[i].replace('-', '')

        if os.path.exists(f"./data/untreated_data/twse_investmentbanks_{time_str}.csv"):
            print(f"已下載過資料:twse_investmentbanks_{time_str}.csv")
        else:
            url = TWSE_investmentbanks.format(TIME=time_str)
            download(url=url,ticker=f"twse_investmentbanks_{time_str}",filetype="json")
    
        time_str  = opendate_FromToday[i].replace('-', '%2F')
        time_str_name = opendate_FromToday[i].replace('-', '')
        
        if os.path.exists(f"./data/untreated_data/tpex_investmentbanks_buy_{time_str_name}.csv"):
            print(f"已下載過資料:tpex_investmentbanks_buy_{time_str_name}.csv")
        else:
            url = TPEX_investmentbanks.format(TIME=time_str,BUYorSELL="buy")
            download(url=url,ticker=f"tpex_investmentbanks_buy_{time_str}",filetype="csv")
        
        if os.path.exists(f"./data/untreated_data/tpex_investmentbanks_sell_{time_str_name}.csv"):
            print(f"已下載過資料:tpex_investmentbanks_sell_{time_str_name}.csv")
        else: 
            url = TPEX_investmentbanks.format(TIME=time_str,BUYorSELL="sell")
            download(url=url,ticker=f"tpex_investmentbanks_sell_{time_str}",filetype="csv")

        time.sleep(1)
    get_today_price()
    caluate_investmentbanks_avgBS(howManyDaysNeedToGet,opendate_FromToday)

def call_yfinance(ticker="",howlongfromToday="1mo"):
    data = yf.Tickers(ticker).history(period=howlongfromToday)
    return data

def get_today_price():
    try:
        headers = {
            "accept": "text/csv"
        }
        response = requests.get(TWSE_price, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        df_twse = pd.read_csv(StringIO(response.text))

        response = requests.get(TPEX_price, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        df_tpex = pd.read_csv(StringIO(response.text))

        all_data = pd.read_csv('./data/all.csv')
        all_data["今日價格"] = None

        for i,company_name in enumerate(all_data[all_data.columns[0]]):
            if(all_data[all_data.columns[2]][i] == 1):#上櫃
                stock_code = str(company_name).strip()
                matching_rows = df_tpex[df_tpex['代號'].astype(str).str.strip() == stock_code]
                if not matching_rows.empty:
                    index_val = matching_rows.index[0]
                    all_data.loc[i,"今日價格"] = df_tpex.loc[index_val, '收盤'] 
                else:
                    print(f"找不到股票代號: {stock_code}")
            else:#上市
                stock_code = str(company_name).strip()
                matching_rows = df_twse[df_twse['證券代號'].astype(str).str.strip() == stock_code]
                if not matching_rows.empty:
                    index_val = matching_rows.index[0]
                    all_data.loc[i,"今日價格"] = df_twse.loc[index_val, "收盤價"] 
                else:
                    print(f"找不到股票代號: {stock_code}")
        print(f"成功下載今日上市公司價格資料")
        all_data.to_csv('./data/all.csv', index=False, encoding='utf-8')
    except requests.exceptions.RequestException as e:
        print(f"發生錯誤：{e}")

def download(url="",ticker="",filetype=""):
    try:        
        if filetype == "yfinance":#api有限制請求所以放棄改用證交所&櫃買中心api
            all_data = pd.read_csv('./data/all.csv')
            all_data["今日價格"] = None
            ticker_str = ""
            length = len(all_data[all_data.columns[0]])
            for i,company_name in enumerate(all_data[all_data.columns[0]]):
                ticker_str += f"{company_name}.TW{'' if all_data[all_data.columns[2]][i] == 0 else 'O'} "
                if ( i + 1 ) % 100 == 0 or i == length -1:
                    while True:
                        try:        
                            prices = call_yfinance(
                                ticker=ticker_str,
                                howlongfromToday='1d'
                            )["Close"].items()
                            break
                        except Exception as e:
                            if "Too Many Requests" in str(e):
                                print("YFRateLimitError occurred: waiting 60 seconds, then retrying...")
                                time.sleep(60)
                            else:
                                raise e
                    j = 99 if i != length -1 else length % 100 - 1
                    for ticker, price in prices:
                        all_data.loc[i-j,"今日價格"] = round(float(str(price).split()[2]),2)
                        j-=1
                    ticker_str = ""
                    time.sleep(2)
            all_data.to_csv('./data/all.csv', index=False, encoding='utf-8')          
            return 
        elif filetype == "json":
            try:
                response = requests.get(url)
                response.raise_for_status() 
                json_data = response.json()
                df = pd.DataFrame(json_data["data"], columns=json_data["fields"])
                df = df.drop(df.columns[0],axis=1)
            except (ValueError, requests.exceptions.RequestException) as e:
                print(f"轉換失敗：{e}")
        elif filetype == "csv":
            response = requests.get(url)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text), skiprows=1)
            df = df[:-1]
            df.reset_index(drop=True, inplace=True)
            ticker = ticker.replace("%2F","")
        else:
            print("請輸入正確的檔案格式")
        
        df.to_csv(f"./data/untreated_data/{ticker}.csv", encoding='utf-8')
        print(f"成功下載資料:{ticker}.csv")

    except requests.exceptions.RequestException as e:
        print(f"發生錯誤：{e}")

def updateCompany():
    try:
        twse_company_url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
        tpex_company_url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=4'

        response = requests.get(twse_company_url)
        response.raise_for_status()
        html_content_twse = response.text 
        
        response = requests.get(tpex_company_url)
        response.raise_for_status()
        html_content_tpex = response.text 

        updateCompany_clean(html_content_tpex,html_content_twse)

    except requests.exceptions.RequestException as e:
        print(f"發生錯誤：{e}")
    except Exception as e:
        print(f"發生未預期的錯誤：{e}")

def updateCompany_clean(html_content_tpex,html_content_twse):

    soup = BeautifulSoup(html_content_tpex, 'html.parser')
    results_tpex = []
    jud = False
    for row in soup.find_all('tr'):
        text = row.find('td').get_text(strip=True)
        if text in ('股票', '特別股'):
            jud ^= True
            continue
        if text and jud:
            temp = text.split("\u3000")
            results_tpex.append([temp[0],temp[1],1])

    soup = BeautifulSoup(html_content_twse, 'html.parser')
    results_twse = []
    for i, row in enumerate(soup.find_all('tr')):
        text = row.find('td').get_text(strip=True)
        if text and text == '上市認購(售)權證':
            break
        if text and i > 1:
            temp = text.split("\u3000")
            results_twse.append([temp[0], temp[1], 0])

    final = results_tpex + results_twse

    columns = ["股票代號","公司名稱","上市/櫃"]
    df = pd.DataFrame(final, columns=columns)
    df.to_csv("./data/company.csv", index=False, encoding="utf-8")

def result():
    find_company = []
    all_data = pd.read_csv('./data/all.csv')
    for i,company_name in enumerate(all_data[all_data.columns[0]]):
        price = all_data.loc[i,'今日價格']
        nine_days = all_data.loc[i,'前9日加總買賣超']
        today = all_data.loc[i,'當日投信買賣超']
        try:
            price = float(price) if price is not None else None
            nine_days = float(nine_days) if nine_days is not None else None
            today = float(today) if today is not None else None
        except ValueError:
            continue

        if abs(nine_days) <= 5:
            if today != 0:
                if abs(price * today) >= 30000:
                    find_company.append(company_name)
    print(find_company) 

def main():
    howManyDaysNeedToGet,opendate_FromToday = caluate_date()
    get_rail_data(howManyDaysNeedToGet,opendate_FromToday)
    update_CHECKandDATA(howManyDaysNeedToGet,opendate_FromToday)
    result()

if __name__ == "__main__":
    main()

"""
# 開發進度
- [OK✅] know how many didn't load->(to reduce request same day data)
- [OK✅] Update Company List
- dowload_data-> 
    - use https request to get investmentbanks data [OK✅] 
        - [OK✅] get rail data
        - [OK✅] clean data 
    - yfinace to get today price [🆘]下載api時間太久->[OK✅]更換api
        - [OK✅] get rail data
        - [OK✅] clean data 
- refresh data->
    - [OK✅] modify the date
    - [OK✅] caluate the avg BS
    - [OK✅] update the data
- [OK✅] compute the result->
- use LINE send to the user

# 測試進度
"""
