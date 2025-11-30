import { useState, useEffect } from 'react';
import { ApiClient } from './utils/api';
import type { User, Config } from './types';
import AuthContainer from './components/AuthContainer';
import ChatContainer from './components/ChatContainer';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initialize = async () => {
      try {
        const configData = await ApiClient.getConfig();
        setConfig(configData);

        const token = localStorage.getItem('ai_service_token');
        if (token) {
          try {
            const userData = await ApiClient.verifyToken(token);
            setUser(userData);
          } catch (error) {
            console.error('Token verification failed:', error);
            localStorage.removeItem('ai_service_token');
          }
        }
      } catch (error) {
        console.error('Initialization error:', error);
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, []);

  const handleLogin = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = async () => {
    await ApiClient.logout();
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <FontAwesomeIcon icon={faSpinner} className="w-8 h-8 text-primary-400 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <AuthContainer config={config!} onLogin={handleLogin} />;
  }

  return <ChatContainer config={config!} user={user} onLogout={handleLogout} />;
}

export default App;

