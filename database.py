import urllib.parse
import psycopg
import os

conn = None
cursor = None

def get_connection_uri():

    # Read URI parameters from the environment
    dbhost = os.environ['DBHOST']
    dbname = os.environ['DBNAME']
    dbuser = urllib.parse.quote(os.environ['DBUSER'])
    password = os.environ['DBPASSWORD']
    sslmode = os.environ['SSLMODE']
    db_uri = f"host={dbhost} dbname={dbname} user={dbuser} password={password} sslmode={sslmode}"
    # Construct connection URI
    return db_uri

def get_connection():
    conn_string = get_connection_uri()
    conn = psycopg.connect(conn_string)
    print("Connection established")
    return conn,conn.cursor()

def close_connection(conn,cursor):
    conn.commit()
    cursor.close()
    conn.close()

def get_subscribers():
    try:
        if conn is None or cursor is None: conn, cursor = get_connection()
        cursor.execute("SELECT * FROM linebot")
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(e)
        return False

def add_subscriber(line_chat_id):
    try:
        if conn is None or cursor is None: conn, cursor = get_connection()
        cursor.execute("""
            INSERT INTO linebot (line_chat_id)
            VALUES (%s)
        """,(line_chat_id))
        return True
    except Exception as e:
        print(e)
        return False

def delete_subscriber(line_chat_id):
    try:
        if conn is None or cursor is None: conn, cursor = get_connection()
        cursor.execute("DELETE FROM linebot WHERE line_chat_id = %s",(line_chat_id))
        return True
    except Exception as e:
        print(e)
        return False

def add_stock(stock_date,company_name,company_code,price,investmentbank_volume):
    try:
        if conn is None or cursor is None: conn, cursor = get_connection()
        cursor.execute("""
            INSERT INTO stock_info (stock_date, company_name, company_code, price, investmentbank_volume)
            VALUES (%s,%s,%s,%s,%s)
        """,(stock_date,company_name,company_code,price,investmentbank_volume))
        return True
    except Exception as e:
        print(e)
        return False

def get_stock():
    try:
        if conn is None or cursor is None: conn, cursor = get_connection()
        cursor.execute("SELECT * FROM stock_info")
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(e)
        return False

def get_result(time):
    stockdata = [stock for stock in get_stock() if stock[1] == time]
    if len(stockdata) == 0:
        return "今日無符合條件的股票"
    result_str = f"今日({time})符合條件的有:\n"
    for stock in stockdata:
        result_str += f"{stock[2]}{str(stock[3])} 今日收盤價格{str(stock[4])} 買賣超{str(stock[4]*stock[5]/10)}萬元\n"
    return result_str