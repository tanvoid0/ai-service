import type { Conversation, ChatFolder, Message } from '../types/chat';

const STORAGE_KEY = 'ai_service_chats';

export class ChatStore {
  private static getStorage(): { folders: ChatFolder[]; conversations: Conversation[] } {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const data = JSON.parse(stored);
        // Convert date strings back to Date objects
        data.conversations = data.conversations.map((conv: any) => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt),
          messages: conv.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
        }));
        return data;
      } catch (e) {
        console.error('Failed to parse chat storage:', e);
      }
    }
    return { folders: [], conversations: [] };
  }

  private static saveStorage(data: { folders: ChatFolder[]; conversations: Conversation[] }) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  static getConversations(): Conversation[] {
    const { conversations } = this.getStorage();
    return conversations.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  }

  static getConversation(id: string): Conversation | null {
    const conversations = this.getConversations();
    return conversations.find((c) => c.id === id) || null;
  }

  static createConversation(title?: string): Conversation {
    const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const conversation: Conversation = {
      id,
      title: title || 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const storage = this.getStorage();
    storage.conversations.push(conversation);
    this.saveStorage(storage);

    return conversation;
  }

  static updateConversation(id: string, updates: Partial<Conversation>) {
    const storage = this.getStorage();
    const index = storage.conversations.findIndex((c) => c.id === id);
    if (index !== -1) {
      storage.conversations[index] = {
        ...storage.conversations[index],
        ...updates,
        updatedAt: new Date(),
      };
      this.saveStorage(storage);
    }
  }

  static addMessage(conversationId: string, message: Message) {
    const storage = this.getStorage();
    const convIndex = storage.conversations.findIndex((c) => c.id === conversationId);
    if (convIndex !== -1) {
      storage.conversations[convIndex].messages.push(message);
      storage.conversations[convIndex].updatedAt = new Date();
      
      // Auto-generate title from first user message if still default
      if (storage.conversations[convIndex].title === 'New Chat' && message.role === 'user') {
        const title = message.content.substring(0, 50).trim();
        if (title) {
          storage.conversations[convIndex].title = title;
        }
      }
      
      this.saveStorage(storage);
    }
  }

  static deleteConversation(id: string) {
    const storage = this.getStorage();
    storage.conversations = storage.conversations.filter((c) => c.id !== id);
    this.saveStorage(storage);
  }

  static getFolders(): ChatFolder[] {
    const { folders } = this.getStorage();
    return folders;
  }

  static createFolder(name: string): ChatFolder {
    const id = `folder_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const folder: ChatFolder = {
      id,
      name,
      conversations: [],
    };

    const storage = this.getStorage();
    storage.folders.push(folder);
    this.saveStorage(storage);

    return folder;
  }

  static moveConversationToFolder(conversationId: string, folderId: string | null) {
    const storage = this.getStorage();
    const conv = storage.conversations.find((c) => c.id === conversationId);
    if (conv) {
      // Remove from old folder
      storage.folders.forEach((folder) => {
        folder.conversations = folder.conversations.filter((c) => c.id !== conversationId);
      });

      // Add to new folder
      if (folderId) {
        const folder = storage.folders.find((f) => f.id === folderId);
        if (folder) {
          folder.conversations.push(conv);
        }
      }

      conv.folderId = folderId || undefined;
      this.saveStorage(storage);
    }
  }
}

