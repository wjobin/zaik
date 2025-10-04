# Zaik Frontend

React-based frontend for the Zaik text-based adventure game. Built with React, TypeScript, and Vite.

## Getting Started

### Prerequisites

- Node.js 18+ (or use mise: `mise use node@lts`)
- npm

### Installation

```bash
npm install
```

### Development

Run the development server with hot module reloading:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

Create a production build:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

### Linting

Run ESLint to check code quality:

```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx          # Main application component
│   ├── main.tsx         # Application entry point
│   ├── assets/          # Static assets (images, icons)
│   └── *.css            # Styles
├── public/              # Public static files
├── index.html           # HTML template
└── vite.config.ts       # Vite configuration
```

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool with HMR
- **ESLint** - Code linting

## Development Notes

### Architecture Principles

- Keep UI state separate from game state
- Game state should be managed by the backend
- UI components should be presentational where possible
- Use React hooks for local state management

### Backend Integration

The frontend will communicate with the FastAPI backend running on `http://localhost:8000`. API endpoints will be added as game features are implemented.

### Terminal-like Interface

The UI is designed to provide a terminal-like text interface for the adventure game, mimicking classic text adventures like Zork.

## Vite + React + TypeScript

This template uses:
- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) - Uses Babel for Fast Refresh
- TypeScript for type safety
- ESLint for code quality

### Expanding the ESLint Configuration

For production applications, consider enabling type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      tseslint.configs.recommendedTypeChecked,
      // Or stricter: tseslint.configs.strictTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
])
```

## Contributing

Follow the development workflow in the main project [CLAUDE.md](../CLAUDE.md):
1. Check the Notion board for tasks
2. Move tasks to "In Progress" when starting
3. Commit and push changes when complete
4. Move tasks to "Done" when finished
