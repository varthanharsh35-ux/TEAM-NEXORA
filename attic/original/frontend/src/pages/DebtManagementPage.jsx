import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, AlertCircle, CheckCircle, Clock, IndianRupee, Bell, Plus, Trash2 } from 'lucide-react';

const containerVariants = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

export default function DebtManagementPage() {
  const { t } = useTranslation();
  const [loans, setLoans] = useState(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_loans');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [showAddModal, setShowAddModal] = useState(false);
  const [newLoan, setNewLoan] = useState({
    name: '',
    principal: '',
    remaining: '',
    emi: '',
    nextDue: '',
    status: 'on_track'
  });

  useEffect(() => {
    localStorage.setItem('gramsahayak_loans', JSON.stringify(loans));
  }, [loans]);

  const totalDebt = loans.reduce((s, l) => s + Number(l.principal || 0), 0);
  const totalRemaining = loans.reduce((s, l) => s + Number(l.remaining || 0), 0);
  const totalRepaid = Math.max(0, totalDebt - totalRemaining);
  const repaymentProgress = totalDebt > 0 ? (totalRepaid / totalDebt) * 100 : 0;

  const handleAddLoan = () => {
    if (!newLoan.name || !newLoan.principal) return;
    const loan = {
      id: Date.now(),
      name: newLoan.name,
      principal: Number(newLoan.principal),
      remaining: Number(newLoan.remaining || newLoan.principal),
      emi: Number(newLoan.emi || 0),
      nextDue: newLoan.nextDue || 'Upcoming',
      status: newLoan.status || 'on_track'
    };
    setLoans(prev => [...prev, loan]);
    setNewLoan({ name: '', principal: '', remaining: '', emi: '', nextDue: '', status: 'on_track' });
    setShowAddModal(false);
  };

  const handleRemoveLoan = (id) => {
    setLoans(prev => prev.filter(l => l.id !== id));
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="max-w-6xl mx-auto space-y-6">
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">{t('debt.title')}</h1>
          <p className="text-white/40">Track and manage outstanding business loans and EMI obligations</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn btn-accent flex items-center gap-2 cursor-pointer" id="add-loan-btn">
          <Plus size={16} />
          {t('debt.add_loan')}
        </button>
      </motion.div>

      {/* Summary Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: t('debt.total_debt'), value: totalDebt, color: 'text-white', icon: Scale },
          { label: t('debt.total_repaid'), value: totalRepaid, color: 'text-success-400', icon: CheckCircle },
          { label: 'Remaining Balance', value: totalRemaining, color: 'text-warning-400', icon: IndianRupee },
          { label: 'Total Monthly EMI', value: loans.reduce((s, l) => s + Number(l.emi || 0), 0), color: 'text-accent-400', icon: Clock },
        ].map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className="glass-card-static p-5">
              <div className="flex items-center gap-2 mb-2">
                <Icon size={16} className={card.color} />
                <span className="text-xs text-white/40">{card.label}</span>
              </div>
              <p className={`text-xl font-bold ${card.color}`}>
                ₹{card.value.toLocaleString('en-IN')}
              </p>
            </div>
          );
        })}
      </motion.div>

      {loans.length > 0 ? (
        <>
          {/* Overall Progress */}
          <motion.div variants={itemVariants}>
            <div className="glass-card-static p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold text-white">{t('debt.progress')}</h3>
                <span className="text-sm font-bold text-success-400">{repaymentProgress.toFixed(1)}%</span>
              </div>
              <div className="h-4 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${repaymentProgress}%` }}
                  transition={{ duration: 1.2, ease: 'easeOut' }}
                  className="h-full rounded-full bg-gradient-to-r from-primary-500 to-success-500"
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-white/40">
                <span>₹{totalRepaid.toLocaleString('en-IN')} repaid</span>
                <span>₹{totalRemaining.toLocaleString('en-IN')} remaining</span>
              </div>
            </div>
          </motion.div>

          {/* Loans Table */}
          <motion.div variants={itemVariants}>
            <div className="glass-card-static p-6">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Scale size={20} className="text-primary-400" />
                {t('debt.outstanding')} ({loans.length})
              </h3>
              <div className="space-y-4">
                {loans.map((loan) => {
                  const progress = loan.principal > 0 ? ((loan.principal - loan.remaining) / loan.principal) * 100 : 100;
                  return (
                    <div key={loan.id} className="p-4 rounded-xl bg-white/2 border border-white/5 hover:bg-white/4 transition-colors">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <p className="text-sm font-semibold text-white">{loan.name}</p>
                          <p className="text-xs text-white/40">Next Due: {loan.nextDue}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            loan.status === 'on_track' ? 'bg-success-500/10 text-success-400' :
                            loan.status === 'paid' ? 'bg-primary-500/10 text-primary-400' : 'bg-danger-500/10 text-danger-400'
                          }`}>
                            {loan.status === 'on_track' ? t('debt.on_track') :
                             loan.status === 'paid' ? t('debt.paid') : t('debt.overdue')}
                          </span>
                          <button
                            onClick={() => handleRemoveLoan(loan.id)}
                            className="p-1 rounded text-white/30 hover:text-danger-400 transition-colors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-3 mb-3">
                        <div>
                          <p className="text-[10px] text-white/30">{t('debt.principal')}</p>
                          <p className="text-sm font-bold text-white">₹{loan.principal.toLocaleString('en-IN')}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-white/30">{t('debt.remaining')}</p>
                          <p className="text-sm font-bold text-warning-400">₹{loan.remaining.toLocaleString('en-IN')}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-white/30">{t('debt.emi')}</p>
                          <p className="text-sm font-bold text-accent-400">₹{loan.emi.toLocaleString('en-IN')}/mo</p>
                        </div>
                      </div>
                      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-primary-500 to-success-500"
                          style={{ width: `${Math.min(100, progress)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        </>
      ) : (
        <div className="glass-card-static p-12 text-center">
          <CheckCircle size={40} className="mx-auto text-success-400/40 mb-3" />
          <p className="text-white/60 text-sm max-w-md mx-auto mb-4">{t('debt.empty_loans')}</p>
          <button onClick={() => setShowAddModal(true)} className="btn btn-sm btn-primary">
            + Add Loan Facility
          </button>
        </div>
      )}

      {/* Add Loan Modal */}
      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowAddModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card-static p-6 max-w-md w-full space-y-4"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-white">Add Loan / Scheme Facility</h3>
              <div>
                <label className="input-label">Loan / Scheme Name</label>
                <input
                  type="text"
                  placeholder="e.g. Mudra Shishu, PM SVANidhi"
                  value={newLoan.name}
                  onChange={e => setNewLoan(p => ({ ...p, name: e.target.value }))}
                  className="input-field"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="input-label">Sanctioned Principal (₹)</label>
                  <input
                    type="number"
                    placeholder="50000"
                    value={newLoan.principal}
                    onChange={e => setNewLoan(p => ({ ...p, principal: e.target.value, remaining: e.target.value }))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="input-label">Monthly EMI (₹)</label>
                  <input
                    type="number"
                    placeholder="1500"
                    value={newLoan.emi}
                    onChange={e => setNewLoan(p => ({ ...p, emi: e.target.value }))}
                    className="input-field"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="input-label">Remaining Balance (₹)</label>
                  <input
                    type="number"
                    placeholder="50000"
                    value={newLoan.remaining}
                    onChange={e => setNewLoan(p => ({ ...p, remaining: e.target.value }))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="input-label">Next Due Date</label>
                  <input
                    type="date"
                    value={newLoan.nextDue}
                    onChange={e => setNewLoan(p => ({ ...p, nextDue: e.target.value }))}
                    className="input-field"
                  />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={() => setShowAddModal(false)} className="btn btn-outline flex-1">
                  Cancel
                </button>
                <button onClick={handleAddLoan} className="btn btn-primary flex-1">
                  Save Loan
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
