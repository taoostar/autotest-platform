import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Space, Tag, Badge, Descriptions, Tabs, Table, message, Row, Col, Statistic, Empty, Alert } from 'antd';
import {
  ArrowLeftOutlined, ReloadOutlined, StopOutlined,
  PlayCircleOutlined, ThunderboltOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { tasksAPI } from '../services/api';
import socketService from '../services/socket';

export default function TaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState({ passed: 0, failed: 0, error: 0, cancelled: 0 });
  const [logs, setLogs] = useState([]);
  const [performance, setPerformance] = useState([]);
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
        setPerformance((prev) => [...prev, data]);
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
    {
      title: '性能',
      width: 100,
      render: (_, record) => record.perf_summary ? '有' : '-'
    },
    { title: '错误类型', dataIndex: 'error_type', ellipsis: true },
    { title: '错误信息', dataIndex: 'error_message', ellipsis: true },
  ];

  // 性能图表配置
  const getPerfChartOption = () => {
    const systemData = performance.filter(p => p.system).map(p => ({
      time: p.timestamp?.slice(11, 19) || '',
      cpu: p.system?.cpu || 0,
      memory: p.system?.memory || 0,
      load: p.system?.load_avg ? Math.min(...p.system.load_avg) : 0
    }));

    const processData = performance.filter(p => p.process).map(p => ({
      time: p.timestamp?.slice(11, 19) || '',
      cpu: p.process?.cpu || 0,
      memory: p.process?.memory || 0,
      fd: p.process?.fd_count || 0
    }));

    return {
      title: { text: '系统性能', left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['CPU %', '内存 %', '负载'], bottom: 0 },
      xAxis: { type: 'category', data: systemData.map(d => d.time) },
      yAxis: [
        { type: 'value', name: '%', max: 100, min: 0 },
        { type: 'value', name: 'Load', min: 0 }
      ],
      series: [
        { name: 'CPU %', type: 'line', data: systemData.map(d => d.cpu) },
        { name: '内存 %', type: 'line', data: systemData.map(d => d.memory) },
        { name: '负载', type: 'line', yAxisIndex: 1, data: systemData.map(d => d.load) }
      ],
      grid: { left: 50, right: 20, top: 40, bottom: 60 }
    };
  };

  const getProcessChartOption = () => {
    const processData = performance.filter(p => p.process).map(p => ({
      time: p.timestamp?.slice(11, 19) || '',
      cpu: p.process?.cpu || 0,
      memory: p.process?.memory || 0,
      fd: p.process?.fd_count || 0
    }));

    if (processData.length === 0) {
      return null;
    }

    return {
      title: { text: `进程性能 (${processData[0]?.process?.keyword || ''})`, left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['进程CPU %', '进程内存 %', 'FD数'], bottom: 0 },
      xAxis: { type: 'category', data: processData.map(d => d.time) },
      yAxis: [
        { type: 'value', name: '%', max: 100, min: 0 },
        { type: 'value', name: 'FD', min: 0 }
      ],
      series: [
        { name: '进程CPU %', type: 'line', data: processData.map(d => d.cpu) },
        { name: '进程内存 %', type: 'line', data: processData.map(d => d.memory) },
        { name: 'FD数', type: 'line', yAxisIndex: 1, data: processData.map(d => d.fd) }
      ],
      grid: { left: 50, right: 20, top: 40, bottom: 60 }
    };
  };

  // 计算性能汇总
  const getPerfSummary = () => {
    if (performance.length === 0) return null;

    const systemData = performance.filter(p => p.system);
    const processData = performance.filter(p => p.process);

    const summary = { system: {}, process: {} };

    if (systemData.length > 0) {
      const cpus = systemData.map(p => p.system?.cpu).filter(c => c != null);
      const mems = systemData.map(p => p.system?.memory).filter(m => m != null);
      const loads = systemData.map(p => p.system?.load_avg).filter(l => l).flat().filter(l => l != null);

      summary.system = {
        cpu_avg: cpus.length ? (cpus.reduce((a, b) => a + b, 0) / cpus.length).toFixed(1) : 0,
        cpu_max: cpus.length ? Math.max(...cpus).toFixed(1) : 0,
        memory_avg: mems.length ? (mems.reduce((a, b) => a + b, 0) / mems.length).toFixed(1) : 0,
        memory_max: mems.length ? Math.max(...mems).toFixed(1) : 0,
        load_max: loads.length ? Math.max(...loads).toFixed(2) : 0
      };
    }

    if (processData.length > 0) {
      const cpus = processData.map(p => p.process?.cpu).filter(c => c != null);
      const mems = processData.map(p => p.process?.memory).filter(m => m != null);
      const fds = processData.map(p => p.process?.fd_count).filter(f => f != null);

      summary.process = {
        keyword: processData[0]?.process?.keyword,
        cpu_avg: cpus.length ? (cpus.reduce((a, b) => a + b, 0) / cpus.length).toFixed(1) : 0,
        cpu_max: cpus.length ? Math.max(...cpus).toFixed(1) : 0,
        memory_avg: mems.length ? (mems.reduce((a, b) => a + b, 0) / mems.length).toFixed(1) : 0,
        memory_max: mems.length ? Math.max(...mems).toFixed(1) : 0,
        fd_max: fds.length ? Math.max(...fds) : 0
      };
    }

    return summary;
  };

  const perfSummary = getPerfSummary();

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
      label: '性能数据',
      children: (
        <div>
          {performance.length === 0 ? (
            <Empty description="暂无性能数据（串行执行时才会采集）" />
          ) : (
            <>
              {task?.concurrency > 1 && (
                <Alert
                  message="注意"
                  description="当前为并行执行模式，性能数据可能不准确。建议使用串行执行模式以获得准确的性能数据。"
                  type="warning"
                  style={{ marginBottom: 16 }}
                />
              )}
              <Row gutter={16}>
                <Col span={12}>
                  <Card title="系统性能">
                    <ReactECharts option={getPerfChartOption()} style={{ height: 250 }} />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card title="进程性能">
                    {getProcessChartOption() ? (
                      <ReactECharts option={getProcessChartOption()} style={{ height: 250 }} />
                    ) : (
                      <Empty description="无进程数据（请检查进程关键字配置）" />
                    )}
                  </Card>
                </Col>
              </Row>
              {perfSummary && (
                <Card title="性能统计" style={{ marginTop: 16 }}>
                  <Row gutter={16}>
                    <Col span={4}>
                      <Statistic title="CPU 均值" value={perfSummary.system?.cpu_avg || 0} suffix="%" />
                    </Col>
                    <Col span={4}>
                      <Statistic title="CPU 峰值" value={perfSummary.system?.cpu_max || 0} suffix="%" />
                    </Col>
                    <Col span={4}>
                      <Statistic title="内存均值" value={perfSummary.system?.memory_avg || 0} suffix="%" />
                    </Col>
                    <Col span={4}>
                      <Statistic title="内存峰值" value={perfSummary.system?.memory_max || 0} suffix="%" />
                    </Col>
                    <Col span={4}>
                      <Statistic title="负载峰值" value={perfSummary.system?.load_max || 0} />
                    </Col>
                    {perfSummary.process && (
                      <>
                        <Col span={4}>
                          <Statistic title="进程CPU均值" value={perfSummary.process?.cpu_avg || 0} suffix="%" />
                        </Col>
                        <Col span={4}>
                          <Statistic title="进程FD峰值" value={perfSummary.process?.fd_max || 0} />
                        </Col>
                      </>
                    )}
                  </Row>
                </Card>
              )}
            </>
          )}
        </div>
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