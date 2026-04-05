import { useState, useEffect } from 'react';
import { Table, Card, Button, Space, Modal, Form, Input, Select, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons';
import { webhooksAPI, plansAPI } from '../services/api';

export default function Webhooks() {
  const [webhooks, setWebhooks] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [webhooksRes, plansRes] = await Promise.all([
        webhooksAPI.list(),
        plansAPI.list(1),
      ]);
      setWebhooks(webhooksRes.data || []);
      setPlans(plansRes.data || []);
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await webhooksAPI.create(values);
      message.success('创建成功');
      setModalVisible(false);
      form.resetFields();
      loadData();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await webhooksAPI.delete(id);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const copyUrl = (url) => {
    navigator.clipboard.writeText(url);
    message.success('URL已复制');
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name' },
    {
      title: '触发URL',
      dataIndex: 'trigger_url',
      render: (url) => (
        <Space>
          <code style={{ fontSize: 12 }}>{url}</code>
          <Button type="text" icon={<CopyOutlined />} onClick={() => copyUrl(url)} />
        </Space>
      ),
    },
    {
      title: '关联计划',
      dataIndex: 'plan_id',
      width: 150,
      render: (id) => plans.find((p) => p.id === id)?.name || id,
    },
    {
      title: 'Token',
      dataIndex: 'token',
      width: 150,
      render: (t) => <code style={{ fontSize: 11 }}>{t}</code>,
    },
    {
      title: '操作',
      width: 100,
      render: (_, record) => (
        <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>Webhook</h2>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => {
            form.resetFields();
            setModalVisible(true);
          }}>
            新建Webhook
          </Button>
          <Button onClick={loadData}>刷新</Button>
        </Space>

        <Table dataSource={webhooks} columns={columns} rowKey="id" loading={loading} />
      </Card>

      <Modal title="新建Webhook" open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="plan_id" label="测试计划" rules={[{ required: true }]}>
            <Select>
              {plans.map((p) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}