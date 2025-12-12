'use client';

import { useState, useRef, useEffect } from 'react';
import {
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  PaperAirplaneIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { sendChatMessage, ChatResponse } from '@/lib/api';
import { SessionManager } from '@/utils/sessionManager';
import { parseMessageContent } from '@/utils/messageParser';

interface FloatingChatBotProps {
  pageContext?: {
    page: string;
    charts?: Array<{
      id: string;
      title: string;
      type: 'bar' | 'pie' | 'line' | 'area';
      data?: any;
    }>;
    alerts?: {
      total: number;
      critical: number;
      warning: number;
      info: number;
      criticalAlerts?: Array<{
        metric: string;
        message: string;
        change: number;
        rootCause: string;
        category: string;
      }>;
      warningAlerts?: Array<{
        metric: string;
        message: string;
        change: number;
        rootCause: string;
        category: string;
      }>;
      byCategory?: Array<{
        category: string;
        count: number;
        alerts: Array<{
          metric: string;
          severity: string;
          message: string;
        }>;
      }>;
      allAlerts?: Array<{
        id: string;
        metric: string;
        severity: string;
        message: string;
        change: number;
        rootCause: string;
        category: string;
        currentValue: number;
        previousValue: number;
      }>;
    };
    catalog?: {
      totalTables: number;
      regions: string[];
      kpiCategories: string[];
      tables: Array<{
        name: string;
        description: string;
        rowCount: string;
        columnCount: number;
        columns: Array<{
          name: string;
          type: string;
          description: string;
        }>;
        category: string;
      }>;
      tablesByCategory?: Array<{
        category: string;
        count: number;
        tables: Array<{
          name: string;
          description: string;
          rowCount: string;
          columnCount: number;
          columns: string[];
        }>;
      }>;
      selectedTable?: {
        name: string;
        description: string;
        rowCount: string;
        columns: Array<{
          name: string;
          type: string;
          description: string;
        }>;
        category: string;
        sampleQuery: string;
      } | null;
    };
    ros?: {
      total: number;
      byStatus?: Array<{
        status: string;
        count: number;
        ros: Array<{
          id: string;
          customer: string;
          status: string;
          promised: string;
          processTime: string;
        }>;
      }>;
    };
    schedule?: {
      date: string;
      totalAppointments: number;
      byStatus?: {
        notArrived: number;
        inProgress: number;
        completed: number;
      };
      appointments?: Array<{
        time: string;
        vehicle: string;
        customer: string;
        advisor: string;
        status: string;
        roNumber?: string;
      }>;
      needsAction?: number;
    };
    logistics?: {
      overallStats?: {
        total_shipments: number;
        delayed_shipments: number;
        delay_rate: number;
      };
      carrierCount?: number;
      routeCount?: number;
      topCarrier?: string;
      topDelayReason?: string;
    };
  };
  onChartUpdate?: (chartId: string, updates: { type?: string; data?: any }) => void;
}

export default function FloatingChatBot({ pageContext, onChartUpdate }: FloatingChatBotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // Build context-aware query
      let query = userMessage;
      
      // Add page context if available
      if (pageContext) {
        const contextInfo = `Current page: ${pageContext.page}. `;
        
        // Add Schedule/Engage context if available - minimal context, tools handle the rest
        if (pageContext.schedule) {
          query = `${contextInfo}User is on the Engage/Customer Experience Management page. User query: ${userMessage}. 

**Available Tools:**
- **get_service_appointments**: Get appointment data with customer info, loyalty tiers, service history
- **get_customer_info**: Look up customer details, loyalty tiers, preferences
- **get_appointment_statistics**: Get appointment counts and summaries

Use these tools to answer questions about appointments, customers, check-ins, and service schedules.`;
        }
        // Add ROS/Inspect context if available - minimal context, tools handle the rest
        else if (pageContext.ros) {
          query = `${contextInfo}User is on the Inspect/Repair Orders page. User query: ${userMessage}. 

**Available Tools:**
- **generate_sql_query**: Query repair order data from the database
- Use this tool to answer questions about repair orders, their status, customers, technicians, process times, and RO workflow.`;
        }
        // Add catalog context if available - minimal context, let tools handle the rest
        else if (pageContext.catalog) {
          // Only pass minimal context - the orchestrator has tools to handle queries intelligently
          query = `${contextInfo}User is on the Data Catalog page. User query: ${userMessage}. 

**Context:**
- Page: Data Catalog
- The user can ask about tables, schemas, or query data from tables

**Available Tools:**
- **generate_sql_query**: Use this for data queries. It automatically:
  * Understands table name variations (fniTransactions → fni_transactions)
  * Accesses the database schema dynamically
  * Generates correct SQLite-compatible SQL
  * Executes the query and returns data
- **search_data_catalog**: Use this for finding tables and schema information

**For queries like "find first 3 transactions in fniTransactions":**
- Simply use generate_sql_query with the user's natural language query
- The tool will handle table name mapping, schema lookup, and SQL generation automatically

The tools handle all the complexity - you just need to route to the right tool based on the user's intent.`;
        }
        // Add alerts context if available - minimal context, tools handle the rest
        else if (pageContext.alerts) {
          query = `${contextInfo}User is on the KPI Alerts page. User query: ${userMessage}. 

**Available Tools:**
- **generate_sql_query**: Query alert data and KPI metrics from the database
- **analyze_kpi_data**: Analyze KPI data to understand root causes
- Use these tools to answer questions about why alerts happened, root causes, affected metrics, and provide recommendations.`;
        }
        // Add logistics context if available - minimal context, tools handle the rest
        else if (pageContext.logistics) {
          query = `${contextInfo}User is on the Logistics Analysis page. User query: ${userMessage}. 

**Available Tools:**
- **generate_sql_query**: Query logistics and shipment data from the database
- **analyze_logistics_delays**: Analyze logistics delays, carrier performance, and route issues
- Use these tools to answer questions about shipment delays, carrier performance, route analysis, dwell times, and delay attribution.`;
        }
        // Add charts context if available
        else if (pageContext.charts && pageContext.charts.length > 0) {
          const chartsInfo = JSON.stringify(pageContext.charts.map(c => ({
            id: c.id,
            title: c.title,
            type: c.type
          })));
          query = `${contextInfo}Available charts: ${chartsInfo}. User query: ${userMessage}. If the user wants to change a chart type, use analyze_chart_change_request tool with the current charts info and return JSON with intent, chart_id, and new_chart_type fields.`;
        } else {
          query = `${contextInfo}${userMessage}`;
        }
      }

      const conversationId = SessionManager.getConversationId();
      const response: ChatResponse = await sendChatMessage(query, conversationId);

      if (response.conversation_id) {
        SessionManager.refreshSession();
      }

      const assistantContent = parseMessageContent(response.message);
      
      // Try to extract JSON from response if it contains structured data
      try {
        // Look for JSON in the response
        const jsonMatch = assistantContent.match(/\{[\s\S]*"intent"[\s\S]*\}/);
        if (jsonMatch) {
          const chartAnalysis = JSON.parse(jsonMatch[0]);
          
          if (chartAnalysis.intent === 'change_chart_type' && chartAnalysis.new_chart_type && onChartUpdate) {
            const chartId = chartAnalysis.chart_id || pageContext?.charts?.[0]?.id;
            const newType = chartAnalysis.new_chart_type.toLowerCase();
            
            if (chartId && ['bar', 'pie', 'line', 'area'].includes(newType)) {
              onChartUpdate(chartId, { type: newType });
              // Update the message to show confirmation
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: 'assistant',
                  content: chartAnalysis.message || `Changed chart to ${newType} chart.`
                };
                return updated;
              });
              return; // Don't add duplicate message
            }
          }
        }
      } catch (e) {
        // Not JSON, continue with normal parsing
      }
      
      // Fallback: Check if response contains chart update instructions in natural language
      const chartUpdateMatch = assistantContent.match(/change.*chart.*to\s+(\w+)/i);
      if (chartUpdateMatch && onChartUpdate && pageContext?.charts) {
        const newType = chartUpdateMatch[1].toLowerCase();
        const chartId = pageContext.charts[0]?.id; // Default to first chart
        if (['bar', 'pie', 'line', 'area'].includes(newType)) {
          onChartUpdate(chartId, { type: newType });
        }
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: assistantContent }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        { 
          role: 'assistant', 
          content: 'Sorry, I encountered an error. Please try again.' 
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-cox-blue-600 hover:bg-cox-blue-700 text-white rounded-full p-4 shadow-lg transition-all hover:scale-110"
          aria-label="Open chat bot"
        >
          <ChatBubbleLeftRightIcon className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col border border-gray-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-cox-blue-600 to-cox-blue-800 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-white/20 rounded flex items-center justify-center">
                <span className="text-white text-xs font-bold">CA</span>
              </div>
              <h3 className="font-semibold">Cox Automotive AI</h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-white/20 rounded p-1 transition-colors"
              aria-label="Close chat"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 text-sm py-8">
                <SparklesIcon className="w-8 h-8 mx-auto mb-2 text-cox-blue-500 opacity-50" />
                <p>Ask me anything about this dashboard!</p>
                <p className="text-xs mt-2">Try: "Change the bar chart to a pie chart"</p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={clsx(
                  'flex',
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={clsx(
                    'max-w-[80%] rounded-lg px-3 py-2 text-sm',
                    msg.role === 'user'
                      ? 'bg-cox-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  )}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-3 py-2 text-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about charts or data..."
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="bg-cox-blue-600 hover:bg-cox-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 transition-colors"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

