import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { campaignsApi } from '../services/api';
import { useState } from 'react';
import './Campaigns.css';

interface CampaignInfo {
  id: string;
  name: string;
  description?: string;
  keyword: string;
  target_blog_url: string;
  read_time_seconds: number;
  status: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  created_at: string;
  updated_at: string;
}

interface CampaignListResponse {
  items: CampaignInfo[];
  total: number;
  limit: number;
  offset: number;
}

interface CampaignStats {
  campaign_id: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  average_duration_seconds: number;
  total_traffic_volume: number;
  success_rate: number;
}

function Campaigns() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    description: '',
    keyword: '',
    target_blog_url: '',
    read_time_seconds: 120,
  });

  // Fetch campaigns list
  const { data, isLoading, error, refetch } = useQuery<CampaignListResponse>({
    queryKey: ['campaigns', statusFilter],
    queryFn: async () => {
      const params = statusFilter === 'all' ? {} : { status: statusFilter };
      const response = await campaignsApi.list(params);
      return response.data;
    },
    refetchInterval: 20000, // Refresh every 20 seconds
  });

  // Fetch campaign stats
  const { data: statsData } = useQuery<CampaignStats>({
    queryKey: ['campaign-stats', selectedCampaign],
    queryFn: async () => {
      if (!selectedCampaign) return null;
      const response = await campaignsApi.stats(selectedCampaign);
      return response.data;
    },
    enabled: !!selectedCampaign,
  });

  // Create campaign mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newCampaign) => campaignsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setShowCreateForm(false);
      setNewCampaign({
        name: '',
        description: '',
        keyword: '',
        target_blog_url: '',
        read_time_seconds: 120,
      });
      alert('캠페인이 생성되었습니다.');
    },
    onError: (error: any) => {
      alert(`캠페인 생성 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Execute campaign mutation
  const executeMutation = useMutation({
    mutationFn: ({ campaignId, personaCount }: { campaignId: string; personaCount: number }) =>
      campaignsApi.execute({ campaign_id: campaignId, persona_count: personaCount }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      alert('캠페인 실행이 시작되었습니다.');
    },
    onError: (error: any) => {
      alert(`캠페인 실행 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleCreateCampaign = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(newCampaign);
  };

  const handleExecuteCampaign = (campaignId: string) => {
    const personaCount = parseInt(
      prompt('사용할 페르소나 수를 입력하세요:', '1') || '0'
    );
    if (personaCount > 0) {
      executeMutation.mutate({ campaignId, personaCount });
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'status-active';
      case 'paused':
        return 'status-paused';
      case 'completed':
        return 'status-completed';
      default:
        return '';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '활성';
      case 'paused':
        return '일시정지';
      case 'completed':
        return '완료';
      default:
        return status;
    }
  };

  const calculateSuccessRate = (campaign: CampaignInfo) => {
    if (campaign.total_executions === 0) return 0;
    return ((campaign.successful_executions / campaign.total_executions) * 100).toFixed(1);
  };

  if (isLoading) {
    return (
      <div className="campaigns-page">
        <div className="loading">캠페인 목록을 불러오는 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="campaigns-page">
        <div className="error">
          <h2>에러 발생</h2>
          <p>{(error as Error).message}</p>
          <button onClick={() => refetch()}>다시 시도</button>
        </div>
      </div>
    );
  }

  const campaigns = data?.items || [];
  const total = data?.total || 0;

  return (
    <div className="campaigns-page">
      <div className="page-header">
        <h1>캠페인 관리</h1>
        <div className="header-actions">
          <span className="campaign-count">총 {total}개 캠페인</span>
          <button onClick={() => setShowCreateForm(!showCreateForm)} className="create-btn">
            ➕ 새 캠페인
          </button>
          <button onClick={() => refetch()} className="refresh-btn">
            🔄 새로고침
          </button>
        </div>
      </div>

      {showCreateForm && (
        <div className="create-form-modal">
          <div className="modal-content">
            <h2>새 캠페인 생성</h2>
            <form onSubmit={handleCreateCampaign}>
              <div className="form-group">
                <label>캠페인 이름</label>
                <input
                  type="text"
                  value={newCampaign.name}
                  onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
                  required
                  placeholder="예: CCTV 설치 캠페인"
                />
              </div>
              <div className="form-group">
                <label>설명</label>
                <textarea
                  value={newCampaign.description}
                  onChange={(e) =>
                    setNewCampaign({ ...newCampaign, description: e.target.value })
                  }
                  placeholder="캠페인 설명 (선택)"
                />
              </div>
              <div className="form-group">
                <label>키워드</label>
                <input
                  type="text"
                  value={newCampaign.keyword}
                  onChange={(e) => setNewCampaign({ ...newCampaign, keyword: e.target.value })}
                  required
                  placeholder="예: CCTV 설치"
                />
              </div>
              <div className="form-group">
                <label>타겟 블로그 URL</label>
                <input
                  type="url"
                  value={newCampaign.target_blog_url}
                  onChange={(e) =>
                    setNewCampaign({ ...newCampaign, target_blog_url: e.target.value })
                  }
                  required
                  placeholder="https://blog.naver.com/..."
                />
              </div>
              <div className="form-group">
                <label>체류 시간 (초)</label>
                <input
                  type="number"
                  value={newCampaign.read_time_seconds}
                  onChange={(e) =>
                    setNewCampaign({ ...newCampaign, read_time_seconds: parseInt(e.target.value) })
                  }
                  min="30"
                  max="600"
                  required
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="submit-btn" disabled={createMutation.isPending}>
                  {createMutation.isPending ? '생성 중...' : '생성'}
                </button>
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={() => setShowCreateForm(false)}
                >
                  취소
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="filters">
        <label>상태 필터:</label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">전체</option>
          <option value="active">활성</option>
          <option value="paused">일시정지</option>
          <option value="completed">완료</option>
        </select>
      </div>

      {campaigns.length === 0 ? (
        <div className="empty-state">
          <h2>캠페인이 없습니다</h2>
          <p>새 캠페인을 생성하여 트래픽 자동화를 시작하세요.</p>
          <button onClick={() => setShowCreateForm(true)} className="create-btn-large">
            ➕ 첫 캠페인 생성하기
          </button>
        </div>
      ) : (
        <div className="campaigns-grid">
          {campaigns.map((campaign) => (
            <div
              key={campaign.id}
              className={`campaign-card ${selectedCampaign === campaign.id ? 'selected' : ''}`}
              onClick={() => setSelectedCampaign(campaign.id)}
            >
              <div className="campaign-header">
                <h3>{campaign.name}</h3>
                <span className={`status-badge ${getStatusBadgeClass(campaign.status)}`}>
                  {getStatusText(campaign.status)}
                </span>
              </div>

              {campaign.description && (
                <p className="campaign-description">{campaign.description}</p>
              )}

              <div className="campaign-info">
                <div className="info-row">
                  <span className="label">키워드</span>
                  <span className="value keyword">{campaign.keyword}</span>
                </div>
                <div className="info-row">
                  <span className="label">타겟 URL</span>
                  <span className="value url">{campaign.target_blog_url}</span>
                </div>
                <div className="info-row">
                  <span className="label">체류 시간</span>
                  <span className="value">{campaign.read_time_seconds}초</span>
                </div>
              </div>

              <div className="campaign-stats">
                <div className="stat-item">
                  <span className="stat-label">총 실행</span>
                  <span className="stat-value">{campaign.total_executions}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">성공</span>
                  <span className="stat-value success">{campaign.successful_executions}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">성공률</span>
                  <span className="stat-value rate">{calculateSuccessRate(campaign)}%</span>
                </div>
              </div>

              <div className="campaign-actions">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleExecuteCampaign(campaign.id);
                  }}
                  className="action-btn execute"
                  disabled={executeMutation.isPending || campaign.status !== 'active'}
                >
                  ▶️ 실행
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedCampaign(campaign.id);
                  }}
                  className="action-btn stats"
                >
                  📊 통계
                </button>
              </div>

              <div className="campaign-meta">
                생성: {new Date(campaign.created_at).toLocaleDateString('ko-KR')}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedCampaign && statsData && (
        <div className="stats-panel">
          <div className="stats-header">
            <h3>캠페인 통계</h3>
            <button onClick={() => setSelectedCampaign(null)} className="close-btn">
              ✕
            </button>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">총 실행 횟수</div>
              <div className="stat-value">{statsData.total_executions}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">성공</div>
              <div className="stat-value success">{statsData.successful_executions}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">실패</div>
              <div className="stat-value fail">{statsData.failed_executions}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">성공률</div>
              <div className="stat-value rate">{statsData.success_rate.toFixed(1)}%</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">평균 시간</div>
              <div className="stat-value">{statsData.average_duration_seconds.toFixed(0)}초</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">총 트래픽</div>
              <div className="stat-value">{statsData.total_traffic_volume}</div>
            </div>
          </div>
        </div>
      )}

      <div className="auto-refresh-info">
        ℹ️ 캠페인 목록은 20초마다 자동으로 새로고침됩니다.
      </div>
    </div>
  );
}

export default Campaigns;
