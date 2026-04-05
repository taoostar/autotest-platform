import { useState, useEffect } from 'react';
import {
  Table, Card, Button, Space, Tag, Modal, Form,
  Input, Select, message, Popconfirm, Transfer
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  PlayCircleOutlined, CopyOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { projectsAPI, plansAPI, casesAPI, tasksAPI } from '../services/api';

export default function Plans() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [planModalVisible, setPlanModalVisible] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [form] = Form.useForm();
  const [caseModalVisible, setCaseModalVisible] = useState(false);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [availableCases, setAvailableCases] = useState([]);
  const [selectedCases, setSelectedCases] = useState([]);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadPlans(selectedProject);
    } else {
      setPlans([]);
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    try {
      const res = await projectsAPI.list();
      setProjects(res.data || []);
      if (res.data?.length > 0) {
        setSelectedProject(res.data[0].id);
      }
    } catch (error) {
      message.error('加载项目失败');
    }
  };

  const loadPlans = async (projectId) => {
    setLoading(true);
    try {
      const res = await plansAPI.list(projectId);
      setPlans(res.data || []);
    } catch (error) {
      message.error('加载计划失败');
    } finally {
      setLoading(false);
    }
  };

  const openPlanModal = (record = null) => {
    setEditingPlan(record);
    if (record) {
      form.setFieldsValue(record);
    } else {
      form.resetFields();
    }
    setPlanModalVisible(true);
  };

  const handlePlanSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingPlan) {
        await plansAPI.update(editingPlan.id, values);
        message.success('更新成功');
      } else {
        await plansAPI.create(selectedProject, values);
        message.success('创建成功');
      }
      setPlanModalVisible(false);
      loadPlans(selectedProject);
    } catch (error) {
      message.error(editingPlan ? '更新失败' : '创建失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await plansAPI.delete(id);
      message.success('删除成功');
      loadPlans(selectedProject);
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleCopy = async (record) => {
    try {
      await plansAPI.copy(record.id);
      message.success('复制成功');
      loadPlans(selectedProject);
    } catch (error) {
      message.error('复制失败');
    }
  };

  const handleRunPlan = async (record) => {
    try {
      const res = await tasksAPI.create({ plan_id: record.id });
      message.success('任务已创建');
      navigate(`/tasks/${res.data.id}`);
    } catch (error) {
      message.error('创建任务失败');
    }
  };

  const openCaseModal = async (record) => {
    setCurrentPlan(record);
    try {
      const res = await casesAPI.list(record.project_id);
      const allCases = res.data.cases || [];
      setAvailableCases(allCases.map((c) => ({ key: c.id, title: c.name })));

      const planRes = await plansAPI.get(record.id);
      const planCases = planRes.data.cases || [];
      setSelectedCases(planCases.map((c) => c.id));

      setCaseModalVisible(true);
    } catch (error) {
      message.error('加载用例失败');
    }
  };

  const handleCaseSubmit = async () => {
    try {
      await plansAPI.updateCases(currentPlan.id, { case_ids: selectedCases });
      message.success('更新成功');
      setCaseModalVisible(false);
    } catch (error) {
      message.error('更新失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name' },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    {
      title: '环境变量',
      dataIndex: 'env_vars',
      width: 100,
      render: (vars) => Object.keys(vars || {}).length,
    },
    {
      title: '操作',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button type="text" icon={<EditOutlined />} onClick={() => openPlanModal(record)} />
          <Button type="text" icon={<PlayCircleOutlined />} onClick={() => handleRunPlan(record)} />
          <Button type="text" icon={<CopyOutlined />} onClick={() => handleCopy(record)} />
          <Button type="text" onClick={() => openCaseModal(record)}>关联用例</Button>
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>测试计划</h2>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="选择项目"
            value={selectedProject}
            onChange={(v) => setSelectedProject(v)}
            style={{ width: 200 }}
          >
            {projects.map((p) => (
              <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
            ))}
          </Select>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openPlanModal()}
            disabled={!selectedProject}
          >
            新建计划
          </Button>
        </Space>

        <Table
          dataSource={plans}
          columns={columns}
          rowKey="id"
          loading={loading}
        />
      </Card>

      <Modal
        title={editingPlan ? '编辑计划' : '新建计划'}
        open={planModalVisible}
        onOk={handlePlanSubmit}
        onCancel={() => setPlanModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="关联用例"
        open={caseModalVisible}
        onOk={handleCaseSubmit}
        onCancel={() => setCaseModalVisible(false)}
        width={600}
      >
        <Transfer
          dataSource={availableCases}
          targetKeys={selectedCases}
          onChange={setSelectedCases}
          render={(item) => item.title}
          titles={['可用用例', '已选用例']}
          listStyle={{ width: 250, height: 300 }}
        />
      </Modal>
    </div>
  );
}