import time
import pyupbit
import datetime

access = "U5xb4ihuULs6I9se0g467KyNnaSwVybGlyWHTwQp"
secret = "HVowWtMp0w2FeyxiaqQqOM4tprqyPxaBfDZ9eEMx"

# def get_target_price(ticker, k):
#     """변동성 돌파 전략으로 매수 목표가 조회"""
#     df = pyupbit.get_ohlcv(ticker, interval="minute10", count=2)
#     target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
#     return target_price

# def get_range(ticker):
#     df = pyupbit.get_ohlcv(ticker, interval="minute10", count=2)
#     range = df.iloc[0]['high'] - df.iloc[0]['low']
#     return range

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=1)
    start_time = df.index[0]
    return start_time

def get_low(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=2)
    low = df.iloc[0]['low']
    return low

def get_open(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=1)
    open = df.iloc[0]['open']
    return open

def get_ma2(ticker):
    """2일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=2)
    ma2 = df['close'].rolling(2).mean().iloc[-1]
    return ma2

def get_ma3(ticker):
    """3일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=3)
    ma3 = df['close'].rolling(3).mean().iloc[-1]
    return ma3

def get_ma4(ticker):
    """4일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=4)
    ma4 = df['close'].rolling(4).mean().iloc[-1]
    return ma4

def get_ma20(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=20)
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
buy_sell = 0
max_price = 0
drop_sell = 0
low_buy = 0
buy_price = 0
# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-GMT")
        end_time = start_time + datetime.timedelta(minutes=10)

        if start_time + datetime.timedelta(seconds=3) < now < end_time:
            current_price = get_current_price("KRW-GMT")
            # target_price = get_target_price("KRW-GMT", 0.333334)
            open = get_open("KRW-GMT")
            low = get_low("KRW-GMT")
            ma2 = get_ma2("KRW-GMT")
            ma3 = get_ma3("KRW-GMT")
            ma4 = get_ma4("KRW-GMT")            
            ma20 = get_ma20("KRW-GMT")

            if (0 < current_price < 0.1):
                under = 0.0001
            elif (0.1 <= current_price < 1):
                under = 0.001
            elif (1 <= current_price < 10):
                under = 0.01
            elif (10 <= current_price < 100):
                under = 0.1
            elif (100 <= current_price < 1005):
                under = 1
            elif (1000 <= current_price < 10000):
                under = 5
            elif (10000 <= current_price < 100000):
                under = 10
            elif (100000 <= current_price < 500000):
                under = 50
            elif (500000 <= current_price < 1000000):
                under = 100
            elif (1000000 <= current_price < 2000000):
                under = 500
            elif (2000000 <= current_price):
                under = 1000

            if buy_sell == 1:
                 if max_price < current_price:
                    max_price = current_price

            if buy_sell == 2:
                 if low_buy > current_price:
                    low_buy = current_price

# 매수 조건            
            if buy_sell == 0:

                if ma4 < ma3 < ma2 and current_price > open and current_price > ma20:
                    krw = get_balance("KRW")
                    if (krw*0.35) > 5000:
                        upbit.buy_market_order("KRW-GMT", (krw*0.35) * 0.9995)
                        buy_price = current_price
                        buy_sell = 1
                
            elif buy_sell == 2:
                if current_price > low_buy + under and ma4 < ma3 < ma2 and current_price > open and current_price > ma20:
                    krw = get_balance("KRW")
                    if (krw*0.35) > 5000:
                        upbit.buy_market_order("KRW-GMT", (krw*0.35) * 0.9995)
                        buy_price = current_price
                        low_buy = 0
                        drop_sell = 0
                        buy_sell = 1
# 매도 조건
            elif buy_sell == 1:
                if current_price <= low:
                    btc = get_balance("GMT")
                    if btc > 0:
                        upbit.sell_market_order("KRW-GMT", btc)
                        buy_price = 0
                        max_price = 0
                        buy_sell = 0
                        drop_sell = 0

                if max_price * 0.996 < current_price and buy_price + (under*2) < current_price or buy_price*0.997 > current_price:
                    btc = get_balance("GMT")
                    if btc > 0:
                        upbit.sell_market_order("KRW-GMT", btc)
                        drop_sell = current_price
                        low_buy = current_price
                        buy_price = 0
                        max_price = 0
                        buy_sell = 2

        else:
            if buy_sell == 2:
                drop_sell = 0
                max_price = 0
                buy_sell = 0


        time.sleep(1)
        print(now,"    CP: %.2f    Ma:  %s    under: %.2f    buy_price: %.2f    open: %.2f    drop_sell: %.2f    sell_price: %.2f    low: %.2f  low_buy: %.2f" %
             (current_price, (ma2>ma3>ma4), under, buy_price, open, drop_sell, max_price * 0.997, low, low_buy))
  
    except Exception as e:
        print(e)
        time.sleep(0.3)
