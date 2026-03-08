import glob
import pandas as pd

from backtest.strategy import Strategy
from backtest.engine import BacktestEngine


files = glob.glob('data/nifty*.parquet')
#print(files)
all_results = []

for f in files:

    print("Running:", f)

    df = pd.read_parquet(f).sort_values("datetime")

    pivot = (
        df.pivot_table(
            index=["datetime","strike_price"],
            columns="right",
            values="close_opt",
            aggfunc="last"
        )
        .reset_index()
        .dropna(subset=["Call","Put"])
    )

    pivot["straddle"] = pivot["Call"] + pivot["Put"]

    expiry = pd.to_datetime(df["expiry"].iloc[0]).strftime("%d%b%y")
    dte = (pd.to_datetime(df["expiry"].iloc[0]) - pd.to_datetime(df["date"].iloc[0])).days

    strategy = Strategy()

    engine = BacktestEngine(df, pivot, strategy, expiry, dte)

    engine.run()

    all_results.append(pd.DataFrame(engine.results))


results = pd.concat(all_results)
results = results.sort_values('entry_time')
results.to_csv("results/trades.csv", index=False)