import KpiCard from './components/KpiCard'
import RevenueChart from './components/RevenueChart'
import { kpis } from './data/mockData'

export default function App() {
  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#f1f5f9' }}>
          Analytics Dashboard
        </h1>
        <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>
          Resultados financeiros · 2025
        </p>
      </header>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '24px',
      }}>
        {kpis.map((kpi) => (
          <KpiCard key={kpi.label} {...kpi} />
        ))}
      </div>

      <RevenueChart />
    </div>
  )
}
