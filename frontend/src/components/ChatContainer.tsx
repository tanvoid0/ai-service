import { useState, useEffect, useRef } from 'react';
import { ApiClient } from '../utils/api';
import type { Config, User, Provider, ChatRequest } from '../types';
import type { Conversation, Message } from '../types/chat';
import { ChatStore } from '../utils/chatStore';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faRobot,
  faSignOutAlt,
  faCircle,
  faPaperPlane,
  faStream,
  faSpinner,
} from '@fortawesome/free-solid-svg-icons';
import ChatSidebar from './ChatSidebar';
import MessageBubble from './MessageBubble';

interface ChatContainerProps {
  config: Config;
  user: User;
  onLogout: () => void;
}

export default function ChatContainer({ config, user, onLogout }: ChatContainerProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [models, setModels] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [loadingModels, setLoadingModels] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<{ connected: boolean; message: string } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    loadConversations();
    loadProviders();
    checkStatus();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = () => {
    const convs = ChatStore.getConversations();
    setConversations(convs);
    if (convs.length > 0 && !currentConversation) {
      setCurrentConversation(convs[0]);
    }
  };

  const checkStatus = async () => {
    const statusData = await ApiClient.checkSecurityServiceStatus();
    setStatus(statusData);
  };

  const loadProviders = async () => {
    try {
      setLoadingProviders(true);
      setError(null);
      const data = await ApiClient.getProviders();
      setProviders(data.providers);

      if (data.providers.length > 0) {
        const firstProvider = data.providers[0];
        setSelectedProvider(firstProvider.provider);
        setModels(firstProvider.models);
        if (firstProvider.default) {
          setSelectedModel(firstProvider.default);
        } else if (firstProvider.models.length > 0) {
          setSelectedModel(firstProvider.models[0]);
        }
      }
    } catch (err: any) {
      setError(err.message);
      if (err.message.includes('Authentication')) {
        onLogout();
      }
    } finally {
      setLoadingProviders(false);
    }
  };

  const handleProviderChange = (providerName: string) => {
    const provider = providers.find((p: Provider) => p.provider === providerName);
    if (provider) {
      setLoadingModels(true);
      setSelectedProvider(provider.provider);
      setModels(provider.models);
      if (provider.default) {
        setSelectedModel(provider.default);
      } else if (provider.models.length > 0) {
        setSelectedModel(provider.models[0]);
      }
      // Small delay to show loading state
      setTimeout(() => setLoadingModels(false), 100);
    }
  };

  const handleNewConversation = () => {
    const newConv = ChatStore.createConversation();
    setCurrentConversation(newConv);
    loadConversations();
  };

  const handleSelectConversation = (id: string) => {
    const conv = ChatStore.getConversation(id);
    if (conv) {
      setCurrentConversation(conv);
    }
  };

  const handleDeleteConversation = (id: string) => {
    ChatStore.deleteConversation(id);
    if (currentConversation?.id === id) {
      const remaining = ChatStore.getConversations();
      setCurrentConversation(remaining.length > 0 ? remaining[0] : null);
    }
    loadConversations();
  };

  const handleRenameConversation = (id: string, newTitle: string) => {
    ChatStore.updateConversation(id, { title: newTitle });
    if (currentConversation?.id === id) {
      setCurrentConversation({ ...currentConversation, title: newTitle });
    }
    loadConversations();
  };

  const sendMessage = async (stream: boolean) => {
    if (!input.trim()) return;
    if (!selectedProvider || !selectedModel) {
      setError('Please select a provider and model');
      return;
    }

    // Create conversation if none exists
    let conv = currentConversation;
    if (!conv) {
      conv = ChatStore.createConversation();
      setCurrentConversation(conv);
      loadConversations();
    }

    // Add user message
    const userMessage: Message = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
      metadata: {
        model: selectedModel,
        provider: selectedProvider,
      },
    };

    ChatStore.addMessage(conv.id, userMessage);
    setInput('');
    setError(null);

    // Create placeholder for AI response
    const aiMessageId = `msg_${Date.now()}_ai`;
    const aiMessage: Message = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      metadata: {
        model: selectedModel,
        provider: selectedProvider,
      },
    };

    ChatStore.addMessage(conv.id, aiMessage);
    loadConversations();

    // Update current conversation
    let updatedConv = ChatStore.getConversation(conv.id);
    if (updatedConv) {
      setCurrentConversation(updatedConv);
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setLoading(true);

    // Build conversation history from previous messages
    // Re-fetch to ensure we have the latest state
    updatedConv = ChatStore.getConversation(conv.id);
    const conversationMessages = updatedConv?.messages || [];
    
    // Convert to API format (exclude the placeholder AI message we just added)
    const messages = conversationMessages
      .filter((msg) => msg.id !== aiMessageId) // Exclude the placeholder
      .map((msg) => ({
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
      }));

    const request: ChatRequest = {
      messages: messages,
      provider: selectedProvider,
      model: selectedModel,
      max_context_messages: 20, // Limit to last 20 messages for context
    };

    try {
      if (stream) {
        await ApiClient.sendStreamingChat(
          request,
          (content) => {
            // Update message in real-time
            const updatedConv = ChatStore.getConversation(conv!.id);
            if (updatedConv) {
              const msgIndex = updatedConv.messages.findIndex((m) => m.id === aiMessageId);
              if (msgIndex !== -1) {
                updatedConv.messages[msgIndex].content = content;
                ChatStore.updateConversation(conv!.id, { messages: updatedConv.messages });
                setCurrentConversation({ ...updatedConv });
              }
            }
          },
          abortControllerRef.current.signal
        );
      } else {
        const data = await ApiClient.sendChat(request, abortControllerRef.current.signal);
        const updatedConv = ChatStore.getConversation(conv.id);
        if (updatedConv) {
          const msgIndex = updatedConv.messages.findIndex((m) => m.id === aiMessageId);
          if (msgIndex !== -1) {
            updatedConv.messages[msgIndex].content = data.response || 'No response received';
            ChatStore.updateConversation(conv.id, { messages: updatedConv.messages });
            setCurrentConversation({ ...updatedConv });
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        if (err.message.includes('401') || err.message.includes('Authentication')) {
          onLogout();
        }
        setError(err.message);
        // Update error message
        const updatedConv = ChatStore.getConversation(conv.id);
        if (updatedConv) {
          const msgIndex = updatedConv.messages.findIndex((m) => m.id === aiMessageId);
          if (msgIndex !== -1) {
            updatedConv.messages[msgIndex].content = `Error: ${err.message}`;
            ChatStore.updateConversation(conv.id, { messages: updatedConv.messages });
            setCurrentConversation({ ...updatedConv });
          }
        }
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
      loadConversations();
    }
  };

  const handleLogout = async () => {
    await ApiClient.logout();
    onLogout();
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <ChatSidebar
        conversations={conversations}
        currentConversationId={currentConversation?.id || null}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onRenameConversation={handleRenameConversation}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
              <FontAwesomeIcon icon={faRobot} className="text-primary-400" />
              AI Service Chat
              <span className="text-sm font-normal bg-gray-100 px-2 py-1 rounded font-mono text-gray-600">
                v{config.version || '2.2.0'}
              </span>
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Model Selector */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <select
                  value={selectedProvider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-primary-400 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={loadingProviders}
                >
                  <option value="">{loadingProviders ? 'Loading providers...' : 'Provider'}</option>
                  {providers.map((provider) => (
                    <option key={provider.provider} value={provider.provider}>
                      {provider.provider} ({provider.models.length})
                    </option>
                  ))}
                </select>
                {loadingProviders && (
                  <div className="absolute right-8 top-1/2 -translate-y-1/2 pointer-events-none">
                    <FontAwesomeIcon icon={faSpinner} className="animate-spin text-gray-400 text-xs" />
                  </div>
                )}
              </div>
              <div className="relative">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-primary-400 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={!selectedProvider || loadingProviders || loadingModels}
                >
                  <option value="">
                    {loadingProviders || loadingModels
                      ? 'Loading models...'
                      : !selectedProvider
                      ? 'Select provider first'
                      : 'Model'}
                  </option>
                  {models.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
                {(loadingProviders || loadingModels) && (
                  <div className="absolute right-8 top-1/2 -translate-y-1/2 pointer-events-none">
                    <FontAwesomeIcon icon={faSpinner} className="animate-spin text-gray-400 text-xs" />
                  </div>
                )}
              </div>
            </div>

            {/* Status & Settings */}
            <button
              onClick={checkStatus}
              className="px-3 py-2 text-sm flex items-center gap-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Check Security Service Connection"
            >
              <FontAwesomeIcon
                icon={faCircle}
                className={`w-2 h-2 ${
                  status?.connected ? 'text-green-500' : status ? 'text-red-500' : 'text-gray-400'
                }`}
              />
              <span className="text-gray-600">{status?.message || 'Check Status'}</span>
            </button>

            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="font-medium">{user.username}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-2 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2"
              >
                <FontAwesomeIcon icon={faSignOutAlt} />
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {currentConversation ? (
            <div className="max-w-4xl mx-auto">
              {currentConversation.messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-20">
                  <FontAwesomeIcon icon={faRobot} className="text-6xl mb-4 text-gray-300" />
                  <p className="text-xl mb-2">Start a conversation</p>
                  <p className="text-sm">Send a message to begin chatting with the AI</p>
                </div>
              ) : (
                currentConversation.messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))
              )}
              {loading && (
                <div className="flex gap-4 mb-6">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center">
                    <FontAwesomeIcon icon={faRobot} className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="bg-gray-100 rounded-2xl px-4 py-3 inline-block">
                      <FontAwesomeIcon icon={faSpinner} className="animate-spin text-gray-400" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          ) : (
            <div className="text-center text-gray-500 mt-20">
              <FontAwesomeIcon icon={faRobot} className="text-6xl mb-4 text-gray-300" />
              <p className="text-xl mb-2">No conversation selected</p>
              <p className="text-sm">Create a new chat to get started</p>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(false);
                  }
                }}
                placeholder="Send a message..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-primary-400 resize-none"
                rows={1}
                disabled={loading}
              />
              <div className="flex gap-2">
                <button
                  onClick={() => sendMessage(false)}
                  disabled={loading || !input.trim()}
                  className="px-4 py-3 bg-primary-400 hover:bg-primary-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  title="Send (Non-Streaming)"
                >
                  <FontAwesomeIcon icon={faPaperPlane} />
                </button>
                <button
                  onClick={() => sendMessage(true)}
                  disabled={loading || !input.trim()}
                  className="px-4 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  title="Send (Streaming)"
                >
                  <FontAwesomeIcon icon={faStream} />
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
