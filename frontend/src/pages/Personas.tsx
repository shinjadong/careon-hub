import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { personasApi } from '../services/api';
import { useState } from 'react';
import './Personas.css';

interface PersonaInfo {
  id: string;
  name: string;
  trust_score: number;
  status: string;
  last_used_at?: string;
  cooldown_until?: string;
  total_sessions: number;
  successful_sessions: number;
  failed_sessions?: number;
  performance_score?: number;
  device_config?: {
    model?: string;
    manufacturer?: string;
    android_id?: string;
  };
  tags?: string[];
}

interface PersonaListResponse {
  items: PersonaInfo[];
  total: number;
  limit: number;
  offset: number;
}

function Personas() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null);

  // Fetch personas list
  const { data, isLoading, error, refetch } = useQuery<PersonaListResponse>({
    queryKey: ['personas', statusFilter],
    queryFn: async () => {
      const params = statusFilter === 'all' ? {} : { status: statusFilter };
      const response = await personasApi.list(params);
      return response.data;
    },
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  // Soul Swap mutation
  const soulSwapMutation = useMutation({
    mutationFn: ({ personaId, apps }: { personaId: string; apps: string[] }) =>
      personasApi.soulSwap(personaId, { apps }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personas'] });
      alert('Soul Swap이 완료되었습니다.');
    },
    onError: (error: any) => {
      alert(`Soul Swap 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleSoulSwap = (personaId: string) => {
    if (confirm(`페르소나 ${personaId}의 Soul Swap을 실행하시겠습니까?`)) {
      soulSwapMutation.mutate({
        personaId,
        apps: ['naver_search', 'naver_blog'],
      });
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'idle':
        return 'status-idle';
      case 'active':
        return 'status-active';
      case 'cooling_down':
        return 'status-cooling';
      case 'banned':
        return 'status-banned';
      default:
        return '';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'idle':
        return '대기';
      case 'active':
        return '활성';
      case 'cooling_down':
        return '쿨다운';
      case 'banned':
        return '차단됨';
      default:
        return status;
    }
  };

  const calculateSuccessRate = (persona: PersonaInfo) => {
    if (persona.total_sessions === 0) return 0;
    return ((persona.successful_sessions / persona.total_sessions) * 100).toFixed(1);
  };

  if (isLoading) {
    return (
      <div className="personas-page">
        <div className="loading">페르소나 목록을 불러오는 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="personas-page">
        <div className="error">
          <h2>에러 발생</h2>
          <p>{(error as Error).message}</p>
          <button onClick={() => refetch()}>다시 시도</button>
        </div>
      </div>
    );
  }

  const personas = data?.items || [];
  const total = data?.total || 0;

  return (
    <div className="personas-page">
      <div className="page-header">
        <h1>페르소나 관리</h1>
        <div className="header-actions">
          <span className="persona-count">총 {total}개 페르소나</span>
          <button onClick={() => refetch()} className="refresh-btn">
            🔄 새로고침
          </button>
        </div>
      </div>

      <div className="filters">
        <label>상태 필터:</label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">전체</option>
          <option value="idle">대기</option>
          <option value="active">활성</option>
          <option value="cooling_down">쿨다운</option>
          <option value="banned">차단됨</option>
        </select>
      </div>

      {personas.length === 0 ? (
        <div className="empty-state">
          <h2>페르소나가 없습니다</h2>
          <p>선택한 필터에 해당하는 페르소나가 없습니다.</p>
        </div>
      ) : (
        <div className="personas-grid">
          {personas.map((persona) => (
            <div
              key={persona.id}
              className={`persona-card ${selectedPersona === persona.id ? 'selected' : ''}`}
              onClick={() => setSelectedPersona(persona.id)}
            >
              <div className="persona-header">
                <h3>{persona.name}</h3>
                <span className={`status-badge ${getStatusBadgeClass(persona.status)}`}>
                  {getStatusText(persona.status)}
                </span>
              </div>

              <div className="persona-stats">
                <div className="stat-item">
                  <span className="stat-label">신뢰도</span>
                  <span className="stat-value trust-score">{persona.trust_score}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">총 세션</span>
                  <span className="stat-value">{persona.total_sessions}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">성공률</span>
                  <span className="stat-value success-rate">
                    {calculateSuccessRate(persona)}%
                  </span>
                </div>
              </div>

              {persona.device_config && (
                <div className="device-info">
                  <div className="info-row">
                    <span className="label">디바이스</span>
                    <span className="value">
                      {persona.device_config.manufacturer} {persona.device_config.model}
                    </span>
                  </div>
                  {persona.device_config.android_id && (
                    <div className="info-row">
                      <span className="label">Android ID</span>
                      <span className="value mono">
                        {persona.device_config.android_id.substring(0, 8)}...
                      </span>
                    </div>
                  )}
                </div>
              )}

              {persona.tags && persona.tags.length > 0 && (
                <div className="tags">
                  {persona.tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <div className="persona-actions">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSoulSwap(persona.id);
                  }}
                  className="action-btn soul-swap"
                  disabled={
                    soulSwapMutation.isPending ||
                    persona.status === 'banned' ||
                    persona.status === 'cooling_down'
                  }
                >
                  🔄 Soul Swap
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    alert('세션 상세보기 기능은 준비 중입니다.');
                  }}
                  className="action-btn sessions"
                >
                  📊 세션 보기
                </button>
              </div>

              {persona.cooldown_until && (
                <div className="cooldown-info">
                  ⏱️ 쿨다운: {new Date(persona.cooldown_until).toLocaleString('ko-KR')}까지
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="auto-refresh-info">
        ℹ️ 페르소나 목록은 15초마다 자동으로 새로고침됩니다.
      </div>
    </div>
  );
}

export default Personas;
