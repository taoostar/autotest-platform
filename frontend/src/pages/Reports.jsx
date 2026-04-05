import { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Select, Space, Button } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, DownloadOutlined
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
      width: 100,
      render: (_, record) => (
        <Button size="small" icon={<DownloadOutlined />} onClick={() => handleExport(record.id)}>
          导出
        </Button>
      ),
    },
  ];

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
    </div>
  );
}