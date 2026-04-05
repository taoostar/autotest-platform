import { useState, useEffect } from 'react';
import { Tabs, Card, Form, Input, Button, Table, Space, message, Switch } from 'antd';
import { configsAPI, auditAPI } from '../services/api';

export default function Settings() {
  const [configs, setConfigs] = useState({});
  const [envVars, setEnvVars] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadConfigs();
    loadEnvVars();
    loadAuditLogs();
  }, []);

  const loadConfigs = async () => {
    try {
      const res = await configsAPI.get();
      setConfigs(res.data || {});
      form.setFieldsValue(res.data);
    } catch (error) {
      console.error('Failed to load configs');
    }
  };

  const loadEnvVars = async () => {
    try {
      const res = await configsAPI.listEnvVars();
      setEnvVars(res.data || []);
    } catch (error) {
      console.error('Failed to load env vars');
    }
  };

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await auditAPI.list({ page_size: 20 });
      setAuditLogs(res.data.logs || []);
    } catch (error) {
      console.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfigs = async () => {
    try {
      await configsAPI.update(form.getFieldsValue());
      message.success('保存成功');
    } catch (error) {
      message.error('保存失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用户ID', dataIndex: 'user_id', width: 80 },
    { title: '操作', dataIndex: 'action', width: 80 },
    { title: '资源类型', dataIndex: 'resource_type', width: 120 },
    {
      title: '时间',
      dataIndex: 'timestamp',
      width: 180,
      render: (t) => t?.replace('T', ' ').slice(0, 19),
    },
  ];

  const items = [
    {
      key: 'configs',
      label: '系统配置',
      children: (
        <Card>
          <Form form={form} layout="vertical" style={{ maxWidth: 500 }}>
            <Form.Item name="log.max_size_mb" label="日志大小限制(MB)">
              <Input type="number" />
            </Form.Item>
            <Form.Item name="log.retention_days" label="日志保留天数">
              <Input type="number" />
            </Form.Item>
            <Button type="primary" onClick={handleSaveConfigs}>保存配置</Button>
          </Form>
        </Card>
      ),
    },
    {
      key: 'env',
      label: '环境变量',
      children: (
        <Card>
          <p style={{ marginBottom: 16 }}>全局环境变量配置</p>
          <Table dataSource={envVars} columns={[
            { title: 'Key', dataIndex: 'key', width: 200 },
            { title: 'Value', dataIndex: 'value' },
          ]} rowKey="id" size="small" pagination={false} />
        </Card>
      ),
    },
    {
      key: 'audit',
      label: '审计日志',
      children: (
        <Card>
          <Space style={{ marginBottom: 16 }}>
            <Button onClick={loadAuditLogs}>刷新</Button>
          </Space>
          <Table dataSource={auditLogs} columns={columns} rowKey="id" loading={loading} size="small" />
        </Card>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>系统设置</h2>
      <Tabs items={items} />
    </div>
  );
}