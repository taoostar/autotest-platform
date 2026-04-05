import { useState, useEffect } from 'react';
import {
  Table, Card, Button, Input, Space, Tag, Modal, Form,
  Select, message, Popconfirm, Tree, Drawer
} from 'antd';
import {
  PlusOutlined, SearchOutlined, StarOutlined, StarFilled,
  EditOutlined, DeleteOutlined, PlayCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { projectsAPI, modulesAPI, casesAPI } from '../services/api';

const { TextArea } = Input;

export default function Cases() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [modules, setModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [caseModalVisible, setCaseModalVisible] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [codeContent, setCodeContent] = useState('');
  const [scriptType, setScriptType] = useState('python');
  const [form] = Form.useForm();

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadModules(selectedProject);
    } else {
      setModules([]);
      setCases([]);
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedModule) {
      loadCases(selectedModule);
    } else {
      setCases([]);
    }
  }, [selectedModule]);

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

  const loadModules = async (projectId) => {
    try {
      const res = await modulesAPI.list(projectId);
      setModules(res.data || []);
    } catch (error) {
      message.error('加载模块失败');
    }
  };

  const loadCases = async (moduleId) => {
    setLoading(true);
    try {
      const params = {};
      if (searchText) params.keyword = searchText;
      const res = await casesAPI.list(moduleId, params);
      setCases(res.data.cases || []);
    } catch (error) {
      message.error('加载用例失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (selectedModule) {
      loadCases(selectedModule);
    }
  };

  const openCaseModal = (record = null) => {
    setEditingCase(record);
    if (record) {
      form.setFieldsValue(record);
      setCodeContent(record.code || '');
      setScriptType(record.script_type || 'python');
    } else {
      form.resetFields();
      setCodeContent('');
      setScriptType('python');
    }
    setCaseModalVisible(true);
  };

  const handleCaseSubmit = async () => {
    try {
      const values = await form.validateFields();
      values.code = codeContent;
      if (editingCase) {
        await casesAPI.update(editingCase.id, values);
        message.success('更新成功');
      } else {
        await casesAPI.create(selectedModule, values);
        message.success('创建成功');
      }
      setCaseModalVisible(false);
      loadCases(selectedModule);
    } catch (error) {
      message.error(editingCase ? '更新失败' : '创建失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await casesAPI.delete(id);
      message.success('删除成功');
      loadCases(selectedModule);
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleToggleFavorite = async (id) => {
    try {
      await casesAPI.toggleFavorite(id);
      loadCases(selectedModule);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleRunCase = (record) => {
    navigate(`/plans?case_id=${record.id}`);
  };

  const columns = [
    {
      title: '收藏',
      width: 60,
      render: (_, record) => (
        <Button
          type="text"
          icon={record.is_favorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
          onClick={() => handleToggleFavorite(record.id)}
        />
      ),
    },
    { title: '名称', dataIndex: 'name', width: 200 },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 150,
      render: (tags) => (tags || []).map((t) => <Tag key={t}>{t}</Tag>),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 80,
      render: (p) => {
        const colors = { 1: 'red', 2: 'orange', 3: 'default', 4: 'blue', 5: 'purple' };
        return <Tag color={colors[p] || 'default'}>P{p}</Tag>;
      },
    },
    { title: '脚本', dataIndex: 'script_type', width: 80 },
    { title: '版本', dataIndex: 'current_version', width: 80 },
    {
      title: '操作',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button type="text" icon={<EditOutlined />} onClick={() => openCaseModal(record)} />
          <Button type="text" icon={<PlayCircleOutlined />} onClick={() => handleRunCase(record)} />
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const moduleTreeData = modules.map((m) => ({
    title: `${m.name} (${m.case_count})`,
    key: m.id,
  }));

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>测试用例</h2>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="选择项目"
            value={selectedProject}
            onChange={(v) => { setSelectedProject(v); setSelectedModule(null); }}
            style={{ width: 200 }}
          >
            {projects.map((p) => (
              <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
            ))}
          </Select>
        </Space>

        <Space style={{ marginBottom: 16 }} align="start">
          <Tree
            treeData={moduleTreeData}
            selectedKeys={selectedModule ? [selectedModule] : []}
            onSelect={(keys) => setSelectedModule(keys[0] || null)}
            style={{ minWidth: 200 }}
          />
          <div style={{ flex: 1 }}>
            <Space style={{ marginBottom: 8 }}>
              <Input.Search
                placeholder="搜索用例"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onSearch={handleSearch}
                style={{ width: 200 }}
              />
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => openCaseModal()}
                disabled={!selectedModule}
              >
                新建用例
              </Button>
            </Space>
            <Table
              dataSource={cases}
              columns={columns}
              rowKey="id"
              loading={loading}
              size="small"
            />
          </div>
        </Space>
      </Card>

      <Modal
        title={editingCase ? '编辑用例' : '新建用例'}
        open={caseModalVisible}
        onOk={handleCaseSubmit}
        onCancel={() => setCaseModalVisible(false)}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>
          <Space>
            <Form.Item name="script_type" label="脚本类型" initialValue="python">
              <Select style={{ width: 120 }} onChange={(v) => setScriptType(v)}>
                <Select.Option value="python">Python</Select.Option>
                <Select.Option value="shell">Shell</Select.Option>
                <Select.Option value="javascript">JavaScript</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="priority" label="优先级" initialValue={3}>
              <Select style={{ width: 100 }}>
                <Select.Option value={1}>P1 (最高)</Select.Option>
                <Select.Option value={2}>P2</Select.Option>
                <Select.Option value={3}>P3</Select.Option>
                <Select.Option value={4}>P4</Select.Option>
                <Select.Option value={5}>P5 (最低)</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="timeout" label="超时(秒)" initialValue={60}>
              <Input type="number" style={{ width: 100 }} />
            </Form.Item>
          </Space>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入标签后回车" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="代码">
            <Editor
              height="300px"
              language={scriptType === 'python' ? 'python' : scriptType === 'javascript' ? 'javascript' : 'shell'}
              value={codeContent}
              onChange={(value) => setCodeContent(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}