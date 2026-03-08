class Strategy:

    def select_strikes(self, row, atm, offset):

        call_row = row[
            (row["right"] == "Call") &
            (row["strike_price"] > atm - 50) &
            (row["close_opt"] <= offset)
        ].sort_values("strike_price").head(1)

        put_row = row[
            (row["right"] == "Put") &
            (row["strike_price"] < atm + 50) &
            (row["close_opt"] <= offset)
        ].sort_values("strike_price", ascending=False).head(1)

        return call_row, put_row


    def entry_signal(self, price, atp):

        return price < atp