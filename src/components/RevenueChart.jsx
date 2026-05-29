import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { revenueData } from '../data/mockData'

const formatBRL = (v) => `R$ ${(v / 1000).toFixed(0)}k`

export default function RevenueChart() {
  return (
    <div style={{
      background: '#1e293b',
      borderRadius: '12px',
      padding: '24px',
      border: '1px solid #334155',
    }}>
      <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#f1f5f9', marginBottom: '24px' }}>
        Receita, Despesas e Lucro — 2025
      </h2>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={revenueData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="mes" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={formatBRL} tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip
            formatter={(v, name) => [formatBRL(v), name.charAt(0).toUpperCase() + name.slice(1)]}
            contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
            labelStyle={{ color: '#f1f5f9' }}
          />
          <Legend wrapperStyle={{ paddingTop: '16px', fontSize: '13px' }} />
          <Line type="monotone" dataKey="receita" stroke="#60a5fa" strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
          <Line type="monotone" dataKey="despesas" stroke="#f87171" strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
          <Line type="monotone" dataKey="lucro" stroke="#34d399" strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
