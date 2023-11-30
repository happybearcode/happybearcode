#-*-coding:utf-8 -*-
import myUpbit   #우리가 만든 함수들이 들어있는 모듈
import time
import pyupbit
import datetime
import numpy as np
import pandas as pd
from pexpect import ExceptionPexpect
import json

#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
# simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Upbit_AccessKey = "aiweM7aKHUdv6BFDgyHjjwpXlb4t8GS854oOtj5H"
Upbit_ScretKey = "8arwk0KzfYoVawx3GGDKWLh7xlOYkAwzpXV1K5qx"
#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)

def get_open_price(ticker, i):
    df_5 = pyupbit.get_ohlcv(ticker, interval=i, count=1)
    open = df_5.iloc[0]['open']
    return open

def get_low(ticker, i):
    df_5 = pyupbit.get_ohlcv(ticker, interval=i, count=2)
    low = df_5.iloc[0]['low']
    return low

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def GetMA(d, a, b):
    """이동 평균선 조회"""
    ma = d['close'].rolling(a).mean().iloc[b]
    return ma

def GetMACD(ohlcv,st):
    macd_short, macd_long, macd_signal=2,3,2

    ohlcv["MACD_short"]=ohlcv["close"].ewm(span=macd_short).mean()
    ohlcv["MACD_long"]=ohlcv["close"].ewm(span=macd_long).mean()
    ohlcv["MACD"]=ohlcv["MACD_short"] - ohlcv["MACD_long"]
    ohlcv["MACD_signal"]=ohlcv["MACD"].ewm(span=macd_signal).mean() 

    dic_macd = dict()
    
    dic_macd['macd'] = ohlcv["MACD"].iloc[st]
    dic_macd['macd_siginal'] = ohlcv["MACD_signal"].iloc[st]
    dic_macd['ocl'] = dic_macd['macd'] - dic_macd['macd_siginal']

    return dic_macd

def GetStoch(ohlcv,period,st):

    dic_stoch = dict()

    ndays_high = ohlcv['high'].rolling(window=period, min_periods=1).max()
    ndays_low = ohlcv['low'].rolling(window=period, min_periods=1).min()
    fast_k = (ohlcv['close'] - ndays_low)/(ndays_high - ndays_low)*100
    slow_k = fast_k.rolling(window=2, min_periods=1).mean()
    slow_d = slow_k.rolling(window=2, min_periods=1).mean()

    dic_stoch['fast_k'] = fast_k.iloc[st]
    dic_stoch['slow_k'] = slow_k.iloc[st]
    dic_stoch['slow_d'] = slow_d.iloc[st]
    
    return dic_stoch

#RSI지표 수치를 구해준다. 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
def GetRSI(ohlcv,period):
    #이 안의 내용이 어려우시죠? 넘어가셔도 되요. 우리는 이 함수가 RSI지표를 정확히 구해준다는 것만 알면 됩니다.
    dic_RSI = dict()

    ohlcv["close"] = ohlcv["close"]
    delta = ohlcv["close"].diff(1)
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    RSI = 100.0 - (100.0/(1.0 + RS))
    dic_RSI['RSI'] = RSI
    return dic_RSI

def GetStoch_RSI(ohlcv,period,st):

    dic_stoch = dict()

    ndays_high = ohlcv.rolling(window=period, min_periods=1).max()
    ndays_low = ohlcv.rolling(window=period, min_periods=1).min()
    fast_k = (ohlcv - ndays_low)/(ndays_high - ndays_low)*100
    slow_k = fast_k.rolling(window=2, min_periods=1).mean()
    slow_d = slow_k.rolling(window=2, min_periods=1).mean()

    dic_stoch['fast_k'] = fast_k.iloc[st]
    dic_stoch['slow_k'] = slow_k.iloc[st]
    dic_stoch['slow_d'] = slow_d.iloc[st]
    
    return dic_stoch

#--알트코인 단타 16%----------------------------------------------------------------------------------------------------------#
#ALT_Portion = 0.16 #알트는 16% 비중인데 A타입과 B타입 각각 8%로 나눔
# A타입(8%) : 상승장에서만 매수, B타입(8%) : 하락장일때도 매수 (언제나 매수)
#상승장 기준 일봉 기준 5일 이동평균선이 증가추세이면서 현재가가 이평선위에 있을때!!

Cash_Portion = 0.05 #현금 비중 15%

