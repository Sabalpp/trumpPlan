# Frontend - Political Alpha Platform

Modern React-based frontend for the Political Sentiment Alpha Platform.

## Features

- 📊 Real-time dashboard with signal statistics
- 📈 Signal browser with advanced filtering
- 🧪 Backtest results visualization
- 💰 Pricing page with subscription tiers
- 📝 Waitlist registration with referral codes
- ⚠️ Comprehensive disclaimer page

## Technology Stack

- **React 18** - UI framework
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Recharts** - Data visualization (optional)
- **CSS3** - Modern styling with gradients and animations

## Setup

### Prerequisites

- Node.js 16+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm start
```

Runs on `http://localhost:3000` with proxy to backend API on `http://localhost:5000`.

### Build for Production

```bash
npm run build
```

Creates an optimized production build in the `build/` directory.

## Project Structure

```
frontend/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── pages/
│   │   ├── Dashboard.js/css    # Main dashboard
│   │   ├── Signals.js/css      # Signal browser
│   │   ├── Backtest.js/css     # Backtest results
│   │   ├── Waitlist.js/css     # Waitlist signup
│   │   ├── Pricing.js/css      # Pricing tiers
│   │   └── Disclaimer.js/css   # Legal disclaimer
│   ├── App.js/css              # Main app component
│   ├── index.js/css            # Entry point
│   └── ...
├── package.json
└── README.md
```

## API Integration

The frontend communicates with the backend Flask API:

- `GET /api/stats` - Platform statistics
- `GET /api/signals` - List trading signals
- `POST /api/signal` - Generate new signal
- `GET /api/backtest` - Backtest results
- `POST /waitlist` - Join waitlist
- `GET /health` - Health check

Proxy is configured in `package.json` to forward API requests to `http://localhost:5000`.

## Deployment

### Netlify / Vercel

1. Connect your Git repository
2. Set build command: `npm run build`
3. Set publish directory: `build`
4. Add environment variable: `REACT_APP_API_URL=https://your-backend-api.com`

### AWS S3 + CloudFront

```bash
npm run build
aws s3 sync build/ s3://your-bucket-name
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

## Environment Variables

Create `.env` file:

```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENV=development
```

## Styling Guidelines

- Uses CSS variables for theming (`:root` in `index.css`)
- Gradient backgrounds for premium feel
- Responsive design with mobile-first approach
- Box shadows for depth and elevation
- Smooth transitions and hover effects

## Contributing

See main project README for contribution guidelines.

