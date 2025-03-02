import { useState, useEffect } from 'react';
import { fetchConversationIds } from '../services/api';

type ConversationSelectorProps = {
  selectedConversationId: number | null;
  onSelectConversation: (id: number | null) => void;
};

function ConversationSelector({
    onSelectConversation,
    selectedConversationId
}: ConversationSelectorProps) {
    const [conversationIds, setConversationIds] = useState<number[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadConversationIds() {
            try {
                setLoading(true);
                const ids = await fetchConversationIds();
                setConversationIds(ids);
                setError(null);
            } catch (e) {
                setError('Failed to load conversation, please try again.');
                console.error(e);
            } finally {
                setLoading(false);
            }
        }

        loadConversationIds();
    }, []);

    /**
     * On the changing of the selector, call the callback given as a prop which will
     * cause the conversation to render
     */
    const handleSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const value = event.target.value;
        if (value === "") {
            onSelectConversation(null);
        } else {
            onSelectConversation(Number(value))
        }
    };

    return (
        <div className="bg-white shadow p-4 mb-6 rounded-lg">
            {/**
             * Note on tailwind css classes above:
             * bg-white: background color
             * shadow: a little border effect of a thin shadow surrounding the element, cast onto its parent element background
             * p-4: padding on all sides (just p, not pt for p-top for instance), (4) represents how much (4*0.25rem == 4*4px). padding means "inside the element"
             * mb-6: margin (m) added to bottom (b). (6) is how much. Margin is "outside the element"
             * rounded-lg: round the corners, (lg) means large radius roundness
             *
             * Too many more below to research. Thank you AI.
             */}
          <div className="max-w-2xl mx-auto">
            <label htmlFor="conversation-select" className="block text-sm font-medium text-gray-700 mb-2">
              Select a conversation:
            </label>
            <div className="relative">
              <select
                id="conversation-select"
                className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                value={selectedConversationId === null ? "" : selectedConversationId.toString()}
                onChange={handleSelectChange}
                disabled={loading}
              >
                <option value="">-- Select a conversation --</option>
                {conversationIds.map((id) => (
                  <option key={id} value={id}>
                    Conversation #{id}
                  </option>
                ))}
              </select>
              {loading && (
                <div className="absolute inset-y-0 right-0 flex items-center pr-12 pointer-events-none">
                  <p className="text-sm text-gray-500">Loading...</p>
                </div>
              )}
            </div>
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          </div>
        </div>
      );
}

export default ConversationSelector;
