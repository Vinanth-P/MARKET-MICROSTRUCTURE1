import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.data_fetchers import CryptoDataFetcher

try:
    b = CryptoDataFetcher.get_binance_klines('BTCUSDT', interval='1d', limit=5)
    print('BINANCE_COUNT', len(b))
    if len(b):
        print('BINANCE_SAMPLE', b[0])
except Exception as e:
    print('BINANCE_ERROR', e)

try:
    c = CryptoDataFetcher.get_historical_data('bitcoin', days=5)
    print('COINGECKO_COUNT', len(c))
    if len(c):
        print('COINGECKO_SAMPLE', c[0])
except Exception as e:
    print('COINGECKO_ERROR', e)
