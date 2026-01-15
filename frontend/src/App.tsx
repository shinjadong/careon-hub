import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="app">
          <nav className="navbar">
            <h1>CareOn Hub</h1>
            <div className="nav-links">
              <Link to="/">Dashboard</Link>
              <Link to="/campaigns">Campaigns</Link>
              <Link to="/personas">Personas</Link>
              <Link to="/devices">Devices</Link>
            </div>
          </nav>
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/campaigns" element={<div>Campaigns (Coming Soon)</div>} />
              <Route path="/personas" element={<div>Personas (Coming Soon)</div>} />
              <Route path="/devices" element={<div>Devices (Coming Soon)</div>} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
