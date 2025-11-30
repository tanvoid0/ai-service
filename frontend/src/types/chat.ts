export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    thought?: string;
    model?: string;
    provider?: string;
    tokens?: number;
    performance?: {
      tokensPerSecond?: number;
      timeToFirstToken?: number;
      stopReason?: string;
    };
  };
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  folderId?: string;
}

export interface ChatFolder {
  id: string;
  name: string;
  conversations: Conversation[];
}

