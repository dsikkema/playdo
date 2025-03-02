import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import ConversationView from './ConversationView'
import { fetchConversation } from '../services/api'
import { Conversation } from '../types'

// Mock the API module
vi.mock('../services/api', () => ({
  fetchConversation: vi.fn()
}))

// Mock implementation of fetchConversation
const mockFetchConversation = fetchConversation as unknown as ReturnType<
  typeof vi.fn
>

describe('<ConversationView />', () => {
  // Reset mocks before each test
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Test case for null conversationId
  it('shows "select a conversation" message when no conversation is selected', () => {
    // Act
    render(<ConversationView conversationId={null} />)

    // Assert
    expect(
      screen.getByText('Please select a conversation from the list.')
    ).toBeInTheDocument()
    expect(mockFetchConversation).not.toHaveBeenCalled()
  })

  // Test case for loading state
  it('shows loading state while fetching conversation', async () => {
    // Arrange
    // Create a promise that won't resolve immediately to keep the component in loading state
    const fetchPromise = new Promise<Conversation>(() => {})
    mockFetchConversation.mockReturnValue(fetchPromise)

    // Act
    render(<ConversationView conversationId={1} />)

    // Assert
    expect(screen.getByText('Loading conversation...')).toBeInTheDocument()
    expect(mockFetchConversation).toHaveBeenCalledWith(1)
  })

  // Test case for error state
  it('shows error message when API call fails', async () => {
    // Arrange
    mockFetchConversation.mockRejectedValue(new Error('API error'))

    // Act
    render(<ConversationView conversationId={1} />)

    // Assert
    await waitFor(() => {
      expect(
        screen.getByText('Failed to load conversation. Please try again later.')
      ).toBeInTheDocument()
    })
    expect(mockFetchConversation).toHaveBeenCalledWith(1)
  })

  // Test case for empty conversation
  it('shows "no messages" when conversation has no messages', async () => {
    // Arrange
    const emptyConversation: Conversation = {
      id: 1,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      messages: []
    }
    mockFetchConversation.mockResolvedValue(emptyConversation)

    // Act
    render(<ConversationView conversationId={1} />)

    // Assert
    await waitFor(() => {
      expect(screen.getByText('No messages found.')).toBeInTheDocument()
    })
    expect(mockFetchConversation).toHaveBeenCalledWith(1)
  })

  // Test case for conversation with a single message
  it('renders a conversation with a single message correctly', async () => {
    // Arrange
    const singleMessageConversation: Conversation = {
      id: 1,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      messages: [
        {
          role: 'user',
          content: [{ type: 'text', text: 'This is a single message' }]
        }
      ]
    }
    mockFetchConversation.mockResolvedValue(singleMessageConversation)

    // Act
    render(<ConversationView conversationId={1} />)

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Conversation #1')).toBeInTheDocument()
      expect(screen.getByText('You')).toBeInTheDocument()
      expect(screen.getByText('This is a single message')).toBeInTheDocument()
    })
    expect(mockFetchConversation).toHaveBeenCalledWith(1)
  })

  // Test case for conversation with multiple messages
  it('renders a conversation with multiple messages correctly', async () => {
    // Arrange
    const multipleMessagesConversation: Conversation = {
      id: 2,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      messages: [
        {
          role: 'user',
          content: [{ type: 'text', text: 'Hello, how are you?' }]
        },
        {
          role: 'assistant',
          content: [{ type: 'text', text: 'I am doing well, thank you!' }]
        },
        {
          role: 'user',
          content: [{ type: 'text', text: 'That is good to hear.' }]
        }
      ]
    }
    mockFetchConversation.mockResolvedValue(multipleMessagesConversation)

    // Act
    render(<ConversationView conversationId={2} />)

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Conversation #2')).toBeInTheDocument()
      expect(screen.getAllByText('You').length).toBe(2)
      expect(screen.getByText('Assistant')).toBeInTheDocument()
      expect(screen.getByText('Hello, how are you?')).toBeInTheDocument()
      expect(
        screen.getByText('I am doing well, thank you!')
      ).toBeInTheDocument()
      expect(screen.getByText('That is good to hear.')).toBeInTheDocument()
    })
    expect(mockFetchConversation).toHaveBeenCalledWith(2)
  })
})
