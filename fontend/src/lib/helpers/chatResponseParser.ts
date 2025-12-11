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
    // The message field contains a Python string representation, not JSON
    // We need to extract the last AI message content using regex
    const messageStr = response.message;
    
    // Look for the last AIMessage with content (JSON-only mode)
    // We need to find the last AIMessage and extract its content
    const aiMessages = [];
    const aiMessageRegex = /AIMessage\(content='((?:[^'\\]|\\.)*)'/g;
    let match;
    
    while ((match = aiMessageRegex.exec(messageStr)) !== null) {
      aiMessages.push(match[1]);
    }
    
    if (aiMessages.length === 0) {
      throw new Error('No AI message content found in response');
    }
    
    // Get the last AI message (most recent)
    const lastAIContent = aiMessages[aiMessages.length - 1];
    
    // Unescape the content
    let jsonContent = lastAIContent
      .replace(/\\'/g, "'")
      .replace(/\\n/g, '\n')
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, '\\');
    
    console.log('Extracted AI message content (first 200 chars):', jsonContent.substring(0, 200));
    console.log('Full content length:', jsonContent.length);
    
    // Try to parse as JSON
    try {
      return JSON.parse(jsonContent);
    } catch (parseError) {
      console.log('Content is not JSON, returning as string:', jsonContent);
      return jsonContent;
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
    const messageStr = response.message;
    
    // Look for ToolMessage with the specified tool name
    const toolPattern = new RegExp(`ToolMessage\\(content='((?:[^'\\\\]|\\\\.)*)'.+?name='${toolName}'`, 'g');
    const match = toolPattern.exec(messageStr);
    
    if (match && match[1]) {
      let jsonContent = match[1];
      
      // Unescape the content
      jsonContent = jsonContent
        .replace(/\\'/g, "'")
        .replace(/\\n/g, '\n')
        .replace(/\\"/g, '"')
        .replace(/\\\\/g, '\\');
      
      console.log(`Extracted tool result for ${toolName}:`, jsonContent);
      
      // Try to parse as JSON
      try {
        return JSON.parse(jsonContent);
      } catch (parseError) {
        console.log('Tool content is not JSON, returning as string:', jsonContent);
        return jsonContent;
      }
    }
    
    return null;
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
    const messageStr = response.message;
    
    // Look for the last AIMessage with content
    const aiMessages = [];
    const aiMessageRegex = /AIMessage\(content='((?:[^'\\]|\\.)*)'/g;
    let match;
    
    while ((match = aiMessageRegex.exec(messageStr)) !== null) {
      aiMessages.push(match[1]);
    }
    
    if (aiMessages.length === 0) {
      return false;
    }
    
    // Get the last AI message (most recent)
    let jsonContent = aiMessages[aiMessages.length - 1];
      
    // Unescape the content
    jsonContent = jsonContent
      .replace(/\\'/g, "'")
      .replace(/\\n/g, '\n')
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, '\\');
    
    // Check if the content is valid JSON
    try {
      JSON.parse(jsonContent);
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
