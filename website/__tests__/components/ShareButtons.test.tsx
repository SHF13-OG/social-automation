import { render, screen, fireEvent } from '@testing-library/react'
import ShareButtons from '@/components/ShareButtons'

describe('ShareButtons', () => {
  const defaultProps = {
    title: 'Test Prayer',
    text: 'This is a test prayer text',
    url: 'https://2ndhalffaith.com/prayer/2024-01-01',
  }

  beforeEach(() => {
    // Reset window.open mock
    jest.spyOn(window, 'open').mockImplementation(() => null)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders share label', () => {
    render(<ShareButtons {...defaultProps} />)

    expect(screen.getByText('Share:')).toBeInTheDocument()
  })

  it('renders Facebook share button', () => {
    render(<ShareButtons {...defaultProps} />)

    const facebookButton = screen.getByRole('button', { name: /share on facebook/i })
    expect(facebookButton).toBeInTheDocument()
  })

  it('renders X (Twitter) share button', () => {
    render(<ShareButtons {...defaultProps} />)

    const twitterButton = screen.getByRole('button', { name: /share on x/i })
    expect(twitterButton).toBeInTheDocument()
  })

  it('renders TikTok follow link', () => {
    render(<ShareButtons {...defaultProps} />)

    const tiktokLink = screen.getByRole('link', { name: /follow on tiktok/i })
    expect(tiktokLink).toBeInTheDocument()
    expect(tiktokLink).toHaveAttribute('href', 'https://www.tiktok.com/@2ndhalf_faith')
    expect(tiktokLink).toHaveAttribute('target', '_blank')
    expect(tiktokLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('opens Facebook share dialog when clicked', () => {
    render(<ShareButtons {...defaultProps} />)

    const facebookButton = screen.getByRole('button', { name: /share on facebook/i })
    fireEvent.click(facebookButton)

    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('facebook.com/sharer'),
      '_blank',
      'width=600,height=400'
    )
  })

  it('encodes URL in Facebook share dialog', () => {
    render(<ShareButtons {...defaultProps} />)

    const facebookButton = screen.getByRole('button', { name: /share on facebook/i })
    fireEvent.click(facebookButton)

    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining(encodeURIComponent(defaultProps.url)),
      '_blank',
      'width=600,height=400'
    )
  })

  it('opens Twitter share dialog when clicked', () => {
    render(<ShareButtons {...defaultProps} />)

    const twitterButton = screen.getByRole('button', { name: /share on x/i })
    fireEvent.click(twitterButton)

    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('twitter.com/intent/tweet'),
      '_blank',
      'width=600,height=400'
    )
  })

  it('includes text and URL in Twitter share dialog', () => {
    render(<ShareButtons {...defaultProps} />)

    const twitterButton = screen.getByRole('button', { name: /share on x/i })
    fireEvent.click(twitterButton)

    const expectedUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(defaultProps.text)}&url=${encodeURIComponent(defaultProps.url)}`
    expect(window.open).toHaveBeenCalledWith(
      expectedUrl,
      '_blank',
      'width=600,height=400'
    )
  })

  it('uses window.location.href when url prop is not provided', () => {
    // Mock window.location
    const originalLocation = window.location
    delete (window as any).location
    window.location = { href: 'https://2ndhalffaith.com' } as Location

    render(<ShareButtons title="Test" text="Test text" />)

    const facebookButton = screen.getByRole('button', { name: /share on facebook/i })
    fireEvent.click(facebookButton)

    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining(encodeURIComponent('https://2ndhalffaith.com')),
      '_blank',
      'width=600,height=400'
    )

    // Restore
    window.location = originalLocation
  })
})
