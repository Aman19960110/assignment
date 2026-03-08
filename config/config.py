from datetime import time


class Config:


    INSTRUMENT = "NIFTY"
    QTY = 1



    START_TIME = time(9,17)
    EXIT_TIME = time(15,16)
    REENTRY_END = time(9,34)



    OFFSET_TH = 0.2



    MAX_TRADES_CE = 2
    MAX_TRADES_PE = 2



    SL_MULTIPLIER = 1.5

    FIXED_SL_ACTIVE_TILL = time(9,34)



    TRAIL_START = 0.5
    TRAIL_RATIO = 0.5
    TRAIL_ACTIVE_TILL = time(9,34)



    ATP_TRAIL_START = time(9,35)
    ATP_MULT = 1.10