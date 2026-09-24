import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import {
  Plus, BarChart3, ArrowLeftRight, Building2,
  TrendingUp, Clock, Activity, Sparkles, AlertCircle, ArrowRight
} from 'lucide-react';

const quickActions = [
  { to: '/assessment', icon: Plus, labelKey: 'dashboard.new_assessment', gradient: 'from-blue-500 to-purple-600' },
  { to: '/feasibility', icon: BarChart3, labelKey: 'dashboard.view_reports', gradient: 'from-emerald-500 to-teal-600' },
  { to: '/cashflow', icon: ArrowLeftRight, labelKey: 'dashboard.cash_flow', gradient: 'from-orange-500 to-amber-600' },
  { to: '/schemes', icon: Building2, labelKey: 'dashboard.schemes', gradient: 'from-rose-500 to-pink-600' },
];

const containerVariants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [assessment, setAssessment] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loans, setLoans] = useState([]);

  useEffect(() => {
    try {
      const savedAssessment = localStorage.getItem('gramsahayak_assessment');
      if (savedAssessment) setAssessment(JSON.parse(savedAssessment));

      const savedTx = localStorage.getItem('gramsahayak_transactions');
      if (savedTx) setTransactions(JSON.parse(savedTx));

      const savedLoans = localStorage.getItem('gramsahayak_loans');
      if (savedLoans) setLoans(JSON.parse(savedLoans));
    } catch (e) {
      console.error('Error loading dashboard state:', e);
    }
  }, []);

  const totalIn = transactions.filter(t => t.type === 'in').reduce((s, t) => s + Number(t.amount || 0), 0);
  const totalOut = transactions.filter(t => t.type === 'out').reduce((s, t) => s + Number(t.amount || 0), 0);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="max-w-6xl mx-auto space-y-6"
    >
      {/* Greeting */}
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">
          {t('dashboard.greeting')}, {user?.displayName || 'Entrepreneur'} 👋
        </h1>
        <p className="text-white/40">
          {assessment?.businessName
            ? `${assessment.businessName} — ${assessment.location || 'Location Set'}`
            : 'Welcome to your real-time rural enterprise advisory platform'}
        </p>
      </motion.div>

      {/* Quick Actions */}
      <motion.div variants={itemVariants}>
        <h2 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-4">
          {t('dashboard.quick_actions')}
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, i) => {
            const Icon = action.icon;
            return (
              <Link key={i} to={action.to}>
                <div className="glass-card p-6 text-center group cursor-pointer h-full flex flex-col items-center justify-center">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${action.gradient} flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform shadow-lg`}>
                    <Icon size={24} className="text-white" />
                  </div>
                  <p className="text-sm font-semibold text-white/80 group-hover:text-white transition-colors">
                    {t(action.labelKey)}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Business Health & Feasibility */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <div className="glass-card-static p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Activity size={20} className="text-primary-400" />
                {t('dashboard.business_health')}
              </h2>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                assessment ? 'bg-success-500/10 text-success-400' : 'bg-white/10 text-white/60'
              }`}>
                {assessment ? t('dashboard.active_status') : t('dashboard.empty_feasibility')}
              </span>
            </div>

            {/* Health Cards */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 rounded-xl bg-white/3 border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp size={16} className="text-success-400" />
                  <span className="text-xs text-white/40">Feasibility</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {assessment?.feasibilityScore != null ? (
                    <>{assessment.feasibilityScore}<span className="text-sm text-white/40">/100</span></>
                  ) : (
                    <span className="text-base text-white/40">{t('dashboard.empty_feasibility')}</span>
                  )}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/3 border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles size={16} className="text-accent-400" />
                  <span className="text-xs text-white/40">Schemes</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {assessment?.matchedSchemes?.length ? (
                    <>{assessment.matchedSchemes.length}<span className="text-sm text-white/40"> matched</span></>
                  ) : (
                    <span className="text-base text-white/40">7 Active</span>
                  )}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/3 border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 size={16} className="text-primary-400" />
                  <span className="text-xs text-white/40">Cashflow</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {transactions.length > 0 ? (
                    `₹${Math.max(0, totalIn - totalOut).toLocaleString('en-IN')}`
                  ) : (
                    <span className="text-base text-white/40">₹0</span>
                  )}
                </p>
              </div>
            </div>

            {assessment ? (
              <Link to="/feasibility" className="btn btn-sm btn-outline w-full flex items-center justify-center gap-2">
                <span>{t('dashboard.view_reports')}</span>
                <ArrowRight size={14} />
              </Link>
            ) : (
              <Link to="/assessment" className="btn btn-sm btn-primary w-full flex items-center justify-center gap-2">
                <span>{t('dashboard.start_assessment_cta')}</span>
                <ArrowRight size={14} />
              </Link>
            )}
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div variants={itemVariants}>
          <div className="glass-card-static p-6 h-full flex flex-col">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
              <Clock size={20} className="text-accent-400" />
              {t('dashboard.recent_activity')}
            </h2>
            
            {assessment || transactions.length > 0 || loans.length > 0 ? (
              <div className="space-y-3 flex-1">
                {assessment && (
                  <div className="flex gap-3 p-3 rounded-xl bg-white/2 border border-white/5">
                    <div className="w-2 h-2 rounded-full mt-2 flex-shrink-0 bg-success-400" />
                    <div className="min-w-0">
                      <p className="text-sm text-white/80 font-medium truncate">Feasibility Assessment</p>
                      <p className="text-xs text-white/40 truncate">{assessment.businessName} ({assessment.category})</p>
                      <p className="text-xs text-white/25 mt-1">Score: {assessment.feasibilityScore || 'Pending'}/100</p>
                    </div>
                  </div>
                )}
                {transactions.slice(0, 2).map((tx, idx) => (
                  <div key={idx} className="flex gap-3 p-3 rounded-xl bg-white/2 border border-white/5">
                    <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${tx.type === 'in' ? 'bg-success-400' : 'bg-danger-400'}`} />
                    <div className="min-w-0">
                      <p className="text-sm text-white/80 font-medium truncate">{tx.description || tx.category}</p>
                      <p className="text-xs text-white/40 truncate">{tx.type === 'in' ? '+' : '-'}₹{Number(tx.amount).toLocaleString('en-IN')}</p>
                      <p className="text-xs text-white/25 mt-1">{tx.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center py-6">
                <AlertCircle size={32} className="text-white/20 mb-2" />
                <p className="text-xs text-white/40 max-w-xs">{t('dashboard.no_recent_activity')}</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
