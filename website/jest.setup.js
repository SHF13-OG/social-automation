import '@testing-library/jest-dom'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: () => '/admin',
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

// Mock next-auth/react
jest.mock('next-auth/react', () => ({
  signOut: jest.fn(),
  useSession: () => ({ data: null, status: 'unauthenticated' }),
}))

// Mock window.matchMedia for recharts
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock ResizeObserver for recharts
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))
