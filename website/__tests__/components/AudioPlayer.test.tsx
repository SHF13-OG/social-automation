import { render, screen, fireEvent } from '@testing-library/react'
import AudioPlayer from '@/components/AudioPlayer'

// Mock HTMLMediaElement methods
beforeAll(() => {
  Object.defineProperty(HTMLMediaElement.prototype, 'play', {
    configurable: true,
    value: jest.fn().mockResolvedValue(undefined),
  })
  Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
    configurable: true,
    value: jest.fn(),
  })
  Object.defineProperty(HTMLMediaElement.prototype, 'duration', {
    configurable: true,
    get: function () {
      return 120
    },
  })
  Object.defineProperty(HTMLMediaElement.prototype, 'currentTime', {
    configurable: true,
    get: function () {
      return 0
    },
    set: jest.fn(),
  })
})

describe('AudioPlayer', () => {
  const defaultProps = {
    src: '/api/audio/1',
    duration: 120,
  }

  it('renders play button initially', () => {
    render(<AudioPlayer {...defaultProps} />)

    const playButton = screen.getByRole('button', { name: /play/i })
    expect(playButton).toBeInTheDocument()
  })

  it('renders mute button', () => {
    render(<AudioPlayer {...defaultProps} />)

    const muteButton = screen.getByRole('button', { name: /mute/i })
    expect(muteButton).toBeInTheDocument()
  })

  it('renders progress slider', () => {
    render(<AudioPlayer {...defaultProps} />)

    const slider = screen.getByRole('slider')
    expect(slider).toBeInTheDocument()
    expect(slider).toHaveAttribute('min', '0')
    expect(slider).toHaveAttribute('max', '100')
  })

  it('displays formatted duration', () => {
    render(<AudioPlayer {...defaultProps} />)

    expect(screen.getByText('2:00')).toBeInTheDocument()
  })

  it('displays 0:00 as initial time', () => {
    render(<AudioPlayer {...defaultProps} />)

    expect(screen.getByText('0:00')).toBeInTheDocument()
  })

  it('toggles play state when play button is clicked', () => {
    render(<AudioPlayer {...defaultProps} />)

    const playButton = screen.getByRole('button', { name: /play/i })
    fireEvent.click(playButton)

    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()
  })

  it('shows pause button after clicking play', () => {
    render(<AudioPlayer {...defaultProps} />)

    const playButton = screen.getByRole('button', { name: /play/i })
    fireEvent.click(playButton)

    const pauseButton = screen.getByRole('button', { name: /pause/i })
    expect(pauseButton).toBeInTheDocument()
  })

  it('displays "--:--" when duration is not provided', () => {
    render(<AudioPlayer src="/api/audio/1" />)

    expect(screen.getByText('--:--')).toBeInTheDocument()
  })

  it('handles seek via slider', () => {
    render(<AudioPlayer {...defaultProps} />)

    const slider = screen.getByRole('slider')
    fireEvent.change(slider, { target: { value: '50' } })

    expect(slider).toHaveValue('50')
  })

  it('toggles mute when mute button is clicked', () => {
    render(<AudioPlayer {...defaultProps} />)

    const muteButton = screen.getByRole('button', { name: /mute/i })
    fireEvent.click(muteButton)

    const unmuteButton = screen.getByRole('button', { name: /unmute/i })
    expect(unmuteButton).toBeInTheDocument()
  })
})
