import { useState } from 'react';
import { ApiClient } from '../utils/api';
import type { Config, User, LoginRequest, RegisterRequest } from '../types';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faRobot,
  faUser,
  faEnvelope,
  faLock,
  faSpinner,
  faCircle,
} from '@fortawesome/free-solid-svg-icons';

interface AuthContainerProps {
  config: Config;
  onLogin: (user: User) => void;
}

export default function AuthContainer({ config, onLogin }: AuthContainerProps) {
  const [activeTab, setActiveTab] = useState<'register' | 'login'>('register');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [status, setStatus] = useState<{ connected: boolean; message: string } | null>(null);

  // Form state
  const [registerForm, setRegisterForm] = useState<RegisterRequest>({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });

  const [loginForm, setLoginForm] = useState<LoginRequest>({
    username: '',
    password: '',
    client_id: config.applicationId,
    auth_mode: 'jwt',
  });

  const checkStatus = async () => {
    const statusData = await ApiClient.checkSecurityServiceStatus();
    setStatus(statusData);
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const data = await ApiClient.register(registerForm);
      setSuccess(`Registration successful! Welcome ${data.username || registerForm.username}`);
      setRegisterForm({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
      });
      setTimeout(() => setActiveTab('login'), 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const data = await ApiClient.login(loginForm);
      if (!data.token) {
        throw new Error('No token received');
      }

      localStorage.setItem('ai_service_token', data.token);
      const user = await ApiClient.verifyToken(data.token);
      setSuccess('Login successful!');
      onLogin(user);
    } catch (err: any) {
      setError(err.message || 'Login failed');
      localStorage.removeItem('ai_service_token');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-10 relative">
      <button
        onClick={checkStatus}
        className="absolute top-5 right-5 px-4 py-2 bg-primary-400/10 border border-primary-400/30 text-primary-400 rounded-lg text-sm flex items-center gap-2 hover:bg-primary-400/20 transition-colors"
        title="Check Security Service Connection"
      >
        <FontAwesomeIcon
          icon={faCircle}
          className={`w-2 h-2 ${
            status?.connected ? 'text-green-500' : status ? 'text-red-500' : 'text-gray-400'
          }`}
        />
        <span>{status?.message || 'Check Status'}</span>
      </button>

      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center justify-center gap-3 flex-wrap">
          <FontAwesomeIcon icon={faRobot} className="text-4xl" />
          AI Service Chat
          <span className="text-sm font-normal bg-gray-100 px-3 py-1 rounded-lg font-mono text-gray-600">
            v{config.version || '2.2.0'}
          </span>
        </h1>
        <p className="text-gray-600 text-sm">Interact with multiple AI providers and models</p>
      </div>

      {(error || success) && (
        <div
          className={`mb-6 p-4 rounded-lg ${
            error ? 'bg-red-50 border border-red-200 text-red-700' : 'bg-green-50 border border-green-200 text-green-700'
          }`}
        >
          {error || success}
        </div>
      )}

      <div className="flex gap-2 mb-6 border-b-2 border-gray-200">
        <button
          onClick={() => {
            setActiveTab('register');
            setError(null);
            setSuccess(null);
          }}
          className={`px-5 py-3 font-medium transition-colors border-b-2 -mb-0.5 ${
            activeTab === 'register'
              ? 'text-primary-400 border-primary-400'
              : 'text-gray-600 border-transparent hover:text-gray-800'
          }`}
        >
          Register
        </button>
        <button
          onClick={() => {
            setActiveTab('login');
            setError(null);
            setSuccess(null);
          }}
          className={`px-5 py-3 font-medium transition-colors border-b-2 -mb-0.5 ${
            activeTab === 'login'
              ? 'text-primary-400 border-primary-400'
              : 'text-gray-600 border-transparent hover:text-gray-800'
          }`}
        >
          Login
        </button>
      </div>

      {activeTab === 'register' ? (
        <form onSubmit={handleRegister} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username *
            </label>
            <div className="relative">
              <FontAwesomeIcon
                icon={faUser}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <input
                type="text"
                required
                minLength={3}
                maxLength={50}
                value={registerForm.username}
                onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
                placeholder="Enter username"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
            <div className="relative">
              <FontAwesomeIcon
                icon={faEnvelope}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <input
                type="email"
                required
                value={registerForm.email}
                onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
                placeholder="Enter email"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password *</label>
            <div className="relative">
              <FontAwesomeIcon
                icon={faLock}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <input
                type="password"
                required
                minLength={8}
                value={registerForm.password}
                onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
                placeholder="Enter password"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
            <input
              type="text"
              value={registerForm.first_name || ''}
              onChange={(e) => setRegisterForm({ ...registerForm, first_name: e.target.value })}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
              placeholder="Enter first name (optional)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
            <input
              type="text"
              value={registerForm.last_name || ''}
              onChange={(e) => setRegisterForm({ ...registerForm, last_name: e.target.value })}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
              placeholder="Enter last name (optional)"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-primary-400 to-primary-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                Registering...
              </span>
            ) : (
              'Register'
            )}
          </button>
        </form>
      ) : (
        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username *</label>
            <div className="relative">
              <FontAwesomeIcon
                icon={faUser}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <input
                type="text"
                required
                value={loginForm.username}
                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
                placeholder="Enter username"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password *</label>
            <div className="relative">
              <FontAwesomeIcon
                icon={faLock}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <input
                type="password"
                required
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
                placeholder="Enter password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-primary-400 to-primary-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                Logging in...
              </span>
            ) : (
              'Login'
            )}
          </button>
        </form>
      )}
    </div>
  );
}

