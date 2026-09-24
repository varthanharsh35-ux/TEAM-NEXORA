import React, { Component } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './i18n';

import AppLayout from './layouts/AppLayout';
import AuthLayout from './layouts/AuthLayout';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import ExistingBusinessPage from './pages/ExistingBusinessPage';
import Dashboard from './pages/Dashboard';
import AssessmentPage from './pages/AssessmentPage';
import FeasibilityDashboard from './pages/FeasibilityDashboard';
import FinancialPage from './pages/FinancialPage';
import SchemesPage from './pages/SchemesPage';
import CashFlowPage from './pages/CashFlowPage';
import CreditMonitoringPage from './pages/CreditMonitoringPage';
import DebtManagementPage from './pages/DebtManagementPage';
import ProfilePage from './pages/ProfilePage';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-900 text-white p-6">
          <div className="glass-card max-w-md p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
            <p className="text-white/60 mb-6 text-sm">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="btn btn-primary"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-900">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl gradient-primary flex items-center justify-center animate-pulse-glow">
            <span className="text-white font-bold text-xl">G</span>
          </div>
          <p className="text-white/40 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/existing-business" element={<ExistingBusinessPage />} />
      </Route>

      {/* Protected Routes */}
      <Route element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/assessment" element={<AssessmentPage />} />
        <Route path="/feasibility" element={<FeasibilityDashboard />} />
        <Route path="/financial" element={<FinancialPage />} />
        <Route path="/schemes" element={<SchemesPage />} />
        <Route path="/cashflow" element={<CashFlowPage />} />
        <Route path="/credit" element={<CreditMonitoringPage />} />
        <Route path="/debt" element={<DebtManagementPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
