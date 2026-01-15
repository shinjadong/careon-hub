import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { devicesApi } from '../services/api';
import { useState } from 'react';
import './Devices.css';

interface DeviceInfo {
  device_id: string;
  model: string;
  manufacturer: string;
  android_version: string;
  status: string;
  battery_level?: number;
  sdk_version?: number;
}

interface DeviceListResponse {
  devices: DeviceInfo[];
  total: number;
}

function Devices() {
  const queryClient = useQueryClient();
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);

  // Fetch devices list (auto-refresh every 10 seconds)
  const { data, isLoading, error, refetch } = useQuery<DeviceListResponse>({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await devicesApi.list();
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Reboot device mutation
  const rebootMutation = useMutation({
    mutationFn: (deviceId: string) => devicesApi.reboot(deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      alert('기기 재부팅 명령이 전송되었습니다.');
    },
    onError: (error: any) => {
      alert(`재부팅 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleReboot = (deviceId: string) => {
    if (confirm(`기기 ${deviceId}를 재부팅하시겠습니까?`)) {
      rebootMutation.mutate(deviceId);
    }
  };

  if (isLoading) {
    return (
      <div className="devices-page">
        <div className="loading">디바이스 목록을 불러오는 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="devices-page">
        <div className="error">
          <h2>에러 발생</h2>
          <p>{(error as Error).message}</p>
          <button onClick={() => refetch()}>다시 시도</button>
        </div>
      </div>
    );
  }

  const devices = data?.devices || [];
  const total = data?.total || 0;

  return (
    <div className="devices-page">
      <div className="page-header">
        <h1>연결된 디바이스</h1>
        <div className="header-actions">
          <span className="device-count">총 {total}개 디바이스</span>
          <button onClick={() => refetch()} className="refresh-btn">
            🔄 새로고침
          </button>
        </div>
      </div>

      {devices.length === 0 ? (
        <div className="empty-state">
          <h2>연결된 디바이스가 없습니다</h2>
          <p>ADB를 통해 디바이스를 연결해주세요.</p>
          <pre>adb devices</pre>
        </div>
      ) : (
        <div className="devices-grid">
          {devices.map((device) => (
            <div
              key={device.device_id}
              className={`device-card ${selectedDevice === device.device_id ? 'selected' : ''}`}
              onClick={() => setSelectedDevice(device.device_id)}
            >
              <div className="device-header">
                <h3>{device.model}</h3>
                <span className={`status-badge ${device.status}`}>
                  {device.status === 'connected' ? '연결됨' : device.status}
                </span>
              </div>

              <div className="device-info">
                <div className="info-row">
                  <span className="label">제조사</span>
                  <span className="value">{device.manufacturer}</span>
                </div>
                <div className="info-row">
                  <span className="label">Device ID</span>
                  <span className="value mono">{device.device_id}</span>
                </div>
                <div className="info-row">
                  <span className="label">Android</span>
                  <span className="value">
                    {device.android_version}
                    {device.sdk_version && ` (SDK ${device.sdk_version})`}
                  </span>
                </div>
                {device.battery_level !== undefined && device.battery_level !== null && (
                  <div className="info-row">
                    <span className="label">배터리</span>
                    <span className="value">{device.battery_level}%</span>
                  </div>
                )}
              </div>

              <div className="device-actions">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleReboot(device.device_id);
                  }}
                  className="action-btn reboot"
                  disabled={rebootMutation.isPending}
                >
                  🔄 재부팅
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    alert('스크린샷 기능은 준비 중입니다.');
                  }}
                  className="action-btn screenshot"
                >
                  📸 스크린샷
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="auto-refresh-info">
        ℹ️ 디바이스 목록은 10초마다 자동으로 새로고침됩니다.
      </div>
    </div>
  );
}

export default Devices;
