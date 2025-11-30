/**
 * Parses AI responses to extract structured information like thoughts, reasoning, etc.
 */
export interface ParsedAIResponse {
  content: string;
  thought?: string;
  metadata?: {
    tokens?: number;
    performance?: {
      tokensPerSecond?: number;
      timeToFirstToken?: number;
      stopReason?: string;
    };
  };
}

/**
 * Attempts to parse AI response for structured content like DeepSeek's thought process
 */
export function parseAIResponse(response: string): ParsedAIResponse {
  const result: ParsedAIResponse = { content: response };

  // Try to detect DeepSeek-style thought blocks
  // Pattern: "Thought for X seconds" followed by reasoning, then the actual response
  const thoughtPattern = /(?:Thought\s+for\s+[\d.]+\s+seconds?[:\n]?)(.*?)(?=\n\n|\n[A-Z]|$)/is;
  const thoughtMatch = response.match(thoughtPattern);

  if (thoughtMatch) {
    result.thought = thoughtMatch[1].trim();
    // Remove thought from main content
    result.content = response.replace(thoughtPattern, '').trim();
  }

  // Try to detect performance metrics at the end
  // Pattern: "X.XX tok/sec • X tokens • X.XXs to first token • Stop reason: ..."
  const perfPattern = /([\d.]+)\s+tok\/sec\s+•\s+(\d+)\s+tokens\s+•\s+([\d.]+)s\s+to\s+first\s+token\s+•\s+Stop\s+reason:\s+(.+)/i;
  const perfMatch = response.match(perfPattern);

  if (perfMatch) {
    result.metadata = {
      tokens: parseInt(perfMatch[2]),
      performance: {
        tokensPerSecond: parseFloat(perfMatch[1]),
        timeToFirstToken: parseFloat(perfMatch[3]),
        stopReason: perfMatch[4].trim(),
      },
    };
    // Remove performance metrics from content
    result.content = result.content.replace(perfPattern, '').trim();
  }

  // If no structured parsing worked, return original response
  if (!result.thought && !result.metadata) {
    result.content = response;
  }

  return result;
}

