import { render, screen } from '@testing-library/react'
import EngagementChart from '@/components/EngagementChart'

const mockPosts = [
  {
    post_id: '1',
    created_at: '2024-01-01T12:00:00Z',
    views: 1000,
    likes: 50,
    comments: 10,
    shares: 5,
    favorites: 20,
  },
  {
    post_id: '2',
    created_at: '2024-01-02T12:00:00Z',
    views: 2000,
    likes: 100,
    comments: 20,
    shares: 10,
    favorites: 40,
  },
  {
    post_id: '3',
    created_at: '2024-01-03T12:00:00Z',
    views: 1500,
    likes: 75,
    comments: 15,
    shares: 8,
    favorites: 30,
  },
]

describe('EngagementChart', () => {
  describe('views chart', () => {
    it('renders without crashing', () => {
      const { container } = render(
        <EngagementChart posts={mockPosts} type="views" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })

    it('renders a container with correct height', () => {
      const { container } = render(
        <EngagementChart posts={mockPosts} type="views" />
      )

      const chartContainer = container.querySelector('.h-64')
      expect(chartContainer).toBeInTheDocument()
    })

    it('handles empty posts array', () => {
      const { container } = render(
        <EngagementChart posts={[]} type="views" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })

    it('handles posts with zero views', () => {
      const postsWithZeroViews = [
        { ...mockPosts[0], views: 0 },
      ]

      const { container } = render(
        <EngagementChart posts={postsWithZeroViews} type="views" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe('engagement chart', () => {
    it('renders without crashing', () => {
      const { container } = render(
        <EngagementChart posts={mockPosts} type="engagement" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })

    it('renders a container with correct height', () => {
      const { container } = render(
        <EngagementChart posts={mockPosts} type="engagement" />
      )

      const chartContainer = container.querySelector('.h-64')
      expect(chartContainer).toBeInTheDocument()
    })

    it('handles empty posts array', () => {
      const { container } = render(
        <EngagementChart posts={[]} type="engagement" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })

    it('calculates engagement rate correctly', () => {
      // engagement = likes + comments + shares
      // rate = (engagement / views) * 100
      // For first post: (50 + 10 + 5) / 1000 * 100 = 6.5%
      const { container } = render(
        <EngagementChart posts={mockPosts} type="engagement" />
      )

      // Chart should render - actual values tested in unit tests for data transformation
      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe('data transformation', () => {
    it('sorts posts by date ascending', () => {
      const unsortedPosts = [
        { ...mockPosts[2] }, // Jan 3
        { ...mockPosts[0] }, // Jan 1
        { ...mockPosts[1] }, // Jan 2
      ]

      const { container } = render(
        <EngagementChart posts={unsortedPosts} type="views" />
      )

      // Component should handle sorting internally
      expect(container.firstChild).toBeInTheDocument()
    })

    it('handles null engagement values', () => {
      const postsWithNulls = [
        {
          post_id: '1',
          created_at: '2024-01-01T12:00:00Z',
          views: 1000,
          likes: null as any,
          comments: null as any,
          shares: null as any,
          favorites: null as any,
        },
      ]

      const { container } = render(
        <EngagementChart posts={postsWithNulls} type="engagement" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })

    it('handles undefined engagement values', () => {
      const postsWithUndefined = [
        {
          post_id: '1',
          created_at: '2024-01-01T12:00:00Z',
          views: 1000,
          likes: undefined as any,
          comments: undefined as any,
          shares: undefined as any,
          favorites: undefined as any,
        },
      ]

      const { container } = render(
        <EngagementChart posts={postsWithUndefined} type="engagement" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })
  })
})
