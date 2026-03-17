'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketClient } from '@/lib/ws';
import { getToken } from '@/lib/auth';
import type { WebSocketMessage } from '@/types/message';

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  send: (message: WebSocketMessage) => void;
  connect: () => void;
  disconnect: () => void;
  readyState: number;
}

export function useWebSocket(path: string, autoConnect = false): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CLOSED);
  const clientRef = useRef<WebSocketClient | null>(null);

  const connect = useCallback(() => {
    if (clientRef.current?.isConnected) return;

    const token = getToken();
    const client = new WebSocketClient(path, token || undefined);

    client.onOpen(() => {
      setIsConnected(true);
      setReadyState(WebSocket.OPEN);
    });

    client.onMessage((message) => {
      setLastMessage(message);
    });

    client.onClose(() => {
      setIsConnected(false);
      setReadyState(WebSocket.CLOSED);
    });

    client.onError(() => {
      setReadyState(WebSocket.CLOSED);
    });

    client.connect();
    clientRef.current = client;
  }, [path]);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current = null;
    setIsConnected(false);
    setReadyState(WebSocket.CLOSED);
  }, []);

  const send = useCallback((message: WebSocketMessage) => {
    clientRef.current?.send(message);
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    send,
    connect,
    disconnect,
    readyState,
  };
}
