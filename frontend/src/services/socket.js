import { io } from 'socket.io-client';

const SOCKET_URL = '';

class SocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect() {
    if (this.socket) return;

    this.socket = io(SOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // 订阅任务日志
  subscribeTask(taskId) {
    if (!this.socket) return;

    this.socket.emit('subscribe_task', { task_id: taskId });
    console.log(`Subscribed to task ${taskId} logs`);
  }

  // 取消订阅任务日志
  unsubscribeTask(taskId) {
    if (!this.socket) return;

    this.socket.emit('unsubscribe_task', { task_id: taskId });
  }

  // 监听任务日志
  onTaskLog(callback) {
    if (!this.socket) return;

    const handler = (data) => {
      callback(data);
    };

    this.socket.on('task_log', handler);

    return () => {
      this.socket.off('task_log', handler);
    };
  }

  // 监听任务状态更新
  onTaskUpdate(callback) {
    if (!this.socket) return;

    const handler = (data) => {
      callback(data);
    };

    this.socket.on('task_update', handler);

    return () => {
      this.socket.off('task_update', handler);
    };
  }

  // 监听性能数据
  onPerformance(callback) {
    if (!this.socket) return;

    const handler = (data) => {
      callback(data);
    };

    this.socket.on('performance', handler);

    return () => {
      this.socket.off('performance', handler);
    };
  }
}

export const socketService = new SocketService();
export default socketService;