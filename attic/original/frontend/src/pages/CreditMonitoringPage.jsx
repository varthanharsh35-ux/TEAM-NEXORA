import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { CreditCard, TrendingUp, Shield, CheckCircle, Info, AlertCircle } from 'lucide-react';

const creditTips = [
  { icon: CheckCircle, text: 'Pay recurring EMIs 3 days before due date to avoid score penalties', type: 'success' },
  { icon: TrendingUp, text: 'Maintain a credit utilization ratio strictly below 30% of limits', type: 'info' },
  { icon: Shield, text: 'Avoid applying for multiple bank loans at the exact same time', type: 'warning' },
  { icon: Info, text: 'Maintain digital transaction proofs via UPI/Bank statement for proof of turnover', type: 'info' },
  { icon: CheckCircle, text: 'Prompt repayment under PM SVANidhi unlocks higher second-tranche credit', type: 'success' },
];

const containerVariants = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

export default function CreditMonitoringPage() {
  const { t } = useTranslation();
  const [score, setScore] = useState(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_cibil');
      return saved ? Number(saved) : 720;
    } catch {
      return 720;
    }
  });

  const [loans, setLoans] = useState(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_loans');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const maxScore = 900;
  const percentage = (score / maxScore) * 100;

  const handleScoreChange = (newScore) => {
    setScore(newScore);
    localStorage.setItem('gramsahayak_cibil', String(newScore));
  };

  const getScoreLabel = (s) => {
    if (s >= 750) return { label: t('credit.excellent'), color: 'text-success-400', bg: 'bg-success-500' };
    if (s >= 650) return { label: t('credit.good'), color: 'text-primary-400', bg: 'bg-primary-500' };
    if (s >= 550) return { label: t('credit.fair'), color: 'text-warning-400', bg: 'bg-warning-500' };
    return { label: t('credit.poor'), color: 'text-danger-400', bg: 'bg-danger-500' };
  };

  const scoreInfo = getScoreLabel(score);

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="max-w-6xl mx-auto space-y-6">
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">{t('credit.title')}</h1>
        <p className="text-white/40">Monitor and optimize your business creditworthiness for bank loans</p>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Credit Score Gauge */}
        <motion.div variants={itemVariants}>
          <div className="glass-card-static p-8 text-center">
            <h3 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-4">
              {t('credit.score')}
            </h3>

            {/* Score Gauge */}
            <div className="relative mx-auto mb-4" style={{ width: 200, height: 120 }}>
              <svg width="200" height="120" viewBox="0 0 200 120">
                <path
                  d="M 20 110 A 80 80 0 0 1 180 110"
                  fill="none"
                  stroke="rgba(255,255,255,0.05)"
                  strokeWidth="14"
                  strokeLinecap="round"
                />
                <path
                  d="M 20 110 A 80 80 0 0 1 180 110"
                  fill="none"
                  stroke="url(#scoreGradient)"
                  strokeWidth="14"
                  strokeLinecap="round"
                  strokeDasharray={`${percentage * 2.51} 251`}
                />
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#ef4444" />
                    <stop offset="33%" stopColor="#f59e0b" />
                    <stop offset="66%" stopColor="#3b5bdb" />
                    <stop offset="100%" stopColor="#10b981" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
                <p className="text-4xl font-black text-white">{score}</p>
                <p className="text-xs text-white/40">of {maxScore}</p>
              </div>
            </div>

            <div className="mb-4">
              <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${scoreInfo.bg}/10 ${scoreInfo.color} text-sm font-semibold`}>
                <Shield size={14} />
                {scoreInfo.label}
              </span>
            </div>

            <div className="pt-2 border-t border-white/5">
              <label className="text-xs text-white/40 block mb-2">Adjust Score / Self-Reported CIBIL</label>
              <input
                type="range"
                min="300"
                max="900"
                step="5"
                value={score}
                onChange={e => handleScoreChange(Number(e.target.value))}
                className="w-full accent-primary-500"
              />
            </div>
          </div>
        </motion.div>

        {/* Credit Tips */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <div className="glass-card-static p-6 h-full flex flex-col">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Info size={20} className="text-primary-400" />
              {t('credit.tips')}
            </h3>
            <div className="space-y-3 flex-1">
              {creditTips.map((tip, i) => {
                const Icon = tip.icon;
                return (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/2 hover:bg-white/4 transition-colors">
                    <Icon size={18} className={
                      tip.type === 'success' ? 'text-success-400' :
                      tip.type === 'warning' ? 'text-warning-400' : 'text-primary-400'
                    } />
                    <p className="text-sm text-white/70">{tip.text}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Repayment Status */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <CreditCard size={20} className="text-accent-400" />
            {t('credit.repayment_status')}
          </h3>
          {loans.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-white/40 uppercase">Scheme / Facility</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-white/40 uppercase">Principal</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-white/40 uppercase">Repaid</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-white/40 uppercase">Progress</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-white/40 uppercase">Status</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-white/40 uppercase">Next Due</th>
                  </tr>
                </thead>
                <tbody>
                  {loans.map((item, i) => {
                    const repaid = Math.max(0, item.principal - item.remaining);
                    const progress = item.principal > 0 ? (repaid / item.principal) * 100 : 100;
                    return (
                      <tr key={i} className="border-b border-white/3 hover:bg-white/2 transition-colors">
                        <td className="py-3 px-4 text-sm font-medium text-white">{item.name}</td>
                        <td className="py-3 px-4 text-sm text-white/60">₹{Number(item.principal).toLocaleString('en-IN')}</td>
                        <td className="py-3 px-4 text-sm text-white/60">₹{repaid.toLocaleString('en-IN')}</td>
                        <td className="py-3 px-4">
                          <div className="w-24 h-2 bg-white/5 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full bg-success-500"
                              style={{ width: `${Math.min(100, progress)}%` }}
                            />
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            item.status === 'on_track' ? 'bg-success-500/10 text-success-400' :
                            item.status === 'paid' ? 'bg-primary-500/10 text-primary-400' :
                            'bg-danger-500/10 text-danger-400'
                          }`}>
                            {item.status === 'on_track' ? t('debt.on_track') :
                             item.status === 'paid' ? t('debt.paid') : t('debt.overdue')}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-white/40">{item.nextDue || '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center">
              <AlertCircle size={32} className="mx-auto text-white/20 mb-2" />
              <p className="text-xs text-white/40">{t('credit.empty_loans')}</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
