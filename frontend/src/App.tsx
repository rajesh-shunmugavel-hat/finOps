import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ServiceDrilldown from './pages/ServiceDrilldown'
import Reports from './pages/Reports'
import ReportDetail from './pages/ReportDetail'
import Departments from './pages/Departments'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/services/:serviceName" element={<ServiceDrilldown />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/reports/:reportId" element={<ReportDetail />} />
        <Route path="/departments" element={<Departments />} />
      </Routes>
    </Layout>
  )
}

export default App
