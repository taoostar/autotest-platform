import { useState, useEffect } from 'react';
import { Table, Card, Button, Space, Tag, Modal, Form, Input, message, Badge, Popconfirm } from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, RobotOutlined
} from '@ant-design/icons';
import { agentsAPI } from '../services/api';

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [groupModalVisible, setGroupModalVisible] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [form] = Form.useForm();
  const [groupForm] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [agentsRes, groupsRes] = await Promise.all([
        agentsAPI.list(),
        agentsAPI.listGroups(),
      ]);
      setAgents(agentsRes.data || []);
      setGroups(groupsRes.data || []);
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingAgent) {
        await agentsAPI.update(editingAgent.id, values);
        message.success('更新成功');
      }
      setModalVisible(false);
      loadData();
    } catch (error) {
      message.error(editingAgent ? '更新失败' : '创建失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await agentsAPI.delete(id);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleGroupSubmit = async () => {
    try {
      await groupForm.validateFields();
      const values = groupForm.getFieldsValue();
      await agentsAPI.createGroup(values);
      message.success('创建成功');
      setGroupModalVisible(false);
      groupForm.resetFields();
      loadData();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const getStatusBadge = (status) => {
    const isOnline = status === 'online';
    return (
      <Badge status={isOnline ? 'success' : 'default'} text={isOnline ? '在线' : '离线'} />
    );
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name' },
    { title: '主机名', dataIndex: 'hostname' },
    { title: 'IP地址', dataIndex: 'ip_address' },
    {
      title: '系统',
      dataIndex: 'os_type',
      width: 80,
      render: (t) => {
        const colors = { linux: 'green', windows: 'blue', mac: 'purple' };
        return <Tag color={colors[t]}>{t}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (s) => getStatusBadge(s),
    },
    {
      title: '负载',
      dataIndex: 'current_load',
      width: 100,
      render: (l) => l ? `${(l * 100).toFixed(0)}%` : '-',
    },
    {
      title: '标签',
      dataIndex: 'labels',
      render: (labels) => (labels || []).map((l) => <Tag key={l}>{l}</Tag>),
    },
    {
      title: '操作',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="text" icon={<EditOutlined />} onClick={() => {
            setEditingAgent(record);
            form.setFieldsValue(record);
            setModalVisible(true);
          }} />
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>Agent管理</h2>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingAgent(null);
              form.resetFields();
              setModalVisible(true);
            }}
          >
            添加Agent
          </Button>
          <Button onClick={() => setGroupModalVisible(true)}>新建分组</Button>
          <Button onClick={loadData}>刷新</Button>
        </Space>

        <Table
          dataSource={agents}
          columns={columns}
          rowKey="id"
          loading={loading}
        />
      </Card>

      <Modal
        title={editingAgent ? '编辑Agent' : '添加Agent'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="hostname" label="主机名">
            <Input />
          </Form.Item>
          <Form.Item name="ip_address" label="IP地址">
            <Input />
          </Form.Item>
          <Form.Item name="os_type" label="系统类型" initialValue="linux">
            <Input />
          </Form.Item>
          <Form.Item name="labels" label="标签">
            <Input placeholder="逗号分隔" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新建分组"
        open={groupModalVisible}
        onOk={handleGroupSubmit}
        onCancel={() => setGroupModalVisible(false)}
      >
        <Form form={groupForm} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}