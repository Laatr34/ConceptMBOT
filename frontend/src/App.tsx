import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import PlaceholderPage from './pages/PlaceholderPage'
import { NAV_ITEMS } from './navigation'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {NAV_ITEMS.map((item) => (
          <Route
            key={item.path}
            path={item.path}
            element={<PlaceholderPage labelKey={item.labelKey} step={item.step} />}
          />
        ))}
      </Route>
    </Routes>
  )
}
