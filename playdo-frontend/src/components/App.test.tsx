import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import App from './App'

// Mock the API module
vi.mock('../services/api', () => ({
  fetchConversationIds: vi.fn(),
  fetchConversation: vi.fn()
}))

// Mock the child components
vi.mock('./ConversationSelector', () => ({
  default: ({
    onSelectConversation,
    selectedConversationId
  }: {
    onSelectConversation: (id: number | null) => void
    selectedConversationId: number | null
  }) => (
    <div data-testid="conversation-selector">
      <button
        onClick={() => onSelectConversation(1)}
        data-testid="select-conversation-button"
      >
        Select Conversation 1
      </button>
      <div data-testid="selected-id">{selectedConversationId}</div>
    </div>
  )
}))

vi.mock('./ConversationView', () => ({
  default: ({ conversationId }: { conversationId: number | null }) => (
    <div data-testid="conversation-view">
      {conversationId
        ? `Viewing conversation ${conversationId}`
        : 'No conversation selected'}
    </div>
  )
}))

describe('<App />', () => {
  it('renders the ConversationSelector and ConversationView components', () => {
    // Act
    render(<App />)

    // Assert
    expect(screen.getByTestId('conversation-selector')).toBeInTheDocument()
    expect(screen.getByTestId('conversation-view')).toBeInTheDocument()
  })

  it('passes the selected conversation ID to ConversationView', async () => {
    // Arrange
    const user = userEvent.setup()

    // Act
    render(<App />)

    // Initially, no conversation is selected
    expect(screen.getByText('No conversation selected')).toBeInTheDocument()

    // Select a conversation
    await user.click(screen.getByTestId('select-conversation-button'))

    // Assert
    expect(screen.getByText('Viewing conversation 1')).toBeInTheDocument()
    expect(screen.getByTestId('selected-id').textContent).toBe('1')
  })
})
