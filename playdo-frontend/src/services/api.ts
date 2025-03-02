// src/services/api.ts

import { Conversation } from '../types';

// For now, hardcoded to fetch conversation with ID 6
export async function fetchConversation(id: number): Promise<Conversation> {
  try {
    const response = await fetch(`http://localhost:5000/api/conversations/${id}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data as Conversation;
  } catch (error) {
    // In a real app, you'd want better error handling
    console.error('Error fetching conversation:', error);
    throw error;
  }
}
