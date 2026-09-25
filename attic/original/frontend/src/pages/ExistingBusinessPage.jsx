import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Package, Receipt, TrendingUp, Sparkles, ArrowRight, ArrowLeft } from 'lucide-react';

export default function ExistingBusinessPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-surface-900 py-16 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-500/10 border border-accent-500/20 text-accent-400 text-xs font-semibold">
            <Sparkles size={14} />
            {t('existing_business.badge')}
          </span>
          <h1 className="text-3xl sm:text-4xl font-black text-white">
            {t('existing_business.title')}
          </h1>
          <p className="text-white/50 max-w-xl mx-auto text-sm sm:text-base leading-relaxed">
            {t('existing_business.subtitle')}
          </p>
        </div>

        {/* Feature Cards / Experimental Previews */}
        <div className="grid md:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card-static p-6 space-y-3"
          >
            <div className="w-12 h-12 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400">
              <Package size={24} />
            </div>
            <h3 className="text-lg font-bold text-white">{t('existing_business.feature1_title')}</h3>
            <p className="text-xs text-white/50 leading-relaxed">{t('existing_business.feature1_desc')}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card-static p-6 space-y-3"
          >
            <div className="w-12 h-12 rounded-xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center text-accent-400">
              <Receipt size={24} />
            </div>
            <h3 className="text-lg font-bold text-white">{t('existing_business.feature2_title')}</h3>
            <p className="text-xs text-white/50 leading-relaxed">{t('existing_business.feature2_desc')}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card-static p-6 space-y-3"
          >
            <div className="w-12 h-12 rounded-xl bg-success-500/10 border border-success-500/20 flex items-center justify-center text-success-400">
              <TrendingUp size={24} />
            </div>
            <h3 className="text-lg font-bold text-white">{t('existing_business.feature3_title')}</h3>
            <p className="text-xs text-white/50 leading-relaxed">{t('existing_business.feature3_desc')}</p>
          </motion.div>
        </div>

        {/* Informational Banner */}
        <div className="glass-card-static p-8 text-center space-y-4 border-dashed border-white/10">
          <p className="text-sm text-white/60 max-w-2xl mx-auto leading-relaxed">
            {t('existing_business.description')}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <Link to="/assessment" className="btn btn-primary">
              <span>{t('existing_business.start_assessment')}</span>
              <ArrowRight size={16} />
            </Link>
            <Link to="/" className="btn btn-outline">
              <ArrowLeft size={16} />
              <span>{t('existing_business.back_home')}</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
