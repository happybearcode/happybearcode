import time
import pyupbit
import datetime
import numpy as np

access = "U5xb4ihuULs6I9se0g467KyNnaSwVybGlyWHTwQp"
secret = "HVowWtMp0w2FeyxiaqQqOM4tprqyPxaBfDZ9eEMx"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=2)
    range = (df.iloc[0]['open'] - df.iloc[0]['close']) * k
    target_price = np.where(df.iloc[0]['open'] > df.iloc[0]['open'] + range,
                        df.iloc[1]['open'] + (range * -1),
                        df.iloc[1]['open'] + range)

    # print("target_price: %f close: %f high: %f low: %f open: %f open2: %f range: %f" % (target_price, df.iloc[0]['close'], df.iloc[0]['high'], df.iloc[0]['low'], df.iloc[0]['open'], df.iloc[1]['open'], range))
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=1)
    start_time = df.index[0]
    return start_time

def get_ma7(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=5)
    ma7 = df['close'].rolling(5).mean().iloc[-1]
    return ma7

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
        end_time = start_time + datetime.timedelta(minutes=30)

        if start_time < now < end_time - datetime.timedelta(seconds=1):
            target_price = get_target_price("KRW-ZRX", 0)
            ma7 = get_ma7("KRW-ZRX")
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
            if target_price < current_price and ma7 < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-ZRX", krw*0.2)
                    time.sleep(0.5)
# 매도명령 타겟가 보다 하락시 판매
            if target_price > (current_price + under):
                btc = get_balance("ZRX")
                if btc > 0:
                    upbit.sell_market_order("KRW-ZRX", btc)
                    max_price = target_price
                 
        
        else:
            btc = get_balance("ZRX")
            if btc > 0:
                upbit.sell_market_order("KRW-ZRX", btc)
                

#         elif (max_price < current_price):
#              max_price = current_price

# # 매도명령 HIGH
#         if max_price > current_price and current_price > (target_price + under + under):
#             if max_price > current_price + under +under:
#                 btc = get_balance("ZRX")
#                 if btc > 0:
#                     upbit.sell_market_order("KRW-ZRX", btc)
#                     max_price = current_price


        time.sleep(0.3)
        # print(now,"TP: %s  CP: %s  Max_P: %s  MA5: %s    HighSell_P: %s  LowSell_P: %s" %
        #      (target_price, current_price, max_price, (ma7 < current_price), (max_price-under-under-under), (target_price-under-under)))
    except Exception as e:
        print(e)
        time.sleep(0.3)
