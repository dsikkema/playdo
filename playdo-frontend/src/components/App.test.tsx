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
      {/**
       * Claude says the following:
       * About the button - this is a simplification for testing purposes. The real component might have a dropdown select, but for testing,
       * all we need is a way to trigger the onSelectConversation function. A button with a click handler is an easy way to do this in tests.
       * The data-testid attributes are special markers added to elements solely for testing purposes. They make it easy to find elements in
       * tests without relying on text content or CSS selectors that might change. This approach isn't buggy or misleading - it's a common
       * testing pattern called "component mocking" where you replace complex child components with simpler versions that provide the same
       * interface but with minimal implementation. The test is focused on how App interacts with its children, not on the internal workings
       * of those children.
       */}
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
