from vnstock import Vnstock
from datetime import date, timedelta
import warnings
warnings.filterwarnings("ignore")


def load_historical_data(symbol,
                         start=date.today().strftime(
                             "%Y-%m-%d"),
                         end=(date.today() + timedelta(days=1)
                              ).strftime("%Y-%m-%d"),
                         interval="15m"):
    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    df = stock.quote.history(start=start, end=end, interval=interval)
    return df
