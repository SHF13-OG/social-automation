# Testing Framework

This document outlines the comprehensive testing strategy for 2nd Half Faith.

## Quick Start

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test category
npm test -- --testPathPattern="__tests__/auth"
npm test -- --testPathPattern="__tests__/api"
npm test -- --testPathPattern="__tests__/website"
npm test -- --testPathPattern="__tests__/data"
npm test -- --testPathPattern="__tests__/tiktok"

# Run in watch mode
npm test -- --watch
```

## Test Categories

### 1. Authentication Tests (`__tests__/auth/`)

Tests for OAuth flow and session management.

| File | Purpose |
|------|---------|
| `google-oauth.test.ts` | Validates Google OAuth URL construction, state handling, admin email restriction |
| `session.test.ts` | Tests JWT session creation, validation, and expiration |

### 2. API Tests (`__tests__/api/`)

Tests for REST API endpoints.

| File | Purpose |
|------|---------|
| `analytics.test.ts` | Analytics endpoint authentication and data formatting |
| `queue.test.ts` | Queue endpoint for scheduled posts |
| `themes.test.ts` | Theme management CRUD operations |
| `prayer-today.test.ts` | Daily prayer retrieval |
| `audio.test.ts` | Audio generation endpoint |

### 3. Website Tests (`__tests__/website/`)

Tests for page rendering and components.

| File | Purpose |
|------|---------|
| `pages.test.ts` | Page rendering and routing |
| `components.test.ts` | Key component behavior |

### 4. Data Quality Tests (`__tests__/data/`)

Tests for data integrity and freshness.

| File | Purpose |
|------|---------|
| `freshness.test.ts` | Validates recent content exists |
| `integrity.test.ts` | Database schema and referential integrity |

### 5. TikTok Integration Tests (`__tests__/tiktok/`)

Tests for TikTok API integration.

| File | Purpose |
|------|---------|
| `api-mock.test.ts` | TikTok API response mocking |
| `publishing.test.ts` | Video publishing flow |

## Test Schedules

| Schedule | Trigger | Categories | Purpose |
|----------|---------|------------|---------|
| **CI** | Every push/PR | auth, api, website | Validate changes don't break functionality |
| **Deploy** | PR merge to main | All + build | Ensure production readiness |
| **Daily** | 6:00 AM UTC | data, tiktok | Monitor data freshness and integrations |

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

1. **Lint & Type Check** - ESLint and TypeScript validation
2. **Unit Tests** - All test categories with coverage
3. **Build** - Next.js and Cloudflare build verification

Test results are stored and viewable in the admin dashboard at `/admin/tests`.

## Writing Tests

### Test File Structure

```typescript
/**
 * Tests for [feature name]
 *
 * Purpose: [Brief description]
 * Schedule: [ci/deploy/daily]
 */

describe('Feature Name', () => {
  beforeEach(() => {
    // Setup
  })

  afterEach(() => {
    // Cleanup
  })

  it('describes expected behavior', () => {
    // Arrange
    // Act
    // Assert
  })
})
```

### Mocking Patterns

**Session mocking:**
```typescript
const mockGetSession = jest.fn()
jest.mock('@/lib/session', () => ({
  getSession: () => mockGetSession(),
}))
```

**Database mocking:**
```typescript
jest.mock('@/lib/db', () => ({
  getDb: () => mockDb,
  ensureDb: () => Promise.resolve(mockDb),
}))
```

**Environment variables:**
```typescript
const originalEnv = process.env
beforeEach(() => {
  process.env = { ...originalEnv, KEY: 'test-value' }
})
afterEach(() => {
  process.env = originalEnv
})
```

## Coverage Requirements

Target coverage: **80%** for new code

Coverage is collected for:
- `components/**/*.{ts,tsx}`
- `lib/**/*.{ts,tsx}`
- `app/api/**/*.{ts,tsx}`

View coverage report after running tests at `coverage/lcov-report/index.html`.

## Test Dashboard

The admin dashboard at `/admin/tests` displays:
- Test run history (last 30 days)
- Pass/fail status
- Coverage percentage
- Category breakdown
- Run type (CI/Deploy/Daily)

## Troubleshooting

### Tests failing locally but passing in CI

1. Clear Jest cache: `npx jest --clearCache`
2. Reinstall dependencies: `rm -rf node_modules && npm ci`
3. Check environment variables match CI

### Module resolution errors

Ensure `jest.config.js` has the correct `moduleNameMapper`:
```javascript
moduleNameMapper: {
  '^@/(.*)$': '<rootDir>/$1',
}
```

### Async test timeouts

Increase timeout for slow operations:
```typescript
it('long operation', async () => {
  // test
}, 10000) // 10 second timeout
```
