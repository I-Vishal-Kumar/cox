/**
 * Session management utilities for conversation persistence
 */

// Generate a UUID v4
export const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

// Session storage keys
const CONVERSATION_ID_KEY = 'cox_automotive_conversation_id';
const SESSION_TIMESTAMP_KEY = 'cox_automotive_session_timestamp';

// Session timeout (24 hours)
const SESSION_TIMEOUT = 24 * 60 * 60 * 1000;

export class SessionManager {
  /**
   * Get or create a conversation ID
   * Creates a new one if none exists or if the session has expired
   */
  static getConversationId(): string {
    try {
      const existingId = sessionStorage.getItem(CONVERSATION_ID_KEY);
      const timestamp = sessionStorage.getItem(SESSION_TIMESTAMP_KEY);
      
      // Check if session is still valid
      if (existingId && timestamp) {
        const sessionAge = Date.now() - parseInt(timestamp);
        if (sessionAge < SESSION_TIMEOUT) {
          return existingId;
        }
      }
      
      // Create new session
      const newId = generateUUID();
      sessionStorage.setItem(CONVERSATION_ID_KEY, newId);
      sessionStorage.setItem(SESSION_TIMESTAMP_KEY, Date.now().toString());
      
      return newId;
    } catch (error) {
      // Fallback if sessionStorage is not available
      console.warn('SessionStorage not available, using temporary ID');
      return generateUUID();
    }
  }

  /**
   * Clear the current session
   */
  static clearSession(): void {
    try {
      sessionStorage.removeItem(CONVERSATION_ID_KEY);
      sessionStorage.removeItem(SESSION_TIMESTAMP_KEY);
    } catch (error) {
      console.warn('Failed to clear session storage');
    }
  }

  /**
   * Refresh the session timestamp
   */
  static refreshSession(): void {
    try {
      const existingId = sessionStorage.getItem(CONVERSATION_ID_KEY);
      if (existingId) {
        sessionStorage.setItem(SESSION_TIMESTAMP_KEY, Date.now().toString());
      }
    } catch (error) {
      console.warn('Failed to refresh session');
    }
  }

  /**
   * Check if we have an active session
   */
  static hasActiveSession(): boolean {
    try {
      const existingId = sessionStorage.getItem(CONVERSATION_ID_KEY);
      const timestamp = sessionStorage.getItem(SESSION_TIMESTAMP_KEY);
      
      if (existingId && timestamp) {
        const sessionAge = Date.now() - parseInt(timestamp);
        return sessionAge < SESSION_TIMEOUT;
      }
      
      return false;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get session info for debugging
   */
  static getSessionInfo(): { id: string; timestamp: string; age: number } | null {
    try {
      const id = sessionStorage.getItem(CONVERSATION_ID_KEY);
      const timestamp = sessionStorage.getItem(SESSION_TIMESTAMP_KEY);
      
      if (id && timestamp) {
        return {
          id,
          timestamp,
          age: Date.now() - parseInt(timestamp)
        };
      }
      
      return null;
    } catch (error) {
      return null;
    }
  }
}