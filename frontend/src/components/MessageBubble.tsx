import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faRobot, faLightbulb, faGauge } from '@fortawesome/free-solid-svg-icons';
import type { Message } from '../types/chat';
import { parseAIResponse } from '../utils/aiParser';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const parsed = message.role === 'assistant' ? parseAIResponse(message.content) : null;

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-6`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary-400 text-white' : 'bg-gray-200 text-gray-700'
        }`}
      >
        <FontAwesomeIcon icon={isUser ? faUser : faRobot} className="w-4 h-4" />
      </div>

      {/* Message Content */}
      <div className={`flex-1 ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
        {/* Thought Section (for AI with reasoning) */}
        {parsed?.thought && (
          <div className="w-full bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-2">
            <div className="flex items-center gap-2 mb-2">
              <FontAwesomeIcon icon={faLightbulb} className="text-yellow-600 w-4 h-4" />
              <span className="text-sm font-semibold text-yellow-800">Thought Process</span>
            </div>
            <p className="text-sm text-yellow-900 whitespace-pre-wrap">{parsed.thought}</p>
          </div>
        )}

        {/* Main Message */}
        <div
          className={`rounded-2xl px-4 py-3 max-w-[85%] ${
            isUser
              ? 'bg-primary-400 text-white'
              : 'bg-gray-100 text-gray-900 border border-gray-200'
          }`}
        >
          <p className="whitespace-pre-wrap break-words">{parsed?.content || message.content}</p>
        </div>

        {/* Metadata (Performance metrics, tokens, etc.) */}
        {(parsed?.metadata || message.metadata) && (
          <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
            {message.metadata?.model && (
              <span className="font-mono">{message.metadata.model}</span>
            )}
            {parsed?.metadata?.performance && (
              <>
                {parsed.metadata.performance.tokensPerSecond && (
                  <span className="flex items-center gap-1">
                    <FontAwesomeIcon icon={faGauge} className="w-3 h-3" />
                    {parsed.metadata.performance.tokensPerSecond.toFixed(2)} tok/sec
                  </span>
                )}
                {parsed.metadata.tokens && (
                  <span>{parsed.metadata.tokens} tokens</span>
                )}
                {parsed.metadata.performance.timeToFirstToken && (
                  <span>{parsed.metadata.performance.timeToFirstToken.toFixed(2)}s to first token</span>
                )}
                {parsed.metadata.performance.stopReason && (
                  <span>Stop: {parsed.metadata.performance.stopReason}</span>
                )}
              </>
            )}
            <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}

