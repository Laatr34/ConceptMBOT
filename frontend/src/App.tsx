import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import PlaceholderPage from './pages/PlaceholderPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import LibraryPage from './pages/LibraryPage'
import MechanicalPage from './pages/MechanicalPage'
import ElectricalPage from './pages/ElectricalPage'
import MotorizationPage from './pages/MotorizationPage'
import DocumentationPage from './pages/DocumentationPage'
import BatteryPage from './pages/BatteryPage'
import { NAV_ITEMS } from './navigation'
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/mechanical" element={<MechanicalPage />} />
        <Route path="/electrical" element={<ElectricalPage />} />
        <Route path="/power" element={<BatteryPage />} />
        <Route path="/motorization" element={<MotorizationPage />} />
        <Route path="/documentation" element={<DocumentationPage />} />
        {NAV_ITEMS.filter((item) => item.path !== '/projects' && item.path !== '/library' && item.path !== '/mechanical' && item.path !== '/electrical' && item.path !== '/power' && item.path !== '/motorization' && item.path !== '/documentation').map((item) => (
          <Route key={item.path} path={item.path}
            element={<PlaceholderPage labelKey={item.labelKey} step={item.step} />} />
        ))}
        <Route path="*" element={<PlaceholderPage labelKey="nav.dashboard" step={12} />} />
      </Route>
    </Routes>
  )
}
