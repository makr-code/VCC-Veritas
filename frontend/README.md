# Frontend - VERITAS User Interface

## Overview

The `frontend/` directory contains the web-based user interface for the VERITAS legal AI system, including React components, styling, and client-side services.

## Structure

```
frontend/
├── public/                   # Static assets
├── src/
│   ├── components/           # React components
│   │   ├── Query/           # Query interface
│   │   ├── Results/         # Results display
│   │   ├── Chat/            # Chat interface
│   │   └── common/          # Shared components
│   ├── pages/               # Page components
│   ├── services/            # API client services
│   ├── hooks/               # Custom React hooks
│   ├── utils/               # Utility functions
│   ├── styles/              # CSS and styling
│   ├── App.jsx              # Main app component
│   └── main.jsx             # React entry point
├── package.json             # Node dependencies
├── vite.config.js           # Vite configuration
└── index.html               # HTML template
```

## Key Features

✅ **Real-time query interface** - Interactive legal research
✅ **SSE integration** - Live progress updates
✅ **Multi-turn chat** - Conversational interface
✅ **Citation display** - Formatted legal references
✅ **Responsive design** - Mobile-friendly UI

## Components

### Query Interface (`components/Query/`)
- Search input with autocomplete
- Filter and refinement options
- Domain selection (BImSchG, etc.)

### Results Display (`components/Results/`)
- Citation formatting (IEEE style)
- Legal reference highlighting
- Relevance scoring display
- Source attribution

### Chat Interface (`components/Chat/`)
- Multi-turn conversation support
- Context preservation
- Message history
- Export functionality

## Development

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Technology Stack

- **React 18+** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Axios** - HTTP client
- **EventSource** - SSE integration

### Development Server

```bash
npm run dev
# Runs on http://localhost:5173
```

### Production Build

```bash
npm run build
# Output: dist/
npm run preview  # Preview build locally
```

## Services

### API Client (`services/`)
```javascript
import { queryAPI, fetchResults } from './services/api'

// Query VERITAS backend
const results = await queryAPI({
  query: "BImSchG genehmigung",
  domain: "admin_law"
})
```

### SSE Integration (`services/sse.js`)
```javascript
// Listen to real-time progress
const eventSource = new EventSource('/api/v3/query-stream')
eventSource.onmessage = (event) => {
  const progress = JSON.parse(event.data)
  updateProgress(progress)
}
```

## Key Routes

- `/` - Home/search interface
- `/results/:queryId` - Results page
- `/chat` - Chat interface
- `/settings` - User settings
- `/about` - About page

## Configuration

Environment variables (`.env`):
```
VITE_API_URL=http://localhost:8000
VITE_API_V3_URL=http://localhost:8000/api/v3
VITE_ENVIRONMENT=development
```

## Performance

- Load time: <2s
- Component render: <100ms
- API response: <1000ms (with streaming)

## Accessibility

- ✅ WCAG 2.1 AA compliance
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Color contrast compliance

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Related Components

- See `vqb_frontend/` for Visual Query Builder
- See `docs/` for full documentation
- See `examples/` for usage examples

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
