import type { WebSocketMessage } from '@/types/message';

type MessageHandler = (message: WebSocketMessage) => void;
type StatusHandler = () => void;

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;

  private onMessageHandlers: MessageHandler[] = [];
  private onOpenHandlers: StatusHandler[] = [];
  private onCloseHandlers: StatusHandler[] = [];
  private onErrorHandlers: StatusHandler[] = [];

  constructor(path: string, token?: string) {
    const params = token ? `?token=${encodeURIComponent(token)}` : '';
    this.url = `${WS_URL}${path}${params}`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.onOpenHandlers.forEach((handler) => handler());
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.onMessageHandlers.forEach((handler) => handler(message));
      } catch {
        // Ignore non-JSON messages
      }
    };

    this.ws.onclose = () => {
      this.onCloseHandlers.forEach((handler) => handler());
      if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      this.onErrorHandlers.forEach((handler) => handler());
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
      this.connect();
    }, this.reconnectDelay);
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.onMessageHandlers.push(handler);
    return () => {
      this.onMessageHandlers = this.onMessageHandlers.filter((h) => h !== handler);
    };
  }

  onOpen(handler: StatusHandler): () => void {
    this.onOpenHandlers.push(handler);
    return () => {
      this.onOpenHandlers = this.onOpenHandlers.filter((h) => h !== handler);
    };
  }

  onClose(handler: StatusHandler): () => void {
    this.onCloseHandlers.push(handler);
    return () => {
      this.onCloseHandlers = this.onCloseHandlers.filter((h) => h !== handler);
    };
  }

  onError(handler: StatusHandler): () => void {
    this.onErrorHandlers.push(handler);
    return () => {
      this.onErrorHandlers = this.onErrorHandlers.filter((h) => h !== handler);
    };
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
