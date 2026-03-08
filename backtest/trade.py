import pandas as pd
from config.config import Config


class Trade:

    def __init__(self, side, strike, entry_price, entry_time, spot, expiry, dte):

        self.side = side
        self.strike = strike
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.spot = spot

        self.expiry = expiry
        self.dte = dte

        self.sl = entry_price * Config.SL_MULTIPLIER
        self.trailing_sl = self.sl

        self.is_open = True


    def check_exit(self, ltp, high, now, call_atp, put_atp):

        profit_move = self.entry_price - ltp

        trail_hit = False

        if now <= Config.TRAIL_ACTIVE_TILL and profit_move >= self.entry_price * Config.TRAIL_START:

            extra_profit = profit_move - (self.entry_price * Config.TRAIL_START)
            trail_reduction = extra_profit * Config.TRAIL_RATIO

            new_trail_sl = self.sl - trail_reduction
            self.trailing_sl = min(self.trailing_sl, new_trail_sl)

            trail_hit = ltp >= self.trailing_sl


        sl_hit = ltp >= self.sl


        fixed_sl_hit = False
        if now <= Config.FIXED_SL_ACTIVE_TILL:
            fixed_sl_hit = high >= self.sl


        atp_trail_hit = False
        if now >= Config.ATP_TRAIL_START:

            atp = call_atp if self.side == "CE" else put_atp

            atp_trail_hit = high >= atp * Config.ATP_MULT


        time_exit = now >= Config.EXIT_TIME


        if sl_hit or fixed_sl_hit or trail_hit or atp_trail_hit or time_exit:

            if fixed_sl_hit:
                exit_price = self.sl
                reason = "fixed SL hit (50%)"

            elif atp_trail_hit:
                atp = call_atp if self.side == "CE" else put_atp
                exit_price = atp * Config.ATP_MULT
                reason = "ATP trailing hit"

            elif trail_hit:
                exit_price = self.trailing_sl
                reason = "Profit trailing SL hit"

            elif sl_hit:
                exit_price = self.sl
                reason = "Initial SL hit"

            else:
                exit_price = ltp
                reason = "time_exit"

            self.is_open = False

            return True, exit_price, reason

        return False, None, None


    def to_dict(self, exit_time, exit_price, exit_reason, atp):

        return {
            'trade_status': 'close',
            'instrument_id': 'NIFTY',
            'symbol': f'NIFTY{self.expiry}{self.strike}{self.side}',
            'option_type': self.side,
            'buy/sell': 'sell',
            'entry_date': self.entry_time.date(),
            'dte': self.dte,
            'expiry': pd.to_datetime(self.expiry).strftime('%Y-%m-%d'),
            'entry_signal_time': self.entry_time,
            'entry_time': self.entry_time,
            'entry_price': self.entry_price,
            'entry_reason': f'{self.side} trade occured',
            'quantity': Config.QTY,
            'market_bias': None,
            'stop_loss': self.sl,
            'trailing_sl': atp * Config.ATP_MULT,
            'exit_date': exit_time.strftime('%Y-%m-%d'),
            'exit_signal_time': exit_time,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl_raw': self.entry_price - exit_price,
            'max_loss': self.sl - self.entry_price,
            'max_profit': self.entry_price,
            'spot_close': self.spot,
        }