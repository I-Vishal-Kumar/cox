/**
 * Helper utilities for parsing chat API responses
 */

export interface ChatResponse {
  message: string;
  conversation_id: string;
  query_type: string;
  sql_query: string | null;
  data: any;
  chart_config: any;
  recommendations: any[];
  sources: any;
}

export interface ParsedMessage {
  role: 'human' | 'ai' | 'tool';
  content: string;
  name?: string;
  tool_calls?: any[];
}

/**
 * Extract clean JSON data from chat API response
 * Works with both normal and JSON-only mode responses
 */
export function extractJSONFromChatResponse(response: ChatResponse): any {
  try {
    // Parse the message field which contains the messages array
    const messagesData = JSON.parse(response.message);
    const messages: ParsedMessage[] = messagesData.messages;
    
    // Get the last AI message (final response)
    const lastAIMessage = [...messages]
      .reverse()
      .find(m => m.role === 'ai' || m.content);
    
    if (!lastAIMessage) {
      throw new Error('No AI message found in response');
    }
    
    // Try to parse the content as JSON
    try {
      return JSON.parse(lastAIMessage.content);
    } catch {
      // If it's not valid JSON, return the content as-is
      return lastAIMessage.content;
    }
  } catch (error) {
    console.error('Failed to extract JSON from chat response:', error);
    throw error;
  }
}

/**
 * Get the tool result from chat response
 * Useful for debugging or getting intermediate results
 */
export function getToolResult(response: ChatResponse, toolName: string): any {
  try {
    const messagesData = JSON.parse(response.message);
    const messages: ParsedMessage[] = messagesData.messages;
    
    // Find the tool message with the specified name
    const toolMessage = messages.find(m => m.name === toolName);
    
    if (!toolMessage) {
      return null;
    }
    
    // Try to parse the tool's content as JSON
    try {
      return JSON.parse(toolMessage.content);
    } catch {
      return toolMessage.content;
    }
  } catch (error) {
    console.error('Failed to get tool result:', error);
    return null;
  }
}

/**
 * Check if the response is in JSON-only mode
 */
export function isJSONOnlyResponse(response: ChatResponse): boolean {
  try {
    const messagesData = JSON.parse(response.message);
    const messages: ParsedMessage[] = messagesData.messages;
    
    const lastAIMessage = [...messages]
      .reverse()
      .find(m => m.role === 'ai' || m.content);
    
    if (!lastAIMessage) return false;
    
    // Check if the content is valid JSON
    try {
      JSON.parse(lastAIMessage.content);
      return true;
    } catch {
      return false;
    }
  } catch {
    return false;
  }
}

// Example usage:
/*
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: "Get weekly F&I revenue trends for the last 4 weeks, return as JSON",
    conversation_id: `dashboard_${Date.now()}`
  })
});

const data = await response.json();

// Extract clean JSON
const weeklyTrends = extractJSONFromChatResponse(data);
console.log(weeklyTrends);
// Output: [{ week: "Week 1", midwest: 318012.89, ... }]

// Or get tool result directly
const toolData = getToolResult(data, 'get_weekly_fni_trends');
console.log(toolData);
*/
