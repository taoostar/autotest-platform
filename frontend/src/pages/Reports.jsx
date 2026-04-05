import { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Select, Space, Button, Modal, Tabs, Empty } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, DownloadOutlined, ThunderboltOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { reportsAPI, tasksAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Reports() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState({ today: {}, trend: [] });
  const [recentTasks, setRecentTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendType, setTrendType] = useState('pass_rate');
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskReport, setTaskReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [summaryRes, tasksRes] = await Promise.all([
        reportsAPI.getSummary({ days: 7 }),
        tasksAPI.list({ page_size: 10 }),
      ]);
      setSummary(summaryRes.data);
      setRecentTasks(tasksRes.data.tasks || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTaskReport = async (taskId) => {
    setReportLoading(true);
    try {
      const res = await reportsAPI.getTaskReport(taskId);
      setTaskReport(res.data);
    } catch (error) {
      console.error('Failed to load task report:', error);
    } finally {
      setReportLoading(false);
    }
  };

  const handleViewReport = (record) => {
    setSelectedTask(record);
    setReportModalVisible(true);
    loadTaskReport(record.id);
  };

  const getTrendOption = () => {
    const trend = summary.trend || [];
    let seriesData, yLabel;

    if (trendType === 'pass_rate') {
      seriesData = trend.map((t) => t.pass_rate || 0);
      yLabel = '{value}%';
    } else if (trendType === 'total') {
      seriesData = trend.map((t) => t.total || 0);
      yLabel = '{value}';
    } else {
      seriesData = trend.map((t) => t.passed || 0);
      yLabel = '{value}';
    }

    return {
      title: { text: '7天趋势', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: trend.map((t) => t.date?.slice(5) || ''),
      },
      yAxis: { type: 'value', axisLabel: { formatter: yLabel } },
      series: [{ data: seriesData, type: 'line', smooth: true, areaStyle: {} }],
      grid: { left: 50, right: 20, top: 40, bottom: 30 },
    };
  };

  // 获取性能图表配置
  const getPerfChartOption = (perfData) => {
    if (!perfData || perfData.length === 0) return null;

    const systemData = perfData.filter(p => p.cpu_percent != null).map(p => ({
      time: p.timestamp?.slice(11, 19) || '',
      cpu: p.cpu_percent || 0,
      memory: p.memory_percent || 0,
      load: p.load_avg_1 || 0
    }));

    if (systemData.length === 0) return null;

    return {
      title: { text: '系统性能趋势', left: 'center' },
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

  // 计算性能汇总
  const calcPerfSummary = (perfData) => {
    if (!perfData || perfData.length === 0) return null;

    const cpus = perfData.map(p => p.cpu_percent).filter(c => c != null);
    const mems = perfData.map(p => p.memory_percent).filter(m => m != null);
    const loads = perfData.map(p => p.load_avg_1).filter(l => l != null);

    return {
      cpu_avg: cpus.length ? (cpus.reduce((a, b) => a + b, 0) / cpus.length).toFixed(1) : 0,
      cpu_max: cpus.length ? Math.max(...cpus).toFixed(1) : 0,
      memory_avg: mems.length ? (mems.reduce((a, b) => a + b, 0) / mems.length).toFixed(1) : 0,
      memory_max: mems.length ? Math.max(...mems).toFixed(1) : 0,
      load_max: loads.length ? Math.max(...loads).toFixed(2) : 0
    };
  };

  const handleExport = async (taskId) => {
    try {
      const res = await reportsAPI.exportReport(taskId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${taskId}.html`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '计划ID', dataIndex: 'plan_id', width: 80 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (s) => {
        const colors = { success: 'green', failed: 'red', running: 'blue', pending: 'gold' };
        return <span style={{ color: colors[s] }}>{s}</span>;
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
      width: 150,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleViewReport(record)} icon={<ThunderboltOutlined />}>
            报告
          </Button>
          <Button size="small" icon={<DownloadOutlined />} onClick={() => handleExport(record.id)}>
            导出
          </Button>
        </Space>
      ),
    },
  ];

  const resultColumns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用例ID', dataIndex: 'case_id', width: 80 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (s) => {
        const colors = { passed: 'green', failed: 'red', error: 'orange' };
        return <span style={{ color: colors[s] }}>{s}</span>;
      },
    },
    { title: '耗时', dataIndex: 'duration', render: (d) => d ? `${d.toFixed(2)}s` : '-' },
    { title: '性能汇总', width: 150, render: (_, r) => r.perf_summary ? '有' : '-' },
  ];

  const tabItems = taskReport ? [
    {
      key: 'summary',
      label: '执行结果',
      children: (
        <Table
          dataSource={taskReport.results}
          columns={resultColumns}
          rowKey="id"
          size="small"
          pagination={false}
        />
      ),
    },
    {
      key: 'performance',
      label: '性能数据',
      children: (
        taskReport.performance?.total?.length > 0 ? (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={4}>
                <Card><Statistic title="CPU 均值" value={calcPerfSummary(taskReport.performance.total)?.cpu_avg || 0} suffix="%" /></Card>
              </Col>
              <Col span={4}>
                <Card><Statistic title="CPU 峰值" value={calcPerfSummary(taskReport.performance.total)?.cpu_max || 0} suffix="%" /></Card>
              </Col>
              <Col span={4}>
                <Card><Statistic title="内存均值" value={calcPerfSummary(taskReport.performance.total)?.memory_avg || 0} suffix="%" /></Card>
              </Col>
              <Col span={4}>
                <Card><Statistic title="内存峰值" value={calcPerfSummary(taskReport.performance.total)?.memory_max || 0} suffix="%" /></Card>
              </Col>
              <Col span={4}>
                <Card><Statistic title="负载峰值" value={calcPerfSummary(taskReport.performance.total)?.load_max || 0} /></Card>
              </Col>
            </Row>
            <ReactECharts option={getPerfChartOption(taskReport.performance.total)} style={{ height: 300 }} />
          </div>
        ) : (
          <Empty description="暂无性能数据（串行执行时才会采集）" />
        )
      ),
    },
  ] : [];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>报告中心</h2>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="今日成功" value={summary.today.success || 0} prefix={<CheckCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="今日失败" value={summary.today.failed || 0} prefix={<CloseCircleOutlined />} valueStyle={{ color: '#ff4d4f' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="今日运行" value={(summary.today.running || 0) + (summary.today.pending || 0)} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="总计" value={summary.today.success + summary.today.failed + summary.today.running + summary.today.pending + summary.today.cancelled || 0} /></Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={16}>
          <Card>
            <Space style={{ marginBottom: 16 }}>
              <Select value={trendType} onChange={setTrendType} style={{ width: 120 }}>
                <Select.Option value="pass_rate">通过率</Select.Option>
                <Select.Option value="total">执行数量</Select.Option>
                <Select.Option value="passed">通过数量</Select.Option>
              </Select>
            </Space>
            <ReactECharts option={getTrendOption()} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="最近任务" extra={<Button size="small" onClick={() => navigate('/tasks')}>更多</Button>}>
            <Table
              dataSource={recentTasks}
              columns={columns}
              rowKey="id"
              size="small"
              pagination={false}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Modal
        title={`任务报告 #${selectedTask?.id}`}
        open={reportModalVisible}
        onCancel={() => setReportModalVisible(false)}
        footer={null}
        width={900}
      >
        {reportLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : taskReport ? (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Card size="small">
                  <Statistic title="通过" value={taskReport.summary?.passed || 0} valueStyle={{ color: '#52c41a' }} />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic title="失败" value={taskReport.summary?.failed || 0} valueStyle={{ color: '#ff4d4f' }} />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic title="错误" value={taskReport.summary?.error || 0} valueStyle={{ color: '#faad14' }} />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic title="耗时" value={selectedTask?.duration ? selectedTask.duration.toFixed(1) : '-'} suffix="秒" />
                </Card>
              </Col>
            </Row>
            <Tabs items={tabItems} />
          </>
        ) : (
          <Empty description="无法加载报告数据" />
        )}
      </Modal>
    </div>
  );
}