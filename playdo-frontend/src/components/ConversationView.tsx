// src/components/Conversation.tsx

import { useEffect, useState } from 'react';
import { Conversation  } from '../types';
import { fetchConversation } from '../services/api';
import Message from './Message';

function ConversationView() {
  // State to store the conversation data
  const [conversation, setConversation] = useState<Conversation | null>(null);
  // State to track loading status
  const [loading, setLoading] = useState(true);
  // State to track any errors
  const [error, setError] = useState<string | null>(null);

  // Effect to fetch the conversation when the component mounts
  useEffect(() => {
    async function loadConversation() {
      try {
        setLoading(true);
        const data = await fetchConversation(1); // hard-codes conversationID=1, TOODO select
        setConversation(data);
        setError(null);
      } catch (err) {
        setError('Failed to load conversation. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadConversation();
  }, []); // Empty dependency array means this runs once on mount

  // Show loading state
  if (loading) {
    return <div className="flex justify-center py-8">Loading conversation...</div>;
  }

  // Show error state
  if (error) {
    return <div className="text-red-500 py-8">{error}</div>;
  }

  // Show empty state
  if (!conversation || !conversation.messages || conversation.messages.length === 0) {
    return <div className="py-8">No messages found.</div>;
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Conversation #{conversation.id}</h1>
      <div className="space-y-4">
        {conversation.messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}
      </div>
    </div>
  );
}

export default ConversationView;
