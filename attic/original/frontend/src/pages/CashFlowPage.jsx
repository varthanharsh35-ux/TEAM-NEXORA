import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { Plus, ArrowUpRight, ArrowDownRight, Wallet, Trash2, AlertCircle } from 'lucide-react';

// Deterministic color palette: each category always gets the same color
const COLOR_PALETTE = [
  '#10b981', '#3b5bdb', '#f97316', '#ef4444', '#8b5cf6',
  '#f59e0b', '#06b6d4', '#ec4899', '#84cc16', '#6366f1'
];

function getCategoryColor(categoryName, categoryIndex) {
  // Hash the category name to get a consistent index
  let hash = 0;
  for (let i = 0; i < categoryName.length; i++) {
    hash = categoryName.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32bit integer
  }
  const idx = Math.abs(hash) % COLOR_PALETTE.length;
  return COLOR_PALETTE[idx];
}

const containerVariants = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

export default function CashFlowPage() {
  const { t } = useTranslation();
  const [transactions, setTransactions] = useState(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_transactions');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [showForm, setShowForm] = useState(false);
  const [newTx, setNewTx] = useState({
    date: new Date().toISOString().split('T')[0],
    type: 'in',
    amount: '',
    category: '',
    description: ''
  });

  useEffect(() => {
    localStorage.setItem('gramsahayak_transactions', JSON.stringify(transactions));
  }, [transactions]);

  const totalIn = transactions.filter(t => t.type === 'in').reduce((s, t) => s + Number(t.amount || 0), 0);
  const totalOut = transactions.filter(t => t.type === 'out').reduce((s, t) => s + Number(t.amount || 0), 0);
  const balance = totalIn - totalOut;

  const monthlyMap = {};
  transactions.forEach(tx => {
    const month = tx.date ? tx.date.substring(0, 7) : 'Current';
    if (!monthlyMap[month]) monthlyMap[month] = { month, income: 0, expenses: 0 };
    if (tx.type === 'in') monthlyMap[month].income += Number(tx.amount || 0);
    else monthlyMap[month].expenses += Number(tx.amount || 0);
  });
  const monthlyData = Object.values(monthlyMap);

  const categoryData = transactions
    .filter(t => t.type === 'out')
    .reduce((acc, t) => {
      const cat = t.category || 'General';
      const existing = acc.find(a => a.name === cat);
      if (existing) existing.value += Number(t.amount || 0);
      else acc.push({ name: cat, value: Number(t.amount || 0) });
      return acc;
    }, []);

  // Apply deterministic color assignment per category
  const coloredCategoryData = categoryData.map((cat, i) => ({
    ...cat,
    color: getCategoryColor(cat.name, i)
  }));

  const addTransaction = () => {
    if (!newTx.amount || Number(newTx.amount) <= 0) return;
    const tx = {
      id: Date.now(),
      ...newTx,
      amount: Number(newTx.amount),
      category: newTx.category.trim() || (newTx.type === 'in' ? 'Sales / Revenue' : 'General Expense'),
      date: newTx.date || new Date().toISOString().split('T')[0],
    };
    setTransactions(prev => [tx, ...prev]);
    setNewTx({
      date: new Date().toISOString().split('T')[0],
      type: 'in',
      amount: '',
      category: '',
      description: ''
    });
    setShowForm(false);
  };

  const removeTransaction = (id) => {
    setTransactions(prev => prev.filter(t => t.id !== id));
  };

  // Get consistent color for a transaction's category
  const getTxCategoryColor = (tx) => {
    if (tx.type === 'in') return '#10b981';
    return getCategoryColor(tx.category || 'General', 0);
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="max-w-6xl mx-auto space-y-6">
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">{t('cashflow.title')}</h1>
          <p className="text-white/40">{t('cashflow.subtitle')}</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-accent flex items-center gap-2 cursor-pointer" id="add-tx-btn">
          <Plus size={16} />
          {t('cashflow.add_transaction')}
        </button>
      </motion.div>

      {/* Summary Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-3 gap-4">
        {[
          { label: t('cashflow.income'), value: totalIn, icon: ArrowUpRight, color: 'text-success-400', bg: 'bg-success-500/10' },
          { label: t('cashflow.expenses'), value: totalOut, icon: ArrowDownRight, color: 'text-danger-400', bg: 'bg-danger-500/10' },
          { label: t('cashflow.balance'), value: balance, icon: Wallet, color: balance >= 0 ? 'text-primary-400' : 'text-danger-400', bg: 'bg-primary-500/10' },
        ].map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className="glass-card-static p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center`}>
                  <Icon size={16} className={card.color} />
                </div>
                <span className="text-xs text-white/40">{card.label}</span>
              </div>
              <p className={`text-2xl font-bold ${card.color}`}>
                ₹{Math.abs(card.value).toLocaleString('en-IN')}
              </p>
            </div>
          );
        })}
      </motion.div>

      {/* Add Transaction Form */}
      {showForm && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="glass-card-static p-6"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <label className="text-xs text-white/40 block mb-1">{t('cashflow.date')}</label>
              <input
                type="date"
                value={newTx.date}
                onChange={e => setNewTx(p => ({...p, date: e.target.value}))}
                className="input-field"
                id="tx-date"
              />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">{t('cashflow.type')}</label>
              <select
                value={newTx.type}
                onChange={e => setNewTx(p => ({...p, type: e.target.value}))}
                className="input-field"
                id="tx-type"
              >
                <option value="in">{t('cashflow.cash_in')}</option>
                <option value="out">{t('cashflow.cash_out')}</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">{t('cashflow.amount_label')}</label>
              <input
                type="number"
                placeholder="e.g., 5000"
                value={newTx.amount}
                onChange={e => setNewTx(p => ({...p, amount: e.target.value}))}
                className="input-field"
                id="tx-amount"
                min="1"
              />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">{t('cashflow.category')}</label>
              <input
                type="text"
                placeholder={t('cashflow.category_placeholder')}
                value={newTx.category}
                onChange={e => setNewTx(p => ({...p, category: e.target.value}))}
                className="input-field"
                id="tx-category"
              />
            </div>
            <div className="flex items-end">
              <button onClick={addTransaction} className="btn btn-primary w-full cursor-pointer" id="save-tx-btn">
                {t('cashflow.add_entry')}
              </button>
            </div>
          </div>
          <div className="mt-3">
            <input
              type="text"
              placeholder={t('cashflow.description_placeholder')}
              value={newTx.description}
              onChange={e => setNewTx(p => ({...p, description: e.target.value}))}
              className="input-field"
              id="tx-desc"
            />
          </div>
        </motion.div>
      )}

      {transactions.length > 0 ? (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Monthly Summary Chart */}
          <motion.div variants={itemVariants}>
            <div className="glass-card-static p-6">
              <h3 className="text-lg font-bold text-white mb-4">{t('cashflow.monthly_summary')}</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={monthlyData} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ background: '#1a2035', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#e2e8f0' }}
                    formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, '']}
                  />
                  <Bar dataKey="income" fill="#10b981" radius={[6, 6, 0, 0]} name={t('cashflow.income')} />
                  <Bar dataKey="expenses" fill="#ef4444" radius={[6, 6, 0, 0]} name={t('cashflow.expenses')} opacity={0.7} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Category Breakdown — with persistent deterministic colors (Spec §11) */}
          <motion.div variants={itemVariants}>
            <div className="glass-card-static p-6">
              <h3 className="text-lg font-bold text-white mb-4">{t('cashflow.category_breakdown')}</h3>
              {coloredCategoryData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={coloredCategoryData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={4}>
                        {coloredCategoryData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#1a2035', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#e2e8f0' }}
                        formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, '']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-3 justify-center mt-2">
                    {coloredCategoryData.map((cat, i) => (
                      <div key={i} className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: cat.color }} />
                        <span className="text-xs text-white/50">{cat.name}: ₹{cat.value.toLocaleString('en-IN')}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="py-12 text-center text-white/40 text-xs">{t('cashflow.no_expense_categories')}</div>
              )}
            </div>
          </motion.div>
        </div>
      ) : (
        <div className="glass-card-static p-12 text-center">
          <AlertCircle size={40} className="mx-auto text-white/20 mb-3" />
          <p className="text-white/60 text-sm max-w-md mx-auto mb-4">{t('cashflow.empty_state')}</p>
          <button onClick={() => setShowForm(true)} className="btn btn-sm btn-primary cursor-pointer">
            {t('cashflow.add_first_entry')}
          </button>
        </div>
      )}

      {/* Transaction List */}
      {transactions.length > 0 && (
        <motion.div variants={itemVariants}>
          <div className="glass-card-static p-6">
            <h3 className="text-lg font-bold text-white mb-4">{t('cashflow.recorded_transactions')} ({transactions.length})</h3>
            <div className="space-y-2">
              {transactions.map((tx) => (
                <div key={tx.id} className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/3 transition-colors group">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    tx.type === 'in' ? 'bg-success-500/10' : 'bg-danger-500/10'
                  }`}>
                    {tx.type === 'in'
                      ? <ArrowUpRight size={18} className="text-success-400" />
                      : <ArrowDownRight size={18} className="text-danger-400" />
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{tx.description || tx.category}</p>
                    <div className="flex items-center gap-2 text-xs text-white/40">
                      <span className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full" style={{ background: getTxCategoryColor(tx) }} />
                        {tx.category}
                      </span>
                      <span>·</span>
                      <span>{tx.date}</span>
                    </div>
                  </div>
                  <p className={`text-sm font-bold ${tx.type === 'in' ? 'text-success-400' : 'text-danger-400'}`}>
                    {tx.type === 'in' ? '+' : '-'}₹{Number(tx.amount).toLocaleString('en-IN')}
                  </p>
                  <button
                    onClick={() => removeTransaction(tx.id)}
                    className="p-2 rounded-lg hover:bg-danger-500/10 text-white/20 hover:text-danger-400 transition-all cursor-pointer"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
