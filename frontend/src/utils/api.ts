import type {
  Config,
  ProvidersResponse,
  ChatRequest,
  ChatResponse,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
} from '../types';

const API_BASE = window.location.origin;

export class ApiClient {
  private static getAuthToken(): string {
    const token = localStorage.getItem('ai_service_token');
    return token ? `Bearer ${token}` : '';
  }

  static async getConfig(): Promise<Config> {
    const response = await fetch(`${API_BASE}/api/config`);
    if (!response.ok) {
      throw new Error('Failed to load configuration');
    }
    return response.json();
  }

  static async verifyToken(token: string): Promise<User> {
    const config = await this.getConfig();
    const response = await fetch(`${config.securityServiceUrl}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Token verification failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async login(credentials: LoginRequest): Promise<AuthResponse> {
    const config = await this.getConfig();
    const response = await fetch(`${config.securityServiceUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || errorData.error || `Login failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async register(data: RegisterRequest): Promise<AuthResponse> {
    const config = await this.getConfig();
    const response = await fetch(`${config.securityServiceUrl}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Registration failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async logout(): Promise<void> {
    const token = localStorage.getItem('ai_service_token');
    if (!token) return;

    try {
      const config = await this.getConfig();
      await fetch(`${config.securityServiceUrl}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('ai_service_token');
    }
  }

  static async getProviders(): Promise<ProvidersResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${API_BASE}/api/v1/models`, {
      headers: {
        Authorization: token,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('ai_service_token');
        throw new Error('Authentication required. Please login.');
      }
      throw new Error(`Failed to load models: ${response.statusText}`);
    }

    return response.json();
  }

  static async sendChat(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token,
      },
      body: JSON.stringify(request),
      signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async sendStreamingChat(
    request: ChatRequest,
    onChunk: (content: string) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token,
      },
      body: JSON.stringify(request),
      signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Request failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Failed to get response stream');
    }

    const decoder = new TextDecoder();
    let fullText = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'chunk' && data.content) {
                fullText += data.content;
                onChunk(fullText);
              } else if (data.type === 'done') {
                return;
              } else if (data.type === 'error') {
                throw new Error(data.message || 'Streaming error');
              }
            } catch (e) {
              // Skip invalid JSON lines
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  static async checkSecurityServiceStatus(): Promise<{ connected: boolean; message: string }> {
    try {
      const config = await this.getConfig();
      const token = localStorage.getItem('ai_service_token');
      
      let testUrl: string;
      let useAuth = false;
      
      if (token) {
        testUrl = `${config.securityServiceUrl}/api/v1/auth/me`;
        useAuth = true;
      } else {
        testUrl = `${config.securityServiceUrl}/q/health`;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const headers: HeadersInit = {
        Accept: 'application/json',
      };

      if (useAuth && token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(testUrl, {
        method: 'GET',
        signal: controller.signal,
        headers,
      });

      clearTimeout(timeoutId);

      if (response.status >= 200 && response.status < 500) {
        return { connected: true, message: 'Connected ✓' };
      } else {
        return { connected: true, message: 'Connected (may need configuration)' };
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        return { connected: false, message: 'Timeout' };
      } else if (
        error.message.includes('Failed to fetch') ||
        error.message.includes('ERR_NAME_NOT_RESOLVED') ||
        error.message.includes('NetworkError')
      ) {
        return { connected: false, message: 'Disconnected' };
      } else {
        return { connected: true, message: 'Connected (endpoint may require auth)' };
      }
    }
  }
}

