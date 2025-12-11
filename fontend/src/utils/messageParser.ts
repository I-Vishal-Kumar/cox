/**
 * Utility functions for parsing backend message responses
 */

export const parseMessageContent = (message: any): string => {
  // If it's already a string, return it
  if (typeof message === 'string') {
    // Check if it's a JSON string that needs parsing
    if (message.startsWith('{')) {
      try {
        const parsed = JSON.parse(message);
        return extractMessageFromObject(parsed);
      } catch {
        return message;
      }
    }
    return message;
  }

  // If it's an object, extract the message content
  if (typeof message === 'object' && message !== null) {
    return extractMessageFromObject(message);
  }

  // Fallback to string representation
  return String(message);
};

const extractMessageFromObject = (obj: any): string => {
  // Handle LangChain message format
  if (obj.messages && Array.isArray(obj.messages)) {
    const lastMessage = obj.messages[obj.messages.length - 1];
    if (lastMessage && lastMessage.content) {
      return lastMessage.content;
    }
  }

  // Handle direct content property
  if (obj.content) {
    return obj.content;
  }

  // Handle analysis property
  if (obj.analysis) {
    return obj.analysis;
  }

  // Handle message property
  if (obj.message) {
    return typeof obj.message === 'string' ? obj.message : extractMessageFromObject(obj.message);
  }

  // Fallback to JSON string
  return JSON.stringify(obj, null, 2);
};