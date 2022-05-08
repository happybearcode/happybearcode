import time
import pyupbit
import datetime
import numpy as np

access = "U5xb4ihuULs6I9se0g467KyNnaSwVybGlyWHTwQp"
secret = "HVowWtMp0w2FeyxiaqQqOM4tprqyPxaBfDZ9eEMx"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=2)
    range = (df.iloc[0]['open'] - df.iloc[0]['close']) * k
    target_price = df.iloc[0]['close']
    high = df.iloc[1]['high']
    low = df.iloc[1]['low']

    # print("target_price: %.1f close: %.1f high: %.1f low: %.1f open: %.1f open2: %.1f range: %.1f" % (target_price, df.iloc[0]['close'], df.iloc[0]['high'], df.iloc[0]['low'], df.iloc[0]['open'], df.iloc[1]['open'], range))
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=1)
    start_time = df.index[0]
    return start_time

def get_ma2(ticker):
    """2일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=2)
    ma2 = df['close'].rolling(2).mean().iloc[-1]
    return ma2

def get_ma3(ticker):
    """3일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=3)
    ma3 = df['close'].rolling(3).mean().iloc[-1]
    return ma3

def get_ma4(ticker):
    """4일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=4)
    ma4 = df['close'].rolling(4).mean().iloc[-1]
    return ma4

def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_ma20(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=20)
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    return ma20

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

max_price = 0
# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-ZRX")
        end_time = start_time + datetime.timedelta(minutes=60)

        if start_time < now < end_time + datetime.timedelta(seconds=1):
            target_price = get_target_price("KRW-ZRX", 0)
            ma2 = get_ma2("KRW-ZRX")
            ma3 = get_ma3("KRW-ZRX")
            ma4 = get_ma4("KRW-ZRX")
            ma5 = get_ma5("KRW-ZRX")
            ma20 = get_ma20("KRW-ZRX")
            current_price = get_current_price("KRW-ZRX")
            if (0 < current_price < 1.01):
                under = 0.0001
            elif (1 <= current_price < 10.1):
                under = 0.01
            elif (10.1 <= current_price < 101):
                under = 0.1
            elif (101 <= current_price < 1005):
                under = 1
            elif (1005 <= current_price < 10010):
                under = 5
            elif (10010 <= current_price < 100050):
                under = 10
            elif (100050 <= current_price < 500100):
                under = 50
            elif (500100 <= current_price < 1000500):
                under = 100
            elif (1000500 <= current_price < 2001000):
                under = 500
            elif (2001000 <= current_price):
                under = 1000
            
# 매수 조건
            if current_price > ma2 > ma3 > ma4 > ma5:
                krw = get_balance("KRW")
                if (krw*0.25) > 5000:
                    upbit.buy_market_order("KRW-ZRX", (krw*0.25)*0.9995)
                time.sleep(0.2)
# 매도 조건
            else:
                btc = get_balance("ZRX")
                if btc > 0:
                    upbit.sell_market_order("KRW-ZRX", btc)
       
                

        time.sleep(0.5)
        # print(now,"TP: %.1f  CP: %.1f  Ma2: %.1f  %s  Ma3: %.1f  %s  Ma4: %.1f  %s  Ma5: %.1f  %s under: %.1f" %
        #      (target_price, current_price, ma2, (current_price>ma2), ma3, (ma2>ma3), ma4, (ma3>ma4), ma5, (ma4>ma5), under))
  
    except Exception as e:
        print(e)
        time.sleep(0)
