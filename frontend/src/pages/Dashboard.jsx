import { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, List, Tag, Table } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useNavigate } from 'react-router-dom';
import { reportsAPI, tasksAPI, agentsAPI } from '../services/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState({ today: {}, trend: [] });
  const [recentTasks, setRecentTasks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, tasksRes, agentsRes] = await Promise.all([
        reportsAPI.getSummary({ days: 7 }),
        tasksAPI.list({ page_size: 5 }),
        agentsAPI.list(),
      ]);

      setSummary(summaryRes.data);
      setRecentTasks(tasksRes.data.tasks || []);
      setAgents(agentsRes.data || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTrendOption = () => {
    const trend = summary.trend || [];
    return {
      title: { text: '7天通过率趋势', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: trend.map((t) => t.date?.slice(5) || ''),
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { formatter: '{value}%' },
      },
      series: [
        {
          data: trend.map((t) => t.pass_rate || 0),
          type: 'line',
          smooth: true,
          areaStyle: { color: 'rgba(102, 126, 234, 0.3)' },
          lineStyle: { color: '#667eea' },
          itemStyle: { color: '#667eea' },
        },
      ],
      grid: { left: 50, right: 20, top: 40, bottom: 30 },
    };
  };

  const getStatusTag = (status) => {
    const statusMap = {
      success: { color: 'green', text: '成功' },
      failed: { color: 'red', text: '失败' },
      running: { color: 'blue', text: '运行中' },
      pending: { color: 'gold', text: '等待中' },
      cancelled: { color: 'default', text: '已取消' },
    };
    const { color, text } = statusMap[status] || { color: 'default', text: status };
    return <Tag color={color}>{text}</Tag>;
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '计划ID', dataIndex: 'plan_id', width: 80 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status) => getStatusTag(status),
    },
    { title: '触发方式', dataIndex: 'trigger_type', width: 100 },
    {
      title: '耗时',
      dataIndex: 'duration',
      width: 100,
      render: (d) => (d ? `${d.toFixed(1)}s` : '-'),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>仪表盘</h2>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日成功"
              value={summary.today.success || 0}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日失败"
              value={summary.today.failed || 0}
              prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="运行中"
              value={summary.today.running || 0}
              prefix={<SyncOutlined spin style={{ color: '#1677ff' }} />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Agent在线"
              value={`${agents.filter((a) => a.status === 'online').length}/${agents.length}`}
              prefix={<RobotOutlined style={{ color: '#667eea' }} />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="通过率趋势">
            <ReactECharts option={getTrendOption()} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title="最近任务"
            extra={<a onClick={() => navigate('/tasks')}>查看更多</a>}
          >
            <Table
              dataSource={recentTasks}
              columns={columns}
              rowKey="id"
              size="small"
              pagination={false}
              onRow={(record) => ({
                onClick: () => navigate(`/tasks/${record.id}`),
                style: { cursor: 'pointer' },
              })}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}