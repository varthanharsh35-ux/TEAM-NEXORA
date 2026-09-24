import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import AIAssistant from '../components/AIAssistant';

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-surface-900">
      <Navbar />
      <div className="flex pt-16">
        <Sidebar />
        <main className="flex-1 min-h-[calc(100vh-64px)] p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
      <AIAssistant />
    </div>
  );
}