ALT_Btype_Portion = 0.95 #B타입 비중 8%
ALT_Btype_MaxCnt = 8.0 #B타입 알트코인의 매수 개수 최대치!
ALT_Btype_Greed_Gap = 0.1 #B타입 그리드(거미줄)간 간격 0.4면 0.4%마다 매수 주문을 깔아놓는다는이야기!
ALT_Btype_First_Buy_Rate = 1.0 #B타입 첫 매수시 들어갈 금액 비중

MinimunCash = 5000.0 #업비트 최소 매수매도 금액!
Target_Revenue_Rate = 1.1 #단타 목표 수익율 1.1%
TopList_TF = 0
#----------------------------------------------------------------------------------------------------------------------#

PassCoinList = ['KRW-BTC','KRW-BTT','KRW-ETH','KRW-ATOM','KRW-XRP','KRW-ETC']
#----------------------------------------------------------------------------------------------------------------------#


#----------------------------------------------------------------------------------------------------------------------#

#도달 수익을 임시 저장할 파일
revenue_file_path = "./RevenueDict.json"

revenueDic = dict() #딕셔너리다!!!

#파일을 읽어서 리스트를 만듭니다. 맨 처음엔 없을테니 당연이 예외처리 로그 나옵니다.
try:
    with open(revenue_file_path, "r") as json_file:
        revenueDic = json.load(json_file)

except Exception as e:
    print("Exception :", e)





#원화 마켓에 상장된 모든 코인들을 가져온다.
Tickers = pyupbit.get_tickers("KRW")




