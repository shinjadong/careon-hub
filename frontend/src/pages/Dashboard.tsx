import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../services/api';

export default function Dashboard() {
  const { data: health, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.check().then(res => res.data),
    refetchInterval: 5000 // 5초마다 갱신
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error connecting to backend</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h2>CareOn Hub 대시보드</h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '20px',
        marginTop: '20px'
      }}>
        <StatCard title="백엔드 상태" value={health?.status || 'N/A'} />
        <StatCard title="서비스" value={health?.service || 'N/A'} />
        <StatCard title="활성 캠페인" value="0" />
        <StatCard title="페르소나" value="0" />
      </div>

      <div style={{ marginTop: '40px' }}>
        <h3>시스템 상태</h3>
        <pre style={{
          background: '#f4f4f4',
          padding: '15px',
          borderRadius: '5px',
          overflow: 'auto'
        }}>
          {JSON.stringify(health, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div style={{
      background: 'white',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '20px',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
        {title}
      </div>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>
        {value}
      </div>
    </div>
  );
}
