export default function KpiCard({ label, value, change, up }) {
  return (
    <div style={{
      background: '#1e293b',
      borderRadius: '12px',
      padding: '24px',
      border: '1px solid #334155',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
    }}>
      <span style={{ fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>
      <span style={{ fontSize: '28px', fontWeight: '700', color: '#f1f5f9' }}>
        {value}
      </span>
      <span style={{ fontSize: '13px', color: up ? '#34d399' : '#f87171', fontWeight: '500' }}>
        {up ? '▲' : '▼'} {change} vs. ano anterior
      </span>
    </div>
  )
}
