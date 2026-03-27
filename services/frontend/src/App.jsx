import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useStore } from './store/useStore'
import { Navbar } from './components/ui'
import Landing from './pages/Landing'
import { Login, Register } from './pages/Auth'
import SearchPage from './pages/Search'
import ProfilePage from './pages/Profile'
import TokensPage from './pages/Tokens'
import GigsPage from './pages/Gigs'

function RequireAuth({ children }) {
  const { isAuthenticated } = useStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/"         element={<Landing />} />
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/search"   element={<RequireAuth><SearchPage /></RequireAuth>} />
        <Route path="/profile"  element={<RequireAuth><ProfilePage /></RequireAuth>} />
        <Route path="/tokens"   element={<RequireAuth><TokensPage /></RequireAuth>} />
        <Route path="/gigs"     element={<RequireAuth><GigsPage /></RequireAuth>} />
        <Route path="*"         element={<Navigate to="/" replace />} />
      </Routes>

      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#16161f',
            color: '#f0f0f8',
            border: '1px solid #22222e',
            fontFamily: 'Manrope, sans-serif',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: '#00e5a0', secondary: '#0a0a0f' } },
          error:   { iconTheme: { primary: '#ff6b6b', secondary: '#0a0a0f' } },
        }}
      />
    </BrowserRouter>
  )
}
