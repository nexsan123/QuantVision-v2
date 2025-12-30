import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import FactorLab from './pages/FactorLab'
import StrategyBuilder from './pages/StrategyBuilder'
import BacktestCenter from './pages/BacktestCenter'
import Trading from './pages/Trading'
import RiskCenter from './pages/RiskCenter'

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="factor-lab" element={<FactorLab />} />
        <Route path="strategy" element={<StrategyBuilder />} />
        <Route path="backtest" element={<BacktestCenter />} />
        <Route path="trading" element={<Trading />} />
        <Route path="risk" element={<RiskCenter />} />
      </Route>
    </Routes>
  )
}

export default App
