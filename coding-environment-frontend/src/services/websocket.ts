/** WebSocket client for CWS and MCP Server connections. */

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private messageQueue: string[] = [];

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      let timeout: ReturnType<typeof setTimeout> | null = null;
      
      try {
        // Use proxy through FastAPI
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}${this.url}`;
        
        console.log('Attempting WebSocket connection to:', wsUrl);
        this.ws = new WebSocket(wsUrl);
        
        // Set a timeout for connection
        timeout = setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            console.error('WebSocket connection timeout');
            if (this.ws) {
              this.ws.close();
            }
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000); // 10 second timeout

        this.ws.onopen = () => {
          console.log('WebSocket connected:', this.url);
          if (timeout) clearTimeout(timeout);
          this.reconnectAttempts = 0;
          // Send queued messages
          while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (message && this.ws?.readyState === WebSocket.OPEN) {
              this.ws.send(message);
            }
          }
          this.emit('open', {});
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.emit('message', data);
          } catch (e) {
            // If not JSON, emit raw data
            this.emit('message', event.data);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error, 'URL:', wsUrl);
          if (timeout) clearTimeout(timeout);
          this.emit('error', error);
          reject(new Error(`WebSocket connection failed: ${wsUrl}`));
        };

        this.ws.onclose = () => {
          console.log('WebSocket closed:', this.url);
          this.emit('close', {});
          this.ws = null;
          
          // Attempt to reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
              console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
              this.connect().catch(console.error);
            }, this.reconnectDelay * this.reconnectAttempts);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  send(data: any): void {
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      // Queue message if not connected
      this.messageQueue.push(message);
      if (this.ws?.readyState === WebSocket.CONNECTING) {
        // Wait for connection
        return;
      }
      // Try to reconnect
      this.connect().catch(console.error);
    }
  }

  on(event: string, callback: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: (data: any) => void): void {
    this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any): void {
    this.listeners.get(event)?.forEach(callback => callback(data));
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
    this.messageQueue = [];
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
