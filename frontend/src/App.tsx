import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import PlaceholderPage from './pages/PlaceholderPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import LibraryPage from './pages/LibraryPage'
import MechanicalPage from './pages/MechanicalPage'
import { NAV_ITEMS } from './navigation'
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/mechanical" element={<MechanicalPage />} />
        {NAV_ITEMS.filter((item) => item.path !== '/projects' && item.path !== '/library' && item.path !== '/mechanical').map((item) => (
          <Route key={item.path} path={item.path}
            element={<PlaceholderPage labelKey={item.labelKey} step={item.step} />} />
        ))}
        <Route path="*" element={<PlaceholderPage labelKey="nav.dashboard" step={12} />} />
      </Route>
    </Routes>
  )
}
