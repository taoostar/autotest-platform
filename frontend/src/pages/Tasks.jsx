import { useState, useEffect } from 'react';
import { Table, Card, Button, Space, Tag, Select, message, Modal, Badge } from 'antd';
import {
  SyncOutlined, StopOutlined, ReloadOutlined, EyeOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { tasksAPI } from '../services/api';

export default function Tasks() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadTasks();
  }, [page, status]);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (status) params.status = status;
      const res = await tasksAPI.list(params);
      setTasks(res.data.tasks || []);
      setTotal(res.data.total || 0);
    } catch (error) {
      message.error('加载任务失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id) => {
    try {
      await tasksAPI.cancel(id);
      message.success('任务已取消');
      loadTasks();
    } catch (error) {
      message.error('取消失败');
    }
  };

  const handleRetry = async (id) => {
    try {
      const res = await tasksAPI.retry(id);
      message.success('任务已重新创建');
      navigate(`/tasks/${res.data.id}`);
    } catch (error) {
      message.error('重试失败');
    }
  };

  const getStatusTag = (status) => {
    const statusMap = {
      success: { color: 'success', text: '成功' },
      failed: { color: 'error', text: '失败' },
      running: { color: 'processing', text: '运行中' },
      pending: { color: 'default', text: '等待中' },
      cancelled: { color: 'default', text: '已取消' },
    };
    const { color, text } = statusMap[status] || { color: 'default', text: status };
    return <Badge status={color} text={text} />;
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 80 },
    { title: '计划ID', dataIndex: 'plan_id', width: 80 },
    {
      title: 'Agent',
      dataIndex: 'agent_id',
      width: 80,
      render: (id) => id || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (s) => getStatusTag(s),
    },
    {
      title: '触发方式',
      dataIndex: 'trigger_type',
      width: 100,
      render: (t) => {
        const map = { manual: '手动', schedule: '定时', webhook: 'Webhook' };
        return map[t] || t;
      },
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      width: 100,
      render: (d) => (d ? `${d.toFixed(1)}s` : '-'),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (t) => t?.replace('T', ' ').slice(0, 19),
    },
    {
      title: '操作',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/tasks/${record.id}`)}
          >
            查看
          </Button>
          {record.status === 'pending' || record.status === 'running' ? (
            <Button
              type="text"
              danger
              icon={<StopOutlined />}
              onClick={() => handleCancel(record.id)}
            >
              取消
            </Button>
          ) : null}
          {record.status === 'failed' || record.status === 'cancelled' ? (
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={() => handleRetry(record.id)}
            >
              重试
            </Button>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>测试任务</h2>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="状态筛选"
            allowClear
            value={status}
            onChange={(v) => { setStatus(v); setPage(1); }}
            style={{ width: 120 }}
          >
            <Select.Option value="pending">等待中</Select.Option>
            <Select.Option value="running">运行中</Select.Option>
            <Select.Option value="success">成功</Select.Option>
            <Select.Option value="failed">失败</Select.Option>
            <Select.Option value="cancelled">已取消</Select.Option>
          </Select>
          <Button icon={<SyncOutlined />} onClick={loadTasks}>刷新</Button>
        </Space>

        <Table
          dataSource={tasks}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p, ps) => { setPage(p); setPageSize(ps); },
          }}
          onRow={(record) => ({
            onClick: () => navigate(`/tasks/${record.id}`),
            style: { cursor: 'pointer' },
          })}
        />
      </Card>
    </div>
  );
}