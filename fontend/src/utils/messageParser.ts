/**
 * Utility functions for parsing backend message responses
 */

export const parseMessageContent = (message: unknown): string => {
  // Handle null/undefined
  if (message === null || message === undefined) {
    return '';
  }

  // If it's already a string, clean and return it
  if (typeof message === 'string') {
    // Check if it's a JSON string that needs parsing
    if (message.startsWith('{') || message.startsWith('[')) {
      try {
        const parsed = JSON.parse(message);
        return cleanObjectObjectFromString(extractMessageFromObject(parsed));
      } catch {
        return cleanObjectObjectFromString(message);
      }
    }
    return cleanObjectObjectFromString(message);
  }

  // Handle arrays - filter out objects and join with newlines
  if (Array.isArray(message)) {
    const parsedItems = message
      .map(item => parseMessageContent(item))
      .filter(item => item && item !== '[object Object]' && !item.startsWith('[object Object]'));
    return cleanObjectObjectFromString(parsedItems.join('\n'));
  }

  // If it's an object, extract the message content
  if (typeof message === 'object' && message !== null) {
    return cleanObjectObjectFromString(extractMessageFromObject(message));
  }

  // Fallback to string representation
  const result = String(message);
  return result === '[object Object]' ? '' : cleanObjectObjectFromString(result);
};

/**
 * Remove [object Object] artifacts from strings
 */
const cleanObjectObjectFromString = (str: string): string => {
  if (!str) return '';
  // Remove standalone [object Object] with optional comma/newline separators
  return str
    .replace(/\[object Object\],?\s*/g, '')
    .replace(/,?\s*\[object Object\]/g, '')
    .trim();
};

const extractMessageFromObject = (obj: unknown): string => {
  // Handle null/undefined
  if (obj === null || obj === undefined) {
    return '';
  }

  // Handle arrays - filter and join
  if (Array.isArray(obj)) {
    const results = obj
      .map(item => extractMessageFromObject(item))
      .filter(item => item && item.trim() !== '' && item !== '[object Object]');
    return results.join('\n');
  }

  // Handle non-objects
  if (typeof obj !== 'object') {
    const str = String(obj);
    return str === '[object Object]' ? '' : str;
  }

  const record = obj as Record<string, unknown>;

  // Skip tool_use blocks - they don't contain displayable text
  if (record.type === 'tool_use') {
    return '';
  }

  // Handle LangChain content block format: { type: 'text', text: '...' }
  if (record.type === 'text' && record.text !== undefined) {
    return String(record.text);
  }

  // Handle LangChain message format
  if (record.messages && Array.isArray(record.messages)) {
    const lastMessage = record.messages[record.messages.length - 1] as Record<string, unknown> | undefined;
    if (lastMessage && lastMessage.content) {
      return parseMessageContent(lastMessage.content);
    }
  }

  // Handle direct content property
  if (record.content !== undefined) {
    return parseMessageContent(record.content);
  }

  // Handle analysis property
  if (record.analysis !== undefined) {
    return parseMessageContent(record.analysis);
  }

  // Handle message property
  if (record.message !== undefined) {
    return parseMessageContent(record.message);
  }

  // Handle text property (common in some API responses)
  if (record.text !== undefined) {
    return parseMessageContent(record.text);
  }

  // Handle response property
  if (record.response !== undefined) {
    return parseMessageContent(record.response);
  }

  // Handle output property
  if (record.output !== undefined) {
    return parseMessageContent(record.output);
  }

  // Handle result property
  if (record.result !== undefined) {
    return parseMessageContent(record.result);
  }

  // For unknown objects, return empty string instead of JSON to avoid [object Object]
  // Only stringify if it has meaningful content we want to show
  const keys = Object.keys(record);
  if (keys.length === 0) {
    return '';
  }

  // If it looks like a tool result or internal object, skip it
  if (keys.includes('id') && keys.includes('name') && keys.includes('input')) {
    return ''; // This is a tool_use block structure
  }

  // Fallback to JSON string only for objects that might contain useful data
  try {
    const json = JSON.stringify(obj, null, 2);
    // Don't return if it would result in [object Object] display
    if (json.includes('[object Object]')) {
      return '';
    }
    return json;
  } catch {
    return '';
  }
};
