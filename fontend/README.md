# Cox Automotive AI Analytics Frontend

## Overview

The Cox Automotive AI Analytics Frontend is a modern Next.js application that provides an intuitive interface for AI-powered data analytics. Built with React, TypeScript, and Tailwind CSS, it offers conversational BI capabilities, real-time dashboards, and interactive data visualization.

## Features

### 🤖 Conversational AI Interface
- Natural language query processing
- Real-time chat with AI analytics assistant
- Streaming responses for complex queries
- Context-aware conversations with history

### 📊 Interactive Dashboards
- **Invite Dashboard** - Marketing campaign performance and ROI
- **F&I Analysis** - Finance & Insurance revenue tracking
- **Logistics Dashboard** - Shipment delays and carrier performance
- **Plant Dashboard** - Manufacturing downtime analysis
- **KPI Alerts** - Real-time monitoring and alerting

### 🎯 Demo Scenarios
- Pre-built analysis scenarios for quick testing
- F&I revenue drop analysis
- Logistics delay root cause analysis
- Plant downtime investigation

### 📈 Data Visualization
- Interactive charts with Recharts
- SQL query display for transparency
- Tabular data presentation
- Export capabilities

## Technology Stack

### Core Framework
- **Next.js 14** - React framework with App Router
- **React 18** - UI library with hooks and modern patterns
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework

### UI Components
- **Heroicons** - Beautiful SVG icons
- **Recharts** - Composable charting library
- **clsx** - Conditional className utility
- **date-fns** - Date manipulation library

### Development Tools
- **ESLint** - Code linting
- **PostCSS** - CSS processing
- **Autoprefixer** - CSS vendor prefixing

## Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn package manager
- Backend API running on `http://localhost:8000`

### Setup

1. **Navigate to frontend directory**
```bash
cd co/fontend
```

2. **Install dependencies**
```bash
npm install
# or
yarn install
```

3. **Start development server**
```bash
npm run dev
# or
yarn dev
```

4. **Open in browser**
Navigate to `http://localhost:3000`

## Project Structure

```
co/fontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── alerts/            # KPI alerts page
│   │   ├── analysis/          # Analysis dashboards
│   │   │   ├── fni/          # F&I analysis
│   │   │   ├── logistics/    # Logistics analysis
│   │   │   └── plant/        # Plant analysis
│   │   ├── catalog/           # Data catalog page
│   │   ├── invite/            # Marketing dashboard
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Home page
│   ├── components/            # Reusable components
│   │   ├── chat/             # Chat interface components
│   │   │   └── ChatInterface.tsx
│   │   ├── dashboard/        # Dashboard components
│   │   └── ui/               # UI components
│   │       ├── Header.tsx
│   │       └── Sidebar.tsx
│   ├── lib/                  # Utility libraries
│   │   └── api.ts            # API client functions
│   └── types/                # TypeScript type definitions
│       └── index.ts
├── public/                   # Static assets
├── next.config.js           # Next.js configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies and scripts
```

## Key Components

### ChatInterface
The main conversational AI component featuring:
- Real-time messaging with the AI assistant
- Demo scenario quick-start buttons
- SQL query display toggle
- Data table visualization
- Recommendation chips
- Backend status indicator

### Sidebar Navigation
Organized navigation with:
- **Main Section**: Core functionality (Analytics Chat, Dashboards)
- **Quick Analysis**: Direct access to specialized analysis tools
- **Status Indicators**: Backend connectivity and AI model info

### Dashboard Components
Specialized dashboard views for:
- Marketing campaign performance (Invite)
- F&I revenue analysis
- Logistics and shipment tracking
- Manufacturing plant monitoring
- KPI alerts and monitoring

## API Integration

### Backend Communication
The frontend communicates with the FastAPI backend through:

```typescript
// Main chat endpoint
POST /api/v1/chat
{
  "message": "Why did F&I revenue drop?",
  "conversation_id": "optional-uuid"
}

// Dashboard endpoints
GET /api/v1/dashboard/invite
GET /api/v1/dashboard/fni
GET /api/v1/dashboard/logistics
GET /api/v1/dashboard/plant

// KPI and monitoring
GET /api/v1/kpi/metrics
GET /api/v1/kpi/alerts
```

### Response Handling
- Automatic conversation ID management
- Error handling with fallback to demo mode
- Real-time backend status monitoring
- Streaming response support

## Configuration

### Next.js Configuration (`next.config.js`)
```javascript
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};
```

### Tailwind Configuration
Custom Cox Automotive brand colors:
- **cox-blue**: Primary brand blue palette
- **cox-orange**: Secondary brand orange palette

### TypeScript Configuration
Strict type checking with:
- Path mapping for clean imports (`@/components`)
- Strict mode enabled
- Modern ES features support

## Development

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Lint code
npm run lint
```

### Code Style Guidelines

1. **Components**
   - Use functional components with hooks
   - Implement proper TypeScript interfaces
   - Follow naming conventions (PascalCase for components)

2. **Styling**
   - Use Tailwind CSS utility classes
   - Implement responsive design patterns
   - Follow Cox Automotive brand guidelines

3. **State Management**
   - Use React hooks for local state
   - Implement proper error boundaries
   - Handle loading states gracefully

### Adding New Features

1. **New Dashboard Page**
```typescript
// Create page in app/new-dashboard/page.tsx
'use client';
import Header from '@/components/ui/Header';

export default function NewDashboard() {
  return (
    <div className="flex flex-col h-screen">
      <Header title="New Dashboard" />
      {/* Dashboard content */}
    </div>
  );
}
```

2. **New API Integration**
```typescript
// Add to lib/api.ts
export async function getNewData() {
  const response = await fetch(`${API_BASE}/new-endpoint`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
```

3. **New Component**
```typescript
// Create in components/
interface NewComponentProps {
  data: DataType[];
  onAction: (id: string) => void;
}

export default function NewComponent({ data, onAction }: NewComponentProps) {
  // Component implementation
}
```

## Features in Detail

### Demo Mode
When backend is unavailable, the frontend automatically switches to demo mode:
- Pre-defined responses for common queries
- Simulated data for testing
- Visual indicator of offline status
- Graceful degradation of functionality

### Responsive Design
- Mobile-first approach with Tailwind CSS
- Adaptive sidebar navigation
- Responsive data tables and charts
- Touch-friendly interface elements

### Accessibility
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes
- Focus management

### Performance Optimization
- Next.js automatic code splitting
- Image optimization
- Static generation where possible
- Efficient re-rendering with React hooks

## Deployment

### Production Build
```bash
npm run build
npm run start
```

### Environment Variables
Create `.env.local` for environment-specific configuration:
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Vercel Deployment
The application is optimized for Vercel deployment:
1. Connect GitHub repository
2. Configure environment variables
3. Deploy automatically on push

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify backend is running on `http://localhost:8000`
   - Check CORS configuration in backend
   - Ensure network connectivity

2. **Build Errors**
   - Clear `.next` directory: `rm -rf .next`
   - Reinstall dependencies: `rm -rf node_modules && npm install`
   - Check TypeScript errors: `npm run lint`

3. **Styling Issues**
   - Verify Tailwind CSS is properly configured
   - Check for conflicting CSS classes
   - Ensure PostCSS is processing correctly

4. **Performance Issues**
   - Use React DevTools Profiler
   - Check for unnecessary re-renders
   - Optimize large data sets with pagination

### Debug Mode

Enable debug logging:
```typescript
// In components, add console logging
console.log('Debug info:', { data, state });
```

Use React Developer Tools for:
- Component tree inspection
- Props and state debugging
- Performance profiling

## Testing

### Manual Testing Checklist

1. **Chat Interface**
   - [ ] Send messages and receive responses
   - [ ] Demo scenarios work correctly
   - [ ] SQL queries display properly
   - [ ] Data tables render correctly

2. **Navigation**
   - [ ] Sidebar navigation works
   - [ ] Page routing functions
   - [ ] Back/forward browser navigation

3. **Responsive Design**
   - [ ] Mobile layout adapts correctly
   - [ ] Tablet view is functional
   - [ ] Desktop experience is optimal

4. **Error Handling**
   - [ ] Backend offline mode works
   - [ ] API errors display properly
   - [ ] Loading states are shown

## Contributing

### Development Workflow

1. **Setup Development Environment**
   ```bash
   git clone <repository>
   cd co/fontend
   npm install
   npm run dev
   ```

2. **Make Changes**
   - Follow TypeScript best practices
   - Use Tailwind CSS for styling
   - Test across different screen sizes

3. **Testing**
   - Test with backend online and offline
   - Verify responsive design
   - Check accessibility compliance

4. **Code Review**
   - Ensure type safety
   - Follow component patterns
   - Verify performance impact

### Coding Standards

- Use TypeScript for all new code
- Follow React hooks patterns
- Implement proper error boundaries
- Write descriptive component props interfaces
- Use semantic HTML elements
- Follow accessibility guidelines

## Future Enhancements

### Planned Features
- Real-time data streaming
- Advanced chart customization
- Export functionality for reports
- User authentication and roles
- Collaborative features
- Mobile app version

### Technical Improvements
- State management with Zustand/Redux
- Component testing with Jest/RTL
- E2E testing with Playwright
- Performance monitoring
- Error tracking integration

## License

Internal Cox Automotive project - All rights reserved.