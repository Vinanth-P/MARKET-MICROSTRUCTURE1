import requests
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from django.utils import timezone


class CryptoDataFetcher:
    """Fetches cryptocurrency data from CoinGecko API"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    @staticmethod
    def get_price(symbol: str) -> Optional[Dict]:
        """
        Get current price for a cryptocurrency.
        symbol: 'bitcoin', 'ethereum', etc.
        """
        try:
            url = f"{CryptoDataFetcher.BASE_URL}/simple/price"
            params = {
                'ids': symbol,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if symbol in data:
                price_data = data[symbol]
                return {
                    'price': Decimal(str(price_data.get('usd', 0))),
                    'change_24h': Decimal(str(price_data.get('usd_24h_change', 0))),
                    'volume_24h': Decimal(str(price_data.get('usd_24h_vol', 0))),
                }
        except Exception as e:
            print(f"Error fetching crypto data for {symbol}: {e}")
            # Return mock data if API fails
            return CryptoDataFetcher._get_mock_data(symbol)
        return None
    
    @staticmethod
    def _get_mock_data(symbol: str) -> Dict:
        """Generate mock data for development"""
        mock_prices = {
            'bitcoin': {'price': 68420.10, 'change': 4.5},
            'ethereum': {'price': 3892.55, 'change': -0.8},
        }
        data = mock_prices.get(symbol, {'price': 1000, 'change': 0})
        return {
            'price': Decimal(str(data['price'])),
            'change_24h': Decimal(str(data['change'])),
            'volume_24h': Decimal('1200000000'),
        }
    
    @staticmethod
    def get_historical_data(symbol: str, days: int = 30) -> List[Dict]:
        """Get historical price data"""
        try:
            url = f"{CryptoDataFetcher.BASE_URL}/coins/{symbol}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            prices = []
            for price_point in data.get('prices', []):
                prices.append({
                    'timestamp': datetime.fromtimestamp(price_point[0] / 1000, tz=timezone.utc),
                    'price': Decimal(str(price_point[1]))
                })
            return prices
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return []


class StockDataFetcher:
    """Fetches stock market data"""
    
    @staticmethod
    def get_sp500_price() -> Optional[Dict]:
        """Get S&P 500 current price"""
        try:
            # Using Alpha Vantage API (free tier)
            # For production, you'd use an API key
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'SPY',  # S&P 500 ETF
                'apikey': 'demo'  # Replace with actual API key
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            quote = data.get('Global Quote', {})
            if quote:
                current = Decimal(str(quote.get('05. price', 0)))
                change = Decimal(str(quote.get('09. change', 0)))
                change_percent = Decimal(str(quote.get('10. change percent', '0%')).replace('%', ''))
                
                return {
                    'price': current,
                    'change': change,
                    'change_percent': change_percent,
                }
        except Exception as e:
            print(f"Error fetching S&P 500 data: {e}")
        
        # Return mock data
        return {
            'price': Decimal('4132.45'),
            'change': Decimal('49.59'),
            'change_percent': Decimal('1.2'),
        }


class SentimentFetcher:
    """Fetches market sentiment data"""
    
    @staticmethod
    def get_fear_greed_index() -> Dict:
        """
        Get Fear & Greed Index.
        Returns a score from 0-100 and level.
        """
        try:
            # Using Alternative.me API (free, no key required)
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data'):
                latest = data['data'][0]
                score = int(latest.get('value', 50))
                level_map = {
                    '0-24': 'extreme_fear',
                    '25-44': 'fear',
                    '45-55': 'neutral',
                    '56-75': 'greed',
                    '76-100': 'extreme_greed',
                }
                
                if score <= 24:
                    level = 'extreme_fear'
                elif score <= 44:
                    level = 'fear'
                elif score <= 55:
                    level = 'neutral'
                elif score <= 75:
                    level = 'greed'
                else:
                    level = 'extreme_greed'
                
                return {
                    'score': score,
                    'level': level,
                }
        except Exception as e:
            print(f"Error fetching sentiment data: {e}")
        
        # Return mock data
        return {
            'score': 72,
            'level': 'greed',
        }


class DataSyncService:
    """Service to sync market data to database"""
    
    @staticmethod
    def sync_market_indicators():
        """Sync all market indicators"""
        from dashboard.models import MarketIndicator, Asset
        
        # Sync S&P 500
        sp500_data = StockDataFetcher.get_sp500_price()
        if sp500_data:
            MarketIndicator.objects.create(
                indicator_type='sp500',
                value=sp500_data['price'],
                change_percent=sp500_data['change_percent']
            )
        
        # Sync Bitcoin
        btc_data = CryptoDataFetcher.get_price('bitcoin')
        if btc_data:
            MarketIndicator.objects.create(
                indicator_type='btc',
                value=btc_data['price'],
                change_percent=btc_data['change_24h']
            )
            # Update or create Asset
            asset, _ = Asset.objects.get_or_create(
                symbol='BTC/USD',
                defaults={
                    'name': 'Bitcoin',
                    'asset_type': 'crypto',
                    'exchange': 'Coinbase',
                    'current_price': btc_data['price'],
                    'change_24h': btc_data['change_24h'],
                    'volume_24h': btc_data['volume_24h'],
                }
            )
            if not _:
                asset.current_price = btc_data['price']
                asset.change_24h = btc_data['change_24h']
                asset.volume_24h = btc_data['volume_24h']
                asset.save()
        
        # Sync Ethereum
        eth_data = CryptoDataFetcher.get_price('ethereum')
        if eth_data:
            MarketIndicator.objects.create(
                indicator_type='eth',
                value=eth_data['price'],
                change_percent=eth_data['change_24h']
            )
            asset, _ = Asset.objects.get_or_create(
                symbol='ETH/USD',
                defaults={
                    'name': 'Ethereum',
                    'asset_type': 'crypto',
                    'exchange': 'Coinbase',
                    'current_price': eth_data['price'],
                    'change_24h': eth_data['change_24h'],
                    'volume_24h': eth_data['volume_24h'],
                }
            )
            if not _:
                asset.current_price = eth_data['price']
                asset.change_24h = eth_data['change_24h']
                asset.volume_24h = eth_data['volume_24h']
                asset.save()
    
    @staticmethod
    def sync_sentiment():
        """Sync market sentiment"""
        from dashboard.models import MarketSentiment
        
        sentiment_data = SentimentFetcher.get_fear_greed_index()
        MarketSentiment.objects.create(
            score=sentiment_data['score'],
            level=sentiment_data['level']
        )


