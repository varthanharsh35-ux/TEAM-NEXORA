import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts';
import { Wallet, TrendingUp, Clock, IndianRupee, ShieldCheck } from 'lucide-react';

const containerVariants = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

export default function FinancialPage() {
  const { t } = useTranslation();
  const [investment, setInvestment] = useState(200000);
  const [businessType, setBusinessType] = useState('retail');
  const [viewMode, setViewMode] = useState('monthly');
  const [plan, setPlan] = useState(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_assessment');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.investment || parsed.initialCapital) {
          setInvestment(Number(parsed.investment || parsed.initialCapital));
        }
        if (parsed.category || parsed.businessType) {
          setBusinessType(parsed.category || parsed.businessType);
        }
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    async function fetchPlan() {
      try {
        const res = await fetch('http://127.0.0.1:8000/financial/plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            investmentAmount: investment,
            businessType: businessType
          })
        });
        if (res.ok) {
          const data = await res.json();
          setPlan(data);
        }
      } catch (err) {
        console.warn('Financial plan API fallback:', err);
      }
    }
    fetchPlan();
  }, [investment, businessType]);

  const setupCost = plan?.averageSetupCost || Math.round(investment * 0.7);
  const minCapital = plan?.bareMinimumCapital || Math.round(investment * 0.4);
  const establishedCapital = plan?.establishedCapital || Math.round(investment * 1.5);
  const breakEven = plan?.breakEvenMonths || Math.round(8 + (investment / 500000) * 4);

  const recurring = plan?.monthlyRecurring || {
    rent: Math.round(investment * 0.02),
    inventory: Math.round(investment * 0.08),
    staff: Math.round(investment * 0.04),
    utilities: Math.round(investment * 0.015),
    marketing: Math.round(investment * 0.01)
  };

  const totalRecurring = Object.values(recurring).reduce((s, v) => s + Number(v), 0);

  const recurringItems = [
    { label: t('financial.rent'), value: recurring.rent, color: 'bg-blue-500' },
    { label: t('financial.inventory'), value: recurring.inventory, color: 'bg-emerald-500' },
    { label: t('financial.staff'), value: recurring.staff, color: 'bg-amber-500' },
    { label: t('financial.utilities'), value: recurring.utilities, color: 'bg-purple-500' },
    { label: t('financial.marketing'), value: recurring.marketing, color: 'bg-rose-500' },
  ];

  const monthlyProjection = plan?.monthlyProjection || [
    { month: 'M1', revenue: investment * 0.08, expenses: totalRecurring, profit: (investment * 0.08) - totalRecurring },
    { month: 'M2', revenue: investment * 0.1, expenses: totalRecurring * 1.02, profit: (investment * 0.1) - (totalRecurring * 1.02) },
    { month: 'M3', revenue: investment * 0.15, expenses: totalRecurring * 1.05, profit: (investment * 0.15) - (totalRecurring * 1.05) },
    { month: 'M4', revenue: investment * 0.18, expenses: totalRecurring * 1.06, profit: (investment * 0.18) - (totalRecurring * 1.06) },
    { month: 'M5', revenue: investment * 0.21, expenses: totalRecurring * 1.07, profit: (investment * 0.21) - (totalRecurring * 1.07) },
    { month: 'M6', revenue: investment * 0.25, expenses: totalRecurring * 1.1, profit: (investment * 0.25) - (totalRecurring * 1.1) },
    { month: 'M7', revenue: investment * 0.27, expenses: totalRecurring * 1.1, profit: (investment * 0.27) - (totalRecurring * 1.1) },
    { month: 'M8', revenue: investment * 0.29, expenses: totalRecurring * 1.12, profit: (investment * 0.29) - (totalRecurring * 1.12) },
    { month: 'M9', revenue: investment * 0.32, expenses: totalRecurring * 1.15, profit: (investment * 0.32) - (totalRecurring * 1.15) },
    { month: 'M10', revenue: investment * 0.35, expenses: totalRecurring * 1.16, profit: (investment * 0.35) - (totalRecurring * 1.16) },
    { month: 'M11', revenue: investment * 0.37, expenses: totalRecurring * 1.18, profit: (investment * 0.37) - (totalRecurring * 1.18) },
    { month: 'M12', revenue: investment * 0.40, expenses: totalRecurring * 1.2, profit: (investment * 0.40) - (totalRecurring * 1.2) },
  ];

  // Quarterly view: aggregate monthly projections into Q1-Q4 groupings
  const quarterlyProjection = [
    { month: 'Q1', revenue: monthlyProjection.slice(0, 3).reduce((s, d) => s + d.revenue, 0), expenses: monthlyProjection.slice(0, 3).reduce((s, d) => s + d.expenses, 0), profit: monthlyProjection.slice(0, 3).reduce((s, d) => s + d.profit, 0) },
    { month: 'Q2', revenue: monthlyProjection.slice(3, 6).reduce((s, d) => s + d.revenue, 0), expenses: monthlyProjection.slice(3, 6).reduce((s, d) => s + d.expenses, 0), profit: monthlyProjection.slice(3, 6).reduce((s, d) => s + d.profit, 0) },
    { month: 'Q3', revenue: monthlyProjection.slice(6, 9).reduce((s, d) => s + d.revenue, 0), expenses: monthlyProjection.slice(6, 9).reduce((s, d) => s + d.expenses, 0), profit: monthlyProjection.slice(6, 9).reduce((s, d) => s + d.profit, 0) },
    { month: 'Q4', revenue: monthlyProjection.slice(9, 12).reduce((s, d) => s + d.revenue, 0), expenses: monthlyProjection.slice(9, 12).reduce((s, d) => s + d.expenses, 0), profit: monthlyProjection.slice(9, 12).reduce((s, d) => s + d.profit, 0) },
  ];

  const projectionData = viewMode === 'quarterly' ? quarterlyProjection : monthlyProjection;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="max-w-6xl mx-auto space-y-6"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">{t('financial.title')}</h1>
        <p className="text-white/40">{t('financial.subtitle')}</p>
      </motion.div>

      {/* Investment Slider */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6">
          <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
            <Wallet size={18} className="text-accent-400" />
            {t('financial.investment_slider')}
          </h3>
          <input
            type="range"
            min="25000"
            max="3000000"
            step="25000"
            value={investment}
            onChange={(e) => setInvestment(parseInt(e.target.value))}
            className="w-full accent-accent-500 mb-4 cursor-pointer"
            id="financial-investment-slider"
          />
          <div className="flex justify-between items-center">
            <span className="text-xs text-white/40">₹25,000</span>
            <span className="text-3xl font-black text-accent-400">
              ₹{investment.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-white/40">₹30,00,000</span>
          </div>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div variants={itemVariants}>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: t('financial.min_capital'), value: minCapital, icon: Wallet, color: 'text-success-400' },
            { label: t('financial.established_capital'), value: establishedCapital, icon: IndianRupee, color: 'text-primary-400' },
            { label: t('financial.recurring_costs'), value: totalRecurring, icon: TrendingUp, color: 'text-accent-400', suffix: '/mo' },
            { label: t('financial.break_even'), value: breakEven, icon: Clock, color: 'text-warning-400', suffix: ` ${t('financial.months')}` },
          ].map((metric, i) => {
            const Icon = metric.icon;
            return (
              <div key={i} className="glass-card-static p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Icon size={16} className={metric.color} />
                  <span className="text-xs text-white/40">{metric.label}</span>
                </div>
                <p className="text-xl font-bold text-white">
                  {metric.suffix === ` ${t('financial.months')}` ? '' : '₹'}
                  {Number(metric.value).toLocaleString('en-IN')}
                  <span className="text-sm text-white/40">{metric.suffix || ''}</span>
                </p>
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Capital Allocation & Emergency Reserve */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-white">{t('financial.capital_allocation')}</h3>
            <span className="text-xs text-accent-400 flex items-center gap-1">
              <ShieldCheck size={14} />
              {t('financial.emergency_reserve')}: ₹{(plan?.capitalBreakdown?.emergencyReserve || investment * 0.1).toLocaleString('en-IN')}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-white/2 border border-white/5">
              <p className="text-[11px] text-white/40">{t('financial.equipment_capex')}</p>
              <p className="text-base font-bold text-white">₹{(plan?.capitalBreakdown?.machineryAndEquipment || investment * 0.45).toLocaleString('en-IN')}</p>
            </div>
            <div className="p-3 rounded-xl bg-white/2 border border-white/5">
              <p className="text-[11px] text-white/40">{t('financial.initial_stock')}</p>
              <p className="text-base font-bold text-white">₹{(plan?.capitalBreakdown?.initialInventoryStock || investment * 0.3).toLocaleString('en-IN')}</p>
            </div>
            <div className="p-3 rounded-xl bg-white/2 border border-white/5">
              <p className="text-[11px] text-white/40">{t('financial.working_capital')}</p>
              <p className="text-base font-bold text-white">₹{(plan?.capitalBreakdown?.workingCapitalBuffer || investment * 0.15).toLocaleString('en-IN')}</p>
            </div>
            <div className="p-3 rounded-xl bg-white/2 border border-white/5">
              <p className="text-[11px] text-white/40">{t('financial.emergency_buffer')}</p>
              <p className="text-base font-bold text-accent-400">₹{(plan?.capitalBreakdown?.emergencyReserve || investment * 0.1).toLocaleString('en-IN')}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Recurring Costs Breakdown — animated bars with live width binding (Spec §10 fix) */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6">
          <h3 className="text-base font-bold text-white mb-4">{t('financial.recurring_costs')} (₹{totalRecurring.toLocaleString('en-IN')}/{t('financial.month_short')})</h3>
          <div className="space-y-3">
            {recurringItems.map((item, i) => {
              const percentage = totalRecurring > 0 ? (item.value / totalRecurring) * 100 : 20;
              return (
                <div key={`${i}-${investment}-${businessType}`}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-white/60">{item.label}</span>
                    <span className="text-white font-medium">₹{Number(item.value).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      key={`bar-${i}-${investment}-${businessType}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.8, delay: i * 0.1 }}
                      className={`h-full rounded-full ${item.color}`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>

      {/* Cash Flow Projection — force re-mount with key on data changes (Spec §10 fix) */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <TrendingUp size={18} className="text-success-400" />
              {t('financial.projection')}
            </h3>
            <div className="flex gap-1 bg-white/5 rounded-lg p-0.5">
              {['monthly', 'quarterly'].map(mode => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
                    viewMode === mode ? 'bg-primary-600 text-white' : 'text-white/40 hover:text-white/60'
                  }`}
                >
                  {mode === 'monthly' ? t('financial.monthly') : t('financial.quarterly')}
                </button>
              ))}
            </div>
          </div>
          {/* Key forces full chart re-mount when investment or viewMode changes */}
          <div key={`chart-${investment}-${businessType}-${viewMode}`}>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={projectionData}>
                <defs>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b5bdb" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b5bdb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#1a2035', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#e2e8f0' }}
                  formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, '']}
                />
                <Area type="monotone" dataKey="revenue" stroke="#10b981" fill="url(#revenueGrad)" strokeWidth={2} name={t('financial.revenue')} />
                <Area type="monotone" dataKey="profit" stroke="#3b5bdb" fill="url(#profitGrad)" strokeWidth={2} name={t('financial.profit')} />
                <Line type="monotone" dataKey="expenses" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} name={t('financial.expenses')} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
