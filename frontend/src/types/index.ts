export interface User {
  username: string;
  email: string;
}

export interface Config {
  securityServiceUrl: string;
  applicationId: string;
  version?: string;
}

export interface Provider {
  provider: string;
  models: string[];
  default?: string;
}

export interface ProvidersResponse {
  providers: Provider[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  prompt?: string; // Legacy format, for backward compatibility
  messages?: ChatMessage[]; // New format with conversation history
  provider: string;
  model: string;
  max_context_messages?: number; // Optional: limit context window (default: 20)
}

export interface ChatResponse {
  response: string;
}

export interface StreamingChunk {
  type: 'chunk' | 'done' | 'error';
  content?: string;
  message?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  client_id: string;
  auth_mode: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string | null;
  last_name?: string | null;
}

export interface AuthResponse {
  token: string;
  username?: string;
}

