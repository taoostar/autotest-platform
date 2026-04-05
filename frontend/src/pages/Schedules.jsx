import { useState, useEffect } from 'react';
import { Table, Card, Button, Space, Tag, Modal, Form, Input, Select, message, Popconfirm, Switch } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { schedulesAPI, plansAPI } from '../services/api';

export default function Schedules() {
  const [schedules, setSchedules] = useState([]);
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
      const [schedulesRes, plansRes] = await Promise.all([
        schedulesAPI.list(),
        plansAPI.list(plans[0]?.id || 1),
      ]);
      setSchedules(schedulesRes.data || []);

      if (plansRes.data?.length > 0) {
        setPlans(plansRes.data);
      }
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const loadPlans = async () => {
    try {
      const res = await plansAPI.list(1);
      setPlans(res.data || []);
    } catch (error) {
      console.error('Failed to load plans');
    }
  };

  useEffect(() => {
    loadPlans();
  }, []);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await schedulesAPI.create(values);
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
      await schedulesAPI.delete(id);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleToggle = async (record) => {
    try {
      if (record.enabled) {
        await schedulesAPI.disable(record.id);
      } else {
        await schedulesAPI.enable(record.id);
      }
      loadData();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: 'Cron', dataIndex: 'cron_expression', width: 150 },
    { title: '时区', dataIndex: 'timezone', width: 120 },
    {
      title: '计划',
      dataIndex: 'plan_id',
      width: 100,
      render: (id) => plans.find((p) => p.id === id)?.name || id,
    },
    {
      title: '启用',
      dataIndex: 'enabled',
      width: 80,
      render: (enabled, record) => (
        <Switch checked={enabled} onChange={() => handleToggle(record)} size="small" />
      ),
    },
    {
      title: '操作',
      width: 120,
      render: (_, record) => (
        <Space>
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>定时任务</h2>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => {
            form.resetFields();
            setModalVisible(true);
          }}>
            新建定时任务
          </Button>
          <Button onClick={loadData}>刷新</Button>
        </Space>

        <Table dataSource={schedules} columns={columns} rowKey="id" loading={loading} />
      </Card>

      <Modal title="新建定时任务" open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="plan_id" label="测试计划" rules={[{ required: true }]}>
            <Select>
              {plans.map((p) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="cron_expression" label="Cron表达式" rules={[{ required: true, message: '请输入cron表达式' }]}>
            <Input placeholder="0 9 * * * (每天9点)" />
          </Form.Item>
          <Form.Item name="timezone" label="时区" initialValue="Asia/Shanghai">
            <Select>
              <Select.Option value="Asia/Shanghai">Asia/Shanghai</Select.Option>
              <Select.Option value="UTC">UTC</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}