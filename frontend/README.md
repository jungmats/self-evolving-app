# Self-Evolving Web Application Frontend

This is the React TypeScript frontend for the Self-Evolving Web Application.

## Features

- Bug report submission form with severity levels
- Feature request submission form with priority levels
- Input validation and error handling
- Real-time feedback with trace ID tracking
- Responsive design with clean UI

## Development Setup

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm start
```

This runs the app in development mode. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits. You will also see any lint errors in the console.

### Building for Production

```bash
npm run build
```

Builds the app for production to the `build` folder. It correctly bundles React in production mode and optimizes the build for the best performance.

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `POST /api/submit/bug` - Submit bug reports
- `POST /api/submit/feature` - Submit feature requests  
- `GET /api/status/{trace_id}` - Get request status

The frontend uses a proxy configuration to forward API requests to the backend server running on port 8000.

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   ├── BugReportForm.tsx      # Bug report form component
│   │   └── FeatureRequestForm.tsx # Feature request form component
│   ├── api.ts              # API client functions
│   ├── types.ts            # TypeScript type definitions
│   ├── App.tsx             # Main application component
│   ├── index.tsx           # Application entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
└── tsconfig.json          # TypeScript configuration
```

## Usage

1. Select either "Bug Report" or "Feature Request" tab
2. Fill in the required fields:
   - **Title**: Brief description of the issue/feature
   - **Description**: Detailed explanation
   - **Severity/Priority**: Select appropriate level
3. Click submit to send the request
4. Note the Trace ID for tracking your request status

## Testing

The frontend integration is tested through the backend test suite. The tests verify:

- Frontend files are properly structured
- API endpoints work correctly with frontend requests
- Form validation and submission flow
- Error handling and user feedback