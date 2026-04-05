import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Space, Tag, Badge, Descriptions, Tabs, Table, message, Row, Col, Statistic } from 'antd';
import {
  ArrowLeftOutlined, ReloadOutlined, StopOutlined,
  PlayCircleOutlined, ThunderboltOutlined
} from '@ant-design/icons';
import { tasksAPI } from '../services/api';
import socketService from '../services/socket';

export default function TaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState({ passed: 0, failed: 0, error: 0, cancelled: 0 });
  const [logs, setLogs] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('results');
  const logContainerRef = useRef(null);

  useEffect(() => {
    loadTaskDetail();
    loadResults();

    // 连接WebSocket
    socketService.connect();
    socketService.subscribeTask(parseInt(id));

    // 监听日志
    const unsubLog = socketService.onTaskLog((data) => {
      if (data.task_id === parseInt(id)) {
        setLogs((prev) => [...prev, {
          content: data.content,
          timestamp: data.timestamp,
          result_id: data.result_id
        }]);
      }
    });

    // 监听性能数据
    const unsubPerf = socketService.onPerformance((data) => {
      if (data.task_id === parseInt(id)) {
        setPerformance((prev) => prev ? [...prev, data] : [data]);
      }
    });

    return () => {
      socketService.unsubscribeTask(parseInt(id));
      if (unsubLog) unsubLog();
      if (unsubPerf) unsubPerf();
    };
  }, [id]);

  const loadTaskDetail = async () => {
    try {
      const res = await tasksAPI.get(id);
      setTask(res.data);
    } catch (error) {
      message.error('加载任务详情失败');
    }
  };

  const loadResults = async () => {
    try {
      const res = await tasksAPI.getResults(id);
      setResults(res.data.results || []);
      setSummary(res.data.summary || { passed: 0, failed: 0, error: 0, cancelled: 0 });
    } catch (error) {
      console.error('加载结果失败', error);
    }
  };

  const handleDispatch = async () => {
    setLoading(true);
    try {
      await tasksAPI.dispatch(id);
      message.success('任务已分发');
      loadTaskDetail();
    } catch (error) {
      message.error('分发失败: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    try {
      await tasksAPI.cancel(id);
      message.success('任务已取消');
      loadTaskDetail();
    } catch (error) {
      message.error('取消失败');
    }
  };

  const getStatusTag = (status) => {
    const statusMap = {
      success: { color: 'success', text: '成功' },
      failed: { color: 'error', text: '失败' },
      running: { color: 'processing', text: '运行中' },
      pending: { color: 'default', text: '等待中' },
      cancelled: { color: 'default', text: '已取消' },
      error: { color: 'error', text: '错误' },
    };
    const { color, text } = statusMap[status] || { color: 'default', text: status };
    return <Badge status={color} text={text} />;
  };

  const resultColumns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用例ID', dataIndex: 'case_id', width: 80 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (s) => getStatusTag(s),
    },
    { title: '耗时', dataIndex: 'duration', width: 100, render: (d) => d ? `${d.toFixed(2)}s` : '-' },
    { title: '错误类型', dataIndex: 'error_type', ellipsis: true },
    { title: '错误信息', dataIndex: 'error_message', ellipsis: true },
  ];

  const perfColumns = [
    { title: '时间', dataIndex: 'timestamp', width: 180, render: (t) => t?.replace('T', ' ').slice(0, 19) },
    { title: 'CPU %', dataIndex: 'cpu', width: 100, render: (v) => v?.toFixed(1) },
    { title: '内存 %', dataIndex: 'memory', width: 100, render: (v) => v?.toFixed(1) },
    { title: 'IO读 MB', dataIndex: 'io_read_mb', width: 100, render: (v) => v?.toFixed(2) },
    { title: 'IO写 MB', dataIndex: 'io_write_mb', width: 100, render: (v) => v?.toFixed(2) },
    { title: '文件描述符', dataIndex: 'fd_count', width: 100 },
  ];

  const tabItems = [
    {
      key: 'results',
      label: '执行结果',
      children: (
        <Table
          dataSource={results}
          columns={resultColumns}
          rowKey="id"
          size="small"
          pagination={false}
        />
      ),
    },
    {
      key: 'logs',
      label: '实时日志',
      children: (
        <div
          ref={logContainerRef}
          style={{
            height: 400,
            overflow: 'auto',
            background: '#1e1e1e',
            color: '#d4d4d4',
            fontFamily: 'Monaco, Menlo, monospace',
            fontSize: 12,
            padding: 12,
            borderRadius: 4,
          }}
        >
          {logs.length === 0 ? (
            <div style={{ color: '#666' }}>暂无日志...</div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} style={{ marginBottom: 4 }}>
                <span style={{ color: '#858585' }}>[{log.timestamp?.slice(11, 19)}]</span>{' '}
                <span style={{ color: log.content?.startsWith('[ERROR]') ? '#f48771' : '#d4d4d4' }}>
                  {log.content}
                </span>
              </div>
            ))
          )}
        </div>
      ),
    },
    {
      key: 'performance',
      label: '性能监控',
      children: (
        <Table
          dataSource={performance || []}
          columns={perfColumns}
          rowKey="id"
          size="small"
          pagination={false}
        />
      ),
    },
  ];

  if (!task) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tasks')}>返回</Button>
        <h2 style={{ margin: 0 }}>任务 #{id}</h2>
        {getStatusTag(task.status)}
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="通过"
              value={summary.passed}
              valueStyle={{ color: '#52c41a' }}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="失败"
              value={summary.failed}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<StopOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="错误"
              value={summary.error}
              valueStyle={{ color: '#faad14' }}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="耗时"
              value={task.duration ? task.duration.toFixed(1) : '-'}
              suffix="秒"
            />
          </Card>
        </Col>
      </Row>

      <Descriptions size="small" style={{ marginBottom: 16 }} column={4}>
        <Descriptions.Item label="计划ID">{task.plan_id}</Descriptions.Item>
        <Descriptions.Item label="Agent">{task.agent_id || '-'}</Descriptions.Item>
        <Descriptions.Item label="触发方式">
          {task.trigger_type === 'manual' ? '手动' : task.trigger_type === 'schedule' ? '定时' : 'Webhook'}
        </Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {task.created_at?.replace('T', ' ').slice(0, 19)}
        </Descriptions.Item>
      </Descriptions>

      <Space style={{ marginBottom: 16 }}>
        {task.status === 'pending' && (
          <Button type="primary" onClick={handleDispatch} loading={loading}>
            分发任务
          </Button>
        )}
        {(task.status === 'pending' || task.status === 'running') && (
          <Button danger onClick={handleCancel}>
            取消任务
          </Button>
        )}
        <Button icon={<ReloadOutlined />} onClick={() => { loadTaskDetail(); loadResults(); }}>
          刷新
        </Button>
      </Space>

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  );
}