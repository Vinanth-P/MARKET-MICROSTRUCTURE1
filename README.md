# Market Microstructure Platform

A comprehensive Django-based financial market analysis platform featuring real-time market data, price forecasting, and pattern detection.

## Features

- **Market Overview Dashboard**: Real-time market indicators (S&P 500, BTC, ETH), trading signals, and market sentiment analysis
- **Price Forecasting**: AI-powered price predictions with configurable horizons and technical indicators
- **Pattern Detection**: Automated detection of chart patterns (Bull Flag, Head & Shoulders, Double Bottom, etc.)
- **User Authentication**: Secure user accounts with profile management
- **REST API**: Real-time data endpoints for market updates

## Technology Stack

- **Backend**: Django 5.0+
- **Database**: SQLite (development)
- **Frontend**: Django Templates, Chart.js, Vanilla JavaScript
- **APIs**: Django REST Framework
- **External Data**: CoinGecko API, Alpha Vantage API, Alternative.me API

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd market-microstructure
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
market-microstructure/
├── accounts/              # User authentication app
├── dashboard/            # Market overview dashboard
├── forecast/              # Price forecasting app
├── patterns/              # Pattern detection app
├── core/                  # Shared utilities (data fetchers, pattern detection, prediction engine)
├── market_microstructure/ # Main Django project settings
├── static/                # CSS, JavaScript, images
├── templates/             # Base templates
└── manage.py
```

## Apps Overview

### Accounts
- User registration and authentication
- User profiles with plan tracking
- Profile management

### Dashboard
- Market overview with real-time indicators
- Trading signals feed
- Market sentiment gauge
- Asset detail views with price charts

### Forecast
- Price prediction configuration
- Forecast generation with technical indicators
- Historical forecast accuracy tracking
- Interactive forecast visualization

### Patterns
- Live pattern detection alerts
- Pattern configuration
- Historical pattern analysis
- Pattern performance statistics

## API Endpoints

### Dashboard API
- `GET /api/dashboard/market-overview/` - Get market indicators
- `GET /api/dashboard/signals/` - Get trading signals
- `GET /api/dashboard/sentiment/` - Get market sentiment
- `GET /api/dashboard/price-data/<symbol>/` - Get price data for an asset

### Forecast API
- `POST /api/forecast/run/` - Run a new forecast
- `GET /api/forecast/<id>/` - Get forecast details
- `GET /api/forecast/history/` - Get forecast history

### Patterns API
- `POST /api/patterns/detect/` - Run pattern detection
- `GET /api/patterns/live/` - Get live pattern alerts
- `GET /api/patterns/history/` - Get historical pattern data

## Configuration

### External APIs

The application uses the following external APIs (with fallback to mock data):

- **CoinGecko**: Cryptocurrency price data (free tier, no API key required)
- **Alpha Vantage**: Stock market data (requires API key for production)
- **Alternative.me**: Fear & Greed Index (free, no API key required)

To configure API keys, create a `.env` file in the project root:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

## Development

### Running Tests
```bash
python manage.py test
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Features in Development

- WebSocket support for real-time updates
- Advanced ML models for predictions
- Email notifications for alerts
- Export functionality for reports
- Additional pattern types and indicators

## License

This project is for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