print("autotrade start")
# 자동매매 시작
while True:
    try:
        
        # ## 탑 코인 리스트를 파일에서 읽어서 TopCoinList에 넣는다. ##
        top_file_path = "./UpbitTopCoinList.json"

        TopCoinList = list()

        try:
            with open(top_file_path, "r") as json_file:
                TopCoinList = json.load(json_file)

        except Exception as e:
            TopCoinList = myUpbit.GetTopCoinList("day",20)
            print("Exception:", e)

        PlusCoinList = list()                             #B타입 알트 코인들 리스트

        #파일에 저장된 경우 읽어 온다
        PlusCoin_file_path = "./PlusCoin.json"
        try:
            with open(PlusCoin_file_path, "r") as json_file:
                PlusCoinList = json.load(json_file)

        except Exception as e:
            print("Exception:", e)

        B_TypeList = list()                             #B타입 알트 코인들 리스트

        #파일에 저장된 경우 읽어 온다
        btype_file_path = "./B_TypeCoin.json"
        try:
            with open(btype_file_path, "r") as json_file:
                B_TypeList = json.load(json_file)

        except Exception as e:
            print("Exception:", e)


        #내가 가진 잔고 데이터를 다 가져온다.
        balances = upbit.get_balances()
        TotalMoney = myUpbit.GetTotalMoney(balances) #총 원금
        time.sleep(0.05)
        TotalRealMoney = myUpbit.GetTotalRealMoney(balances) #총 평가금액
        #내 총 수익율
        TotalRevenue = (TotalRealMoney - TotalMoney) * 100.0/ TotalMoney
        
        # print("-----------------------------------------------")
        # print ("Total Money:", TotalMoney)
        # print ("Total Real Money:", TotalRealMoney)
        # print ("Total Revenue", TotalRevenue)
        # print("-----------------------------------------------")


        #----------------------------------------------------------------------------------------------------------------------#
        #B타입의 알트코인별 최대 매수 금액(할당 금액) = (총평가금액 * 할당비중(20%) / 최대코인개수)
        ALT_Btype_CoinMaxMoney = ((TotalRealMoney * ALT_Btype_Portion) / ALT_Btype_MaxCnt)

        #B타입의 알트코인의 첫 매수 금액 = 최대 매수 금액(할당 금액) * 첫매수비중
        ALT_Btype_FirstEnterMoney = ALT_Btype_CoinMaxMoney * ALT_Btype_First_Buy_Rate

        #절반팔고 절반은 나중에 파려면 업비트 최소 주문금액 5천원의 2배인 1만원은 첫 매수에 들어가야 하는데 2.5를 곱해서 12500원 정도의 최소치를 정해논다
        if ALT_Btype_FirstEnterMoney < MinimunCash * 1.1:
            ALT_Btype_FirstEnterMoney = MinimunCash * 1.1


        #B타입의 알트코인의 총 물타기 금액 = 최대 매수 금액(할당 금액) * (1.0 - 첫매수비중)
        ALT_Btype_TotalWaterMoney = ALT_Btype_CoinMaxMoney * (1.0 - ALT_Btype_First_Buy_Rate)

        #A타입의 총 거미줄 매수할 시작 금액! 최소주문금액 5000 * 1.5(보정)
        ALT_Btype_Greed_Money = (MinimunCash * 1.1)

        #정률로(모든 그리드가 다 같은 금액 매수한다는 가정) 실제로 가능한 최대 거미줄 개수 
        ALT_Btype_Maximun_Greed_Cnt = ALT_Btype_TotalWaterMoney / ALT_Btype_Greed_Money



        # print ("------------------------------------------------>ALT_Btype_CoinMaxMoney:", ALT_Btype_CoinMaxMoney)
        # print ("->ALT_Btype_FirstEnterMoney", ALT_Btype_FirstEnterMoney)
      
        # print("-----------------------------------------------")
        #----------------------------------------------------------------------------------------------------------------------#
        #알트코인 개수를 프린트!
        # print("len(B_TypeList)",B_TypeList, len(B_TypeList))
        #----------------------------------------------------------------------------------------------------------------------#



        #----------------------------------------------------------------------------------------------------------------------#       



        #시간 정보를 가져옵니다. 
        time_info = datetime.datetime.now()
        year = time_info.year
        month = time_info.month
        day = time_info.day
        hour = time_info.hour
        min = time_info.minute
        sec = time_info.second
        # print("--------------------------------------------------------------------------Time:", year, month, day, " %.0fH : %.0fM : %.0fS" % (hour,min,sec))

        
        if min == 11 or 31 or 51:
            TopList_TF = 0

        if (min == 10 or min == 30 or min == 50):
            if TopList_TF == 0:
                #----------------------------------------------------------------------------------------------------
                TopCoinList = myUpbit.GetTopCoinList("day",20)
                try:
                    with open(top_file_path, 'w') as outfile:
                        json.dump(TopCoinList, outfile)
                except Exception as e:
                    print("Exception:", e)
                #----------------------------------------------------------------------------------------------------

                TopList_TF = 1
        
        #----------------------------------------------------------------------------------------------------------------------#
        
        if len(B_TypeList) < ALT_Btype_MaxCnt:
            #탑코인 리스트를 1위부터 30위 순으로 순회한다!
            # print("----------------BUY LOGIC------------------------")
            for ticker in Tickers:
                try:
                    
                    if myUpbit.CheckCoinInList(PassCoinList,ticker) == True:
                        continue 
                    #이미 매수된 코인이라면 스킵한다!
                    if myUpbit.IsHasCoin(balances,ticker) == True:
                        continue


                    minute_C = "week"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_C, count=200) #분봉 데이타를 가져온다.

                    ma_B1 = GetMA(df, 20, -2)
                    ma_N = GetMA(df, 20, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_20_W = 1
                    else:
                        ma_20_W = 0

                    ma_B1 = GetMA(df, 10, -2)
                    ma_N = GetMA(df, 10, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_10_W = 1
                    else:
                        ma_10_W = 0      

                    if (ma_20_W + ma_10_W) == 0:
                        continue

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    if (0 > macd) == True:
                        continue
                    # 상승시
                    if (0 < macd and 0 < ocl) == True:
                        Macd_day0 = 1
                    else:
                        Macd_day0 = 0


                    minute_C = "day"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_C, count=200) #분봉 데이타를 가져온다.

                    ma_B1 = GetMA(df, 20, -2)
                    ma_N = GetMA(df, 20, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_20 = 1
                    else:
                        ma_20 = 0

                    ma_B1 = GetMA(df, 10, -2)
                    ma_N = GetMA(df, 10, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_10 = 1
                    else:
                        ma_10 = 0      

                    if (ma_20 + ma_10) == 0:
                        continue

                    now_price = GetMA(df, 1, -1)

                    if (0 < now_price < 0.1):
                        tik = 0.0001
                    elif (0.1 <= now_price < 1):
                        tik = 0.001
                    elif (1 <= now_price < 10):
                        tik = 0.01
                    elif (10 <= now_price < 100):
                        tik = 0.1
                    elif (100 <= now_price < 1000):
                        tik = 1
                    elif (1000 <= now_price < 10000):
                        tik = 5
                    elif (10000 <= now_price < 100000):
                        tik = 10
                    elif (100000 <= now_price < 500000):
                        tik = 50
                    elif (500000 <= now_price < 1000000):
                        tik = 100
                    elif (1000000 <= now_price < 2000000):
                        tik = 500
                    elif (2000000 <= now_price):
                        tik = 1000

                    if (tik / now_price) >= 0.005:
                        continue

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    if (0 > macd) == True:
                        continue
                    # 상승시
                    if (0 < macd and 0 < ocl) == True:
                        Macd_day0 = 1
                    else:
                        Macd_day0 = 0

                    minute_B = "minute240"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_B, count=200) #분봉 데이타를 가져온다.

                    ma_B1 = GetMA(df, 20, -2)
                    ma_N = GetMA(df, 20, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_20 = 1
                    else:
                        ma_20 = 0

                    ma_B1 = GetMA(df, 10, -2)
                    ma_N = GetMA(df, 10, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_10 = 1
                    else:
                        ma_10 = 0      

                    ma_B1 = GetMA(df, 1, -2)
                    ma_N = GetMA(df, 1, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_1_240M = 1
                    else:
                        ma_1_240M = 0

                    if (ma_20 + ma_10) == 0 or ma_1_240M == 0:
                        continue

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    if (0 > ocl) == True:
                        continue
                    if (0 < ocl and 0 < macd) == True:
                        Macd_240M1 = 1
                    else:
                        Macd_240M1 = 0                    
                    # 10분 macd가 기준선 위로 상승
                    if (0 < ocl and 0 < macd and macd_before <= 0) == True:
                        Macd_240M2 = 1
                    else:
                        Macd_240M2 = 0
                    if (0 < ocl) == True:
                        Macd_240M3 = 1
                    else:
                        Macd_240M3 = 0

                    minute_B = "minute60"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_B, count=200) #분봉 데이타를 가져온다.

                    ma_B1 = GetMA(df, 20, -2)
                    ma_N = GetMA(df, 20, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_20 = 1
                    else:
                        ma_20 = 0

                    ma_B1 = GetMA(df, 10, -2)
                    ma_N = GetMA(df, 10, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_10 = 1
                    else:
                        ma_10 = 0      

                    ma_B1 = GetMA(df, 1, -2)
                    ma_N = GetMA(df, 1, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_1_60M = 1
                    else:
                        ma_1_60M = 0

                    if (ma_20 + ma_10) == 0 or ma_1_60M == 0:
                        continue

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    # 10분 macd가 기준선 위에서 상승
                    if (0 < ocl and 0 < macd) == True:
                        Macd_60M1 = 1
                    else:
                        Macd_60M1 = 0
                    # 10분 macd가 기준선위에서 반전 상승
                    if (0 < ocl and ocl_before <= 0 and 0 < macd):
                        Macd_60M2 = 1
                    else:
                        Macd_60M2 = 0

                    minute_B = "minute10"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_B, count=200) #분봉 데이타를 가져온다.

                    ma_B1 = GetMA(df, 20, -2)
                    ma_N = GetMA(df, 20, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_20 = 1
                    else:
                        ma_20 = 0

                    ma_B1 = GetMA(df, 10, -2)
                    ma_N = GetMA(df, 10, -1)
                    # 이평선이 상승시에만
                    if ma_B1 < ma_N:
                        ma_10 = 1
                    else:
                        ma_10 = 0      

                    if (ma_20 + ma_10) == 0:
                        continue

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    # 10분 macd가 기준선 위에서 상승
                    if (0 < ocl and 0 < macd) == True:
                        Macd_10M1 = 1
                    else:
                        Macd_10M1 = 0
                    # 10분 macd가 기준선위에서 반전 상승
                    if (0 < ocl and ocl_before <= 0 and 0 < macd):
                        Macd_10M2 = 1
                    else:
                        Macd_10M2 = 0



                    # print("ticker: %s,  macd: %s, macd_siginal: %s ocl: %s" %(ticker, macd_before, macd_siginal_before, ocl_before))
                    # print("ticker: %s,  macd: %s, macd_siginal: %s ocl: %s" %(ticker, macd, macd_siginal, ocl))
                    # print("ticker: %s,  stoch_d_before: %s, stoch_k_before: %s" %(ticker, stoch_d_before, stoch_k_before))
                    # print("ticker: %s,  stoch_d_now: %s, stoch_k_now: %s" %(ticker, stoch_d_now, stoch_k_now))
                    # print("ticker: %s,  stoch_RSI_d_before: %s, stoch_RSI_k_before: %s" %(ticker, stoch_RSI_d_before, stoch_RSI_k_before))
                    # print("ticker: %s,  stoch_RSI_d_now: %s, stoch_RSI_k_now: %s" %(ticker, stoch_RSI_d_now, stoch_RSI_k_now))
                    # print("ticker: %s,  Stoch_RSI_B: %s, Stoch_B: %s, Macd_B: %s" %(ticker, Stoch_RSI_B, Stoch_B, Macd_B))
                    # print("ticker: %s" %(ticker))
                    # print("-----------------------------------------------------------------------------------------")

                    if (Macd_day0 == 1 and Macd_240M3 == 1 and Macd_60M1 == 1 and Macd_10M1 == 1):

                        #아무때나 매수 가능한 B타입이 아직 매수가능 코인 개수가 남아 있을때! (B타입 리스트 개수가 최대매수코인 개수보다 작을 경우)
                        if len(B_TypeList) < ALT_Btype_MaxCnt:
                            #시장가로 매수한다!
                            # print("IN Target!!!")
                            balances = myUpbit.BuyCoinMarket(upbit,ticker,ALT_Btype_FirstEnterMoney)

                            #평균 매입 단가를 읽어옵니다!
                            avgPrice = myUpbit.GetAvgBuyPrice(balances,ticker)

                            #시간 정보를 가져옵니다. 
                            time_info = datetime.datetime.now()
                            year = time_info.year
                            month = time_info.month
                            day = time_info.day
                            hour = time_info.hour
                            min = time_info.minute
                            sec = time_info.second
                            print("...........................................................................Time:", year, month, day, " %.0fH : %.0fM : %.0fS" % (hour,min,sec))

                            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++>BUY: " , ticker, avgPrice)


                            #수익율 당연히 코인명(키)과 수익율(값)을 파일저장한다!
                            revenueDic[ticker] = 0  #당연히 첫 매수니 수익율을 0이다!
                            #파일에 리스트를 저장합니다
                            with open(revenue_file_path, 'w') as outfile:
                                json.dump(revenueDic, outfile)         


                            #매수된 코인을 B_TypeList 리스트에 넣고 이를 파일로 저장해둔다!
                            B_TypeList.append(ticker)
                            # print(B_TypeList)
                            
                            try:
                                with open(btype_file_path, 'w') as outfile:
                                    json.dump(B_TypeList, outfile)
                            except Exception as e:
                                print("Exception:", e)

 
                    if len(B_TypeList) >= ALT_Btype_MaxCnt:
                        break
            

                except Exception as e:
                    print("---:", e)

            # print("--------------------------------------------------")

        #----------------------------------------------------------------------------------------------------------------------#





        #----------------------------------------------------------------------------------------------------------------------#
        

        #이미 보유하고 있는 코인인 매도 대상이다!!
        # print("----------------SELL LOGIC------------------------")
        for ticker in Tickers:
            try: 
                #이미 보유하고 있다며!!

                if myUpbit.IsHasCoin(balances,ticker) == True:

                    if myUpbit.CheckCoinInList(PassCoinList,ticker) == True:
                        continue                     

                    #수익율을 구한다.
                    revenue_rate = myUpbit.GetRevenueRate(balances,ticker)


                    #저장된 수익율보다 현재 수익율이 클때만 갱신시켜준다!
                    if revenueDic[ticker] < revenue_rate:

                        #현재 수익율을 코인티커와 함께 저장해 두자!
                        revenueDic[ticker] = revenue_rate 

                        #파일에 리스트를 저장합니다
                        try:
                            with open(revenue_file_path, 'w') as outfile:
                                json.dump(revenueDic, outfile)         
                        except Exception as e:
                            print("Exception:", e)

                    # avgPrice = myUpbit.GetAvgBuyPrice(balances,ticker)
                    # print("---------------------------> Has coin : ", ticker, "avgPrice : ", avgPrice, "now_price : ", now_price, " revenue_rate --> ", revenue_rate)

                    

                    ################분봉 데이타를 읽고 지표에 의거 매수를 한다!################
                    minute_C = "week"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_C, count=200) #분봉 데이타를 가져온다.

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    # 상승시
                    if (0 > ocl) == True:
                        Macd_week1 = 1
                    else:
                        Macd_week1 = 0

                    if (0 > ocl and 0 > ocl_before) == True:
                        Macd_week2 = 1
                    else:
                        Macd_week2 = 0

                    if (0 > macd and 0 > ocl) == True:
                        Macd_week_stop = 1
                    else:
                        Macd_week_stop = 0


                    minute_C = "day"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_C, count=200) #분봉 데이타를 가져온다.

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    # 상승시
                    if (0 > ocl) == True:
                        Macd_day1 = 1
                    else:
                        Macd_day1 = 0

                    if (0 > ocl and 0 > ocl_before) == True:
                        Macd_day2 = 1
                    else:
                        Macd_day2 = 0

                    if (0 > macd and 0 > ocl) == True:
                        Macd_day_stop = 1
                    else:
                        Macd_day_stop = 0

                    minute_B = "minute240"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_B, count=200) #분봉 데이타를 가져온다.

                    now_price = GetMA(df, 1, -1)

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    ma_B1 = GetMA(df, 1, -2)
                    ma_N = GetMA(df, 1, -1)
                    # 이평선이 상승시에만
                    if ma_B1 > ma_N:
                        ma_1_240M = 1
                    else:
                        ma_1_240M = 0

                    if (0 > ocl) == True:
                        Macd_240M1 = 1
                    else:
                        Macd_240M1 = 0
                    if (0 > macd and 0 > ocl) == True:
                        Macd_240M_stop = 1
                    else:
                        Macd_240M_stop = 0

                    minute_B = "minute60"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_B, count=200) #분봉 데이타를 가져온다.

                    now_price = GetMA(df, 1, -1)

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    ma_B1 = GetMA(df, 1, -2)
                    ma_N = GetMA(df, 1, -1)
                    # 이평선이 하락시에만
                    if ma_B1 > ma_N:
                        ma_1_60M = 1
                    else:
                        ma_1_60M = 0


                    if (0 > ocl) == True:
                        Macd_60M1 = 1
                    else:
                        Macd_60M1 = 0
                    if (0 > macd and 0 > ocl) == True:
                        Macd_60M_stop = 1
                    else:
                        Macd_60M_stop = 0

                    minute_B = "minute10"

                    time.sleep(0.05)
                    df = pyupbit.get_ohlcv(ticker,interval=minute_B, count=200) #분봉 데이타를 가져온다.

                    now_price = GetMA(df, 1, -1)

                    Macd_df = GetMACD(df,-3)
                    macd_before2 = Macd_df['macd']
                    macd_siginal_before2 = Macd_df['macd_siginal']
                    ocl_before2 = Macd_df['ocl']

                    Macd_df = GetMACD(df,-2)
                    macd_before = Macd_df['macd']
                    macd_siginal_before = Macd_df['macd_siginal']
                    ocl_before = Macd_df['ocl']
                    
                    Macd_df = GetMACD(df,-1)
                    macd = Macd_df['macd']
                    macd_siginal = Macd_df['macd_siginal']
                    ocl = Macd_df['ocl']

                    ma_B1 = GetMA(df, 1, -2)
                    ma_N = GetMA(df, 1, -1)
                    # 이평선이 하락시에만
                    if ma_B1 > ma_N:
                        ma_1_10M = 1
                    else:
                        ma_1_10M = 0

                    if (0 > ocl) == True:
                        Macd_10M1 = 1
                    else:
                        Macd_10M1 = 0
                    if (0 > macd and 0 > ocl) == True:
                        Macd_10M_stop = 1
                    else:
                        Macd_10M_stop = 0

                    # print("ticker: %s,  macd: %s, macd_siginal: %s ocl: %s" %(ticker, macd_before, macd_siginal_before, ocl_before))
                    # # print("ticker: %s,  macd: %s, macd_siginal: %s ocl: %s" %(ticker, macd, macd_siginal, ocl))
                    # print("ticker: %s,  stoch_d_before: %s, stoch_k_before: %s" %(ticker, stoch_d_before, stoch_k_before))
                    # # print("ticker: %s,  stoch_d_now: %s, stoch_k_now: %s" %(ticker, stoch_d_now, stoch_k_now))
                    # print("ticker: %s,  stoch_RSI_d_before: %s, stoch_RSI_k_before: %s" %(ticker, stoch_RSI_d_before, stoch_RSI_k_before))
                    # # print("ticker: %s,  stoch_RSI_d_now: %s, stoch_RSI_k_now: %s" %(ticker, stoch_RSI_d_now, stoch_RSI_k_now))
                    # print("ticker: %s,  Stoch_RSI_sell_B: %s, Stoch_sell_B: %s, Macd_sell_B: %s" %(ticker, Stoch_RSI_sell_B, Stoch_sell_B, Macd_sell_B))
                    # # print("ticker: %s" %(ticker))
                    # print("-----------------------------------------------------------------------------------------")

                    if 0 < revenueDic[ticker] < 2:
                        tralling_stop_rate = 0.5
                    elif revenueDic[ticker] < 5:
                        tralling_stop_rate = 0.54
                    elif revenueDic[ticker] < 10:
                        tralling_stop_rate = 0.64
                    elif revenueDic[ticker] < 25:
                        tralling_stop_rate = 0.74                    
                    elif revenueDic[ticker] >= 25:
                        tralling_stop_rate = revenueDic[ticker] - 5


                    if (revenueDic[ticker] > 3 and (revenueDic[ticker] * tralling_stop_rate) > revenue_rate) == True:
                       revenue_rate_TF = 1
                    else:
                       revenue_rate_TF = 0

                    #매도로직
                    if (ma_1_60M == 1 and Macd_240M1 == 1 and Macd_60M_stop == 1 and Macd_10M1 == 1 and (revenue_rate < -0.6 or revenue_rate > 0.6)) or (ma_1_60M == 1 and revenue_rate < -0.6 and Macd_60M1 == 1) or (revenue_rate_TF == 1 and ma_1_10M == 1 and Macd_10M1 == 1):

                        #평균 매입 단가를 읽어옵니다!                        
                        avgPrice = myUpbit.GetAvgBuyPrice(balances,ticker)
                        #시장가로 남은물량 모두 매도처리합니다!
                        balances = myUpbit.SellCoinMarket(upbit,ticker,upbit.get_balance(ticker))

                        #시간 정보를 가져옵니다. 
                        time_info = datetime.datetime.now()
                        year = time_info.year
                        month = time_info.month
                        day = time_info.day
                        hour = time_info.hour
                        min = time_info.minute
                        sec = time_info.second
                        ma_N = GetMA(df, 1, -1)                    
                        print(".................................................................................................................Time:", year, month, day, " %.0fH : %.0fM : %.0fS" % (hour,min,sec))

                        print("-------------------------------------------------------------------------------------------------------------------->  " , ticker," AVG: ",  avgPrice," -> SELL: ", ma_N, revenue_rate)

                        # #파일에 리스트를 저장합니다
                        # if revenueDic[ticker] > 10:

                        #     with open(PlusCoin_file_path, 'w') as outfile:
                        #         json.dump(PlusCoinList, outfile)
                        #                             #매수된 코인을 B_TypeList 리스트에 넣고 이를 파일로 저장해둔다!
                        #     PlusCoinList.append(ticker)
                        #     # print(PlusCoinList)
                            
                        #     try:
                        #         with open(PlusCoin_file_path, 'w') as outfile:
                        #             json.dump(PlusCoinList, outfile)
                        #     except Exception as e:
                        #         print("Exception:", e)

                        revenueDic[ticker] = 0  #매도 초기화 수익율 0으로!
                        #파일에 리스트를 저장합니다
                        try:
                            with open(revenue_file_path, 'w') as outfile:
                                json.dump(revenueDic, outfile)         
                        except Exception as e:
                            print("Exception:", e)

                        #B타입의 알트 코인이었다면 리스트에서 제거 해준다!
                        if myUpbit.CheckCoinInList(B_TypeList,ticker) == True:
                            B_TypeList.remove(ticker)
                            try:
                                with open(btype_file_path, 'w') as outfile:
                                    json.dump(B_TypeList, outfile)
                            except Exception as e:
                                print("Exception:", e)


                elif myUpbit.CheckCoinInList(B_TypeList,ticker) == True:
                    B_TypeList.remove(ticker)
                    # print(B_TypeList)
                    try:
                        with open(btype_file_path, 'w') as outfile:
                            json.dump(B_TypeList, outfile)
                    except Exception as e:
                        print("Exception:", e)


            except Exception as e:
                print("---:", e)


        # print("++++++++++++++++++++++++++++++++++++++++++++++++++")
            

        #----------------------------------------------------------------------------------------------------------------------#

    except Exception as e:
        print(e)
        

