/**
 * useStreamParser - Incremental JSON Parsing Composable
 *
 * Adapted from agent-ui's useAIResponseStream hook.
 * Handles parsing of streaming JSON chunks using brace-counting algorithm.
 *
 * This composable provides utilities to:
 * 1. Parse incomplete JSON objects from streaming buffer
 * 2. Handle both legacy and new AgentOS event formats
 * 3. Extract complete JSON objects incrementally
 */

import type { RunResponseContent, NewFormatData } from '@/types/chat'

/**
 * Detects if the incoming data is in the legacy format (direct RunResponseContent)
 * @param data - The parsed data object
 * @returns true if it's in the legacy format, false if it's in the new format
 */
function isLegacyFormat(data: unknown): data is RunResponseContent {
  return (
    typeof data === 'object' &&
    data !== null &&
    'event' in data &&
    !('data' in data) &&
    typeof (data as RunResponseContent).event === 'string'
  )
}

type LegacyEventFormat = RunResponseContent & { event: string }

/**
 * Converts new format (event + data) to legacy format (flat structure)
 * @param newFormatData - New format data object
 * @returns Legacy format event object
 */
function convertNewFormatToLegacy(
  newFormatData: NewFormatData
): LegacyEventFormat {
  const { event, data } = newFormatData

  // Parse the data field if it's a string
  let parsedData: Record<string, unknown>
  if (typeof data === 'string') {
    try {
      // First try to parse as JSON
      parsedData = JSON.parse(data)
    } catch {
      parsedData = {}
    }
  } else {
    parsedData = data
  }

  const { ...cleanData } = parsedData

  // Convert to legacy format by flattening the structure
  return {
    event: event,
    ...cleanData
  } as LegacyEventFormat
}

/**
 * Processes a single JSON chunk by passing it to the provided callback.
 * @param chunk - A parsed JSON object of type RunResponseContent.
 * @param onChunk - Callback to handle the chunk.
 */
function processChunk(
  chunk: RunResponseContent,
  onChunk: (chunk: RunResponseContent) => void
) {
  onChunk(chunk)
}

/**
 * Extracts complete JSON objects from a buffer string **incrementally**.
 * - It allows partial JSON objects to accumulate across chunks.
 * - It ensures real-time streaming updates.
 *
 * This function uses a brace-counting algorithm to find complete JSON objects
 * in the streaming buffer without requiring the entire object at once.
 *
 * @param buffer - The accumulated string buffer
 * @param onChunk - Callback to process each parsed JSON object
 * @returns Remaining string that did not form a complete JSON object
 */
export function parseBuffer(
  buffer: string,
  onChunk: (chunk: RunResponseContent) => void
): string {
  let currentIndex = 0
  let jsonStartIndex = buffer.indexOf('{', currentIndex)

  // Process as many complete JSON objects as possible.
  while (jsonStartIndex !== -1 && jsonStartIndex < buffer.length) {
    let braceCount = 0
    let inString = false
    let escapeNext = false
    let jsonEndIndex = -1
    let i = jsonStartIndex

    // Walk through the string to find the matching closing brace.
    for (; i < buffer.length; i++) {
      const char = buffer[i]

      if (inString) {
        if (escapeNext) {
          escapeNext = false
        } else if (char === '\\') {
          escapeNext = true
        } else if (char === '"') {
          inString = false
        }
      } else {
        if (char === '"') {
          inString = true
        } else if (char === '{') {
          braceCount++
        } else if (char === '}') {
          braceCount--
          if (braceCount === 0) {
            jsonEndIndex = i
            break
          }
        }
      }
    }

    // If we found a complete JSON object, try to parse it.
    if (jsonEndIndex !== -1) {
      const jsonString = buffer.slice(jsonStartIndex, jsonEndIndex + 1)

      try {
        const parsed = JSON.parse(jsonString)

        // Check if it's in the legacy format - use as is
        if (isLegacyFormat(parsed)) {
          processChunk(parsed, onChunk)
        } else {
          // New format - convert to legacy format for compatibility
          const legacyChunk = convertNewFormatToLegacy(parsed as NewFormatData)
          processChunk(legacyChunk, onChunk)
        }
      } catch {
        // Move past the starting brace to avoid re-parsing the same invalid JSON.
        jsonStartIndex = buffer.indexOf('{', jsonStartIndex + 1)
        continue
      }

      // Move currentIndex past the parsed JSON and trim any leading whitespace.
      currentIndex = jsonEndIndex + 1
      buffer = buffer.slice(currentIndex).trim()

      // Reset currentIndex and search for the next JSON object.
      currentIndex = 0
      jsonStartIndex = buffer.indexOf('{', currentIndex)
    } else {
      // No complete JSON found, break and return remaining buffer
      break
    }
  }

  // Return any remaining unparsed buffer
  return buffer
}

/**
 * Composable for stream parsing utilities
 *
 * Usage:
 * ```typescript
 * const { parseStreamChunk } = useStreamParser()
 *
 * let buffer = ''
 * for await (const chunk of readableStream) {
 *   const text = decoder.decode(chunk)
 *   buffer += text
 *   buffer = parseStreamChunk(buffer, (parsedChunk) => {
 *     console.log('Received chunk:', parsedChunk)
 *   })
 * }
 * ```
 */
export function useStreamParser() {
  /**
   * Parse streaming buffer and extract complete JSON objects
   * @param buffer - Current buffer string
   * @param onChunk - Callback for each parsed chunk
   * @returns Remaining unparsed buffer
   */
  const parseStreamChunk = (
    buffer: string,
    onChunk: (chunk: RunResponseContent) => void
  ): string => {
    return parseBuffer(buffer, onChunk)
  }

  return {
    parseStreamChunk
  }
}
