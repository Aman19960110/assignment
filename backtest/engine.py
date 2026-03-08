import pandas as pd
from backtest.trade import Trade
from config.config import Config


class BacktestEngine:

    def __init__(self, df, pivot, strategy, expiry, dte):

        self.df = df
        self.pivot = pivot
        self.strategy = strategy

        self.expiry = expiry
        self.dte = dte

        self.open_ce_trades = []
        self.open_pe_trades = []

        self.results = []


    def run(self):

        for dt, row in self.df.groupby("datetime"):

            if dt.time() < Config.START_TIME:
                continue

            spot_close = row["close_spot"].iloc[0]
            atm_strike = round(spot_close / 50) * 50

            straddle_row = self.pivot[
                (self.pivot["datetime"] == dt) &
                (self.pivot["strike_price"] == atm_strike)
            ]

            if straddle_row.empty:
                continue

            straddle_p = straddle_row["straddle"].iloc[0]
            offset = Config.OFFSET_TH * straddle_p

            call_row, put_row = self.strategy.select_strikes(row, atm_strike, offset)

            if call_row.empty or put_row.empty:
                continue

            call_strike = call_row["strike_price"].iloc[0]
            put_strike = put_row["strike_price"].iloc[0]

            call_close = call_row["close_opt"].iloc[0]
            put_close = put_row["close_opt"].iloc[0]

            call_atp = self.df[
                (self.df["strike_price"] == call_strike) &
                (self.df["datetime"] <= dt) &
                (self.df["right"] == "Call")
            ]["close_opt"].mean()

            put_atp = self.df[
                (self.df["strike_price"] == put_strike) &
                (self.df["datetime"] <= dt) &
                (self.df["right"] == "Put")
            ]["close_opt"].mean()


            # INITIAL ENTRY

            if dt.time() <= Config.REENTRY_END:

                if not self.open_ce_trades and call_close < call_atp:

                    self.open_ce_trades.append(
                        Trade("CE", call_strike, call_close, dt, spot_close, self.expiry, self.dte)
                    )

                if not self.open_pe_trades and put_close < put_atp:

                    self.open_pe_trades.append(
                        Trade("PE", put_strike, put_close, dt, spot_close, self.expiry, self.dte)
                    )


            # CE TRADE MANAGEMENT

            for trade in self.open_ce_trades.copy():

                opt = row[(row["strike_price"] == trade.strike) & (row["right"] == "Call")]

                if opt.empty:
                    continue

                ce_ltp = opt["close_opt"].iloc[0]
                ce_high = opt["high_opt"].iloc[0]

                exit_flag, exit_price, reason = trade.check_exit(
                    ce_ltp, ce_high, dt.time(), call_atp, put_atp
                )

                if exit_flag:

                    self.results.append(
                        trade.to_dict(dt, exit_price, reason, call_atp)
                    )

                    self.open_ce_trades.remove(trade)


                    # REENTRY → PE

                    if dt.time() <= Config.REENTRY_END and len(self.open_pe_trades) < Config.MAX_TRADES_PE:

                        if put_close < put_atp:

                            self.open_pe_trades.append(
                                Trade("PE", put_strike, put_close, dt, spot_close, self.expiry, self.dte)
                            )


            # PE TRADE MANAGEMENT

            for trade in self.open_pe_trades.copy():

                opt = row[(row["strike_price"] == trade.strike) & (row["right"] == "Put")]

                if opt.empty:
                    continue

                pe_ltp = opt["close_opt"].iloc[0]
                pe_high = opt["high_opt"].iloc[0]

                exit_flag, exit_price, reason = trade.check_exit(
                    pe_ltp, pe_high, dt.time(), call_atp, put_atp
                )

                if exit_flag:

                    self.results.append(
                        trade.to_dict(dt, exit_price, reason, put_atp)
                    )

                    self.open_pe_trades.remove(trade)


                    # REENTRY → CE

                    if dt.time() <= Config.REENTRY_END and len(self.open_ce_trades) < Config.MAX_TRADES_CE:

                        if call_close < call_atp:

                            self.open_ce_trades.append(
                                Trade("CE", call_strike, call_close, dt, spot_close, self.expiry, self.dte)
                            )