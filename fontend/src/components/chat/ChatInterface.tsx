'use client';

import { useState, useRef, useEffect } from 'react';
import {
  PaperAirplaneIcon,
  SparklesIcon,
  ChartBarIcon,
  TableCellsIcon,
  LightBulbIcon,
  CodeBracketIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { ConversationMessage, DemoScenario } from '@/types';
import { sendChatMessage, checkHealth, ChatResponse } from '@/lib/api';
import { useDemoScenarios } from '@/hooks/useDemoScenarios';
import { parseMessageContent } from '@/utils/messageParser';
import { SessionManager } from '@/utils/sessionManager';

// Demo responses
const demoResponses: Record<string, string> = {
  fni_midwest: `**F&I Revenue Analysis - Midwest Region**

F&I revenue in the Midwest region declined **11% vs last week**.

**Key Findings:**
• **65%** of the decline came from three dealers: ABC Ford, XYZ Nissan, and Midtown Auto
• The main driver was lower service contract penetration (down from **39% to 27%**), not unit volume
• Finance manager **John Smith** at ABC Ford accounted for a **5-point drop** in attachment rate

**Root Cause Analysis:**
| Dealer | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| ABC Ford | $42,500 | $52,800 | -19.5% |
| XYZ Nissan | $38,200 | $45,100 | -15.3% |
| Midtown Auto | $35,800 | $41,200 | -13.1% |

**Recommendations:**
1. Focus coaching on service contract sales at these three dealers
2. Review any recent promo or pricing changes
3. Schedule 1:1 with John Smith to address attachment rate decline
4. Consider temporary incentive program for service contracts`,

  logistics_delays: `**Logistics Delay Analysis - Past 7 Days**

Over the past 7 days, **18%** of shipments arrived late.

**Delay Attribution:**
• **55%** of delays are concentrated on **Carrier X** on two routes: Chicago → Detroit and Dallas → Kansas City
• Weather was a minor factor (only **3 delays** tagged to storms)
• Average dwell time at the origin yard for Carrier X increased from **1.2 to 3.1 hours**

**Carrier Performance:**
| Carrier | Total | Delayed | Delay Rate | Avg Dwell |
|---------|-------|---------|------------|-----------|
| Carrier X | 87 | 24 | 27.6% | 3.1 hrs |
| Carrier Y | 65 | 4 | 6.2% | 1.3 hrs |
| Carrier Z | 52 | 3 | 5.8% | 1.1 hrs |

**Recommendations:**
1. Escalate with Carrier X on Chicago-Detroit and Dallas-Kansas City routes
2. Re-route high-priority shipments to Carrier Y where capacity is available
3. Review Carrier X's recent operational changes
4. Consider backup carrier allocation for critical routes`,

  plant_downtime: `**Plant Downtime Analysis - This Week**

Three plants recorded significant downtime this week:

**Plant A — Michigan Assembly** (6.5 hours total)
• Mostly on Line 3
• Unplanned conveyor maintenance: **3.1 hours**
• Paint defects quality hold: **2.2 hours**
• Robotic arm calibration: **0.8 hours**
• Defect rate is **2.5x normal**

**Plant B — Ohio Manufacturing** (4.2 hours)
• Line 1 stoppage
• Component shortage from **Supplier Q** (electronic control units)

**Plant C — Indiana Works** (2.3 hours)
• Line 2
• Planned maintenance overrun

**Recommendations:**
1. **Plant A:** Fast-track root cause on paint defects; defect rate is 2.5x normal
2. **Plant B:** Review purchase order lead times and safety stock for components from Supplier Q
3. **Plant C:** Review maintenance scheduling to prevent future overruns
4. Consider predictive maintenance implementation for conveyor systems`,
};

interface ChatInterfaceProps {
  onDataReceived?: (data: Record<string, unknown>[]) => void;
}

export default function ChatInterface({ onDataReceived }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSqlQuery, setShowSqlQuery] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [conversationId, setConversationId] = useState<string>(() => SessionManager.getConversationId());
  const [currentSqlQuery, setCurrentSqlQuery] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Use TanStack Query for demo scenarios
  const { data: demoScenarios = [], isLoading: scenariosLoading, error: scenariosError } = useDemoScenarios();

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      const isHealthy = await checkHealth();
      setBackendStatus(isHealthy ? 'online' : 'offline');
    };
    checkBackend();
    // Re-check every 30 seconds
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleScenarioClick = (scenario: DemoScenario) => {
    setInput(scenario.question);
    handleSend(scenario.question);
  };

  const handleSend = async (messageText?: string) => {
    const text = messageText || input;
    if (!text.trim()) return;

    const userMessage: ConversationMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setCurrentSqlQuery(null);

    // If backend is online, use streaming API; otherwise fall back to demo responses
    if (backendStatus === 'online') {
      try {
        await handleStreamingChat(text);
      } catch (error) {
        console.error('Streaming API Error:', error);
        // Fall back to regular API
        try {
          const currentConversationId = conversationId || SessionManager.getConversationId();
          const response: ChatResponse = await sendChatMessage(text, currentConversationId);
          
          // Extract actual message content using utility function
          const messageContent = parseMessageContent(response.message);

          // Update conversation ID for context and refresh session
          if (response.conversation_id) {
            setConversationId(response.conversation_id);
            SessionManager.refreshSession();
          }

          // Store SQL query for display
          if (response.sql_query) {
            setCurrentSqlQuery(response.sql_query);
          }

          // Notify parent of received data
          if (response.data && onDataReceived) {
            onDataReceived(response.data);
          }

          const assistantMessage: ConversationMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: messageContent,
            timestamp: new Date(),
            sqlQuery: response.sql_query,
            data: response.data,
            queryType: response.query_type,
            recommendations: response.recommendations || [],
          };

          setMessages((prev) => [...prev, assistantMessage]);
        } catch (fallbackError) {
          console.error('Fallback API Error:', fallbackError);
          // Fall back to demo response on error
          const fallbackMessage = getFallbackResponse(text);
          const assistantMessage: ConversationMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: fallbackMessage,
            timestamp: new Date(),
            recommendations: ['Try reconnecting to the backend', 'Check if the server is running'],
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      }
    } else {
      // Offline mode - use demo responses
      const responseText = getFallbackResponse(text);
      const assistantMessage: ConversationMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseText,
        timestamp: new Date(),
        recommendations: [
          'Review the detailed breakdown above',
          'Click on any metric for drill-down analysis',
          'Export data for further analysis',
        ],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }

    setIsLoading(false);
  };

  const handleStreamingChat = async (text: string) => {
    // Ensure we always have a conversation ID
    const currentConversationId = conversationId || SessionManager.getConversationId();
    
    const params = new URLSearchParams({
      message: text,
      conversation_id: currentConversationId,
    });

    const response = await fetch(`http://localhost:8000/api/v1/chat/stream?${params}`);
    
    if (!response.ok) {
      throw new Error(`Streaming API error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body reader available');
    }

    let assistantMessage: ConversationMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      recommendations: [],
    };

    // Add the initial empty message
    setMessages((prev) => [...prev, assistantMessage]);

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'start' && data.conversation_id) {
                setConversationId(data.conversation_id);
                SessionManager.refreshSession();
              } else if (data.type === 'chunk' && data.content) {
                // Update the message content incrementally
                assistantMessage.content += data.content;
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.id === assistantMessage.id 
                      ? { ...msg, content: assistantMessage.content }
                      : msg
                  )
                );
              } else if (data.type === 'data' && data.data) {
                assistantMessage.data = data.data;
                if (onDataReceived) {
                  onDataReceived(data.data);
                }
              } else if (data.type === 'chart' && data.config) {
                assistantMessage.chart_config = data.config;
              } else if (data.type === 'complete' && data.result) {
                const result = data.result;
                assistantMessage.content = result.analysis || assistantMessage.content;
                assistantMessage.sqlQuery = result.sql_query;
                assistantMessage.recommendations = result.recommendations || [];
                
                // Final update
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.id === assistantMessage.id 
                      ? assistantMessage
                      : msg
                  )
                );
              } else if (data.type === 'error') {
                throw new Error(data.error || 'Streaming error occurred');
              }
            } catch (parseError) {
              console.warn('Failed to parse streaming data:', parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  };

  // Helper function for fallback/demo responses
  const getFallbackResponse = (text: string): string => {
    if (text.toLowerCase().includes('f&i') || text.toLowerCase().includes('midwest')) {
      return demoResponses.fni_midwest;
    } else if (
      text.toLowerCase().includes('delay') ||
      text.toLowerCase().includes('carrier')
    ) {
      return demoResponses.logistics_delays;
    } else if (
      text.toLowerCase().includes('plant') ||
      text.toLowerCase().includes('downtime')
    ) {
      return demoResponses.plant_downtime;
    } else {
      return `I understand you're asking about: "${text}"

I can help you analyze data across several domains:
- **F&I Performance**: Revenue, penetration rates, dealer comparisons
- **Logistics**: Shipment delays, carrier performance, route analysis
- **Manufacturing**: Plant downtime, production issues, root cause analysis
- **Marketing**: Campaign performance, open rates, revenue attribution

Try one of the demo questions to see detailed analysis with data visualizations.`;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearConversation = () => {
    setMessages([]);
    SessionManager.clearSession();
    setConversationId(SessionManager.getConversationId());
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div className="flex items-center">
          <SparklesIcon className="w-6 h-6 text-cox-blue-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">AI Analytics Assistant</h2>
          {/* Backend Status Indicator */}
          <div className="ml-3 flex items-center">
            {backendStatus === 'checking' && (
              <span className="flex items-center text-xs text-gray-400">
                <div className="w-2 h-2 bg-gray-400 rounded-full mr-1 animate-pulse" />
                Connecting...
              </span>
            )}
            {backendStatus === 'online' && (
              <span className="flex items-center text-xs text-green-600">
                <CheckCircleIcon className="w-4 h-4 mr-1" />
                Backend Online
              </span>
            )}
            {backendStatus === 'offline' && (
              <span className="flex items-center text-xs text-amber-600">
                <ExclamationCircleIcon className="w-4 h-4 mr-1" />
                Demo Mode
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSqlQuery(!showSqlQuery)}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              showSqlQuery ? 'bg-cox-blue-100 text-cox-blue-700' : 'text-gray-400 hover:bg-gray-100'
            )}
            title="Show SQL Queries"
          >
            <CodeBracketIcon className="w-5 h-5" />
          </button>
          {messages.length > 0 && (
            <button
              onClick={handleClearConversation}
              className="p-2 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors"
              title="Clear Conversation"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <SparklesIcon className="w-12 h-12 text-cox-blue-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Ask anything about your data
            </h3>
            <p className="text-gray-500 mb-6 max-w-md">
              I can analyze F&I revenue, logistics delays, plant downtime, and more.
              Try one of the demo questions below:
            </p>

            {/* Demo Scenario Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl">
              {scenariosLoading ? (
                // Loading skeletons
                Array.from({ length: 3 }).map((_, idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200 animate-pulse">
                    <div className="flex items-center mb-2">
                      <div className="w-5 h-5 bg-gray-300 rounded mr-2" />
                      <div className="h-4 bg-gray-300 rounded w-24" />
                    </div>
                    <div className="h-4 bg-gray-300 rounded w-full mb-2" />
                    <div className="h-4 bg-gray-300 rounded w-3/4 mb-2" />
                    <div className="h-6 bg-gray-300 rounded w-20" />
                  </div>
                ))
              ) : scenariosError ? (
                // Error state
                <div className="col-span-full text-center py-8">
                  <ExclamationCircleIcon className="w-8 h-8 text-red-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Failed to load demo scenarios</p>
                  <p className="text-xs text-gray-400">Using demo mode</p>
                </div>
              ) : (
                // Loaded scenarios
                demoScenarios.map((scenario) => (
                  <button
                    key={scenario.id}
                    onClick={() => handleScenarioClick(scenario)}
                    className="p-4 text-left bg-gray-50 rounded-lg border border-gray-200 hover:border-cox-blue-300 hover:bg-cox-blue-50 transition-colors"
                  >
                    <div className="flex items-center mb-2">
                      <ChartBarIcon className="w-5 h-5 text-cox-blue-600 mr-2" />
                      <span className="text-sm font-medium text-gray-900">
                        {scenario.title}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{scenario.question}</p>
                    <span className="inline-block mt-2 px-2 py-1 text-xs font-medium text-cox-blue-700 bg-cox-blue-100 rounded">
                      {scenario.category}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={clsx('flex', message.role === 'user' ? 'justify-end' : 'justify-start')}
              >
                <div
                  className={clsx('chat-message', message.role, {
                    'bg-cox-blue-100 text-cox-blue-900': message.role === 'user',
                    'bg-gray-100 text-gray-900': message.role === 'assistant',
                  })}
                >
                  {message.role === 'assistant' && (
                    <div className="flex items-center mb-2">
                      <SparklesIcon className="w-4 h-4 text-cox-blue-600 mr-2" />
                      <span className="text-sm font-medium text-cox-blue-700">AI Analytics</span>
                    </div>
                  )}
                  <div className="prose prose-sm max-w-none">
                    {message.content.split('\n').map((line, idx) => {
                      // Handle markdown-like formatting
                      if (line.startsWith('**') && line.endsWith('**')) {
                        return (
                          <h4 key={idx} className="font-bold text-gray-900 mt-4 mb-2">
                            {line.replace(/\*\*/g, '')}
                          </h4>
                        );
                      }
                      if (line.startsWith('| ')) {
                        // Table row
                        return (
                          <div key={idx} className="font-mono text-xs bg-gray-50 px-2 py-1 border-b border-gray-200">
                            {line}
                          </div>
                        );
                      }
                      if (line.startsWith('• ') || line.startsWith('- ')) {
                        return (
                          <li key={idx} className="ml-4 text-sm">
                            {line.replace(/^[•-]\s/, '')}
                          </li>
                        );
                      }
                      if (line.match(/^\d+\./)) {
                        return (
                          <li key={idx} className="ml-4 text-sm list-decimal">
                            {line.replace(/^\d+\.\s/, '')}
                          </li>
                        );
                      }
                      return (
                        <p key={idx} className="text-sm mb-1">
                          {line}
                        </p>
                      );
                    })}
                  </div>

                  {/* SQL Query Display */}
                  {showSqlQuery && message.sqlQuery && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center text-sm font-medium text-gray-700 mb-2">
                        <CodeBracketIcon className="w-4 h-4 mr-2 text-purple-500" />
                        Generated SQL Query
                      </div>
                      <pre className="bg-gray-800 text-green-400 text-xs p-3 rounded-lg overflow-x-auto">
                        <code>{message.sqlQuery}</code>
                      </pre>
                    </div>
                  )}

                  {/* Data Table Display */}
                  {message.data && message.data.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center text-sm font-medium text-gray-700 mb-2">
                        <TableCellsIcon className="w-4 h-4 mr-2 text-blue-500" />
                        Query Results ({message.data.length} rows)
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs">
                          <thead className="bg-gray-50">
                            <tr>
                              {Object.keys(message.data[0]).map((key) => (
                                <th key={key} className="px-2 py-1 text-left font-medium text-gray-600 border-b">
                                  {key}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {message.data.slice(0, 10).map((row, rowIdx) => (
                              <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                {Object.values(row).map((value, colIdx) => (
                                  <td key={colIdx} className="px-2 py-1 border-b border-gray-100">
                                    {String(value)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {message.data.length > 10 && (
                          <p className="text-xs text-gray-500 mt-2">Showing 10 of {message.data.length} rows</p>
                        )}
                      </div>
                    </div>
                  )}

                  {message.recommendations && message.recommendations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center text-sm font-medium text-gray-700 mb-2">
                        <LightBulbIcon className="w-4 h-4 mr-2 text-yellow-500" />
                        Quick Actions
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {message.recommendations.slice(0, 3).map((rec, idx) => (
                          <button
                            key={idx}
                            className="px-3 py-1 text-xs font-medium text-cox-blue-700 bg-cox-blue-50 rounded-full hover:bg-cox-blue-100"
                          >
                            {rec}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="chat-message bg-gray-100">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.1s' }}
                    />
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask anything about your data..."
              className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-cox-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className={clsx(
              'p-3 rounded-lg transition-colors',
              input.trim() && !isLoading
                ? 'bg-cox-blue-600 text-white hover:bg-cox-blue-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            )}
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-2">
          <p className="text-xs text-gray-400">
            Press Enter to send, Shift+Enter for new line
          </p>
          <div className="flex items-center space-x-4">
            <p className="text-xs text-gray-400">Powered by GPT-4</p>
            {process.env.NODE_ENV === 'development' && (
              <p className="text-xs text-gray-300 font-mono">
                ID: {conversationId?.slice(-8)}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
