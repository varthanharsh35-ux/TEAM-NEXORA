import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, ClipboardList, BarChart3, Wallet,
  Building2, ArrowLeftRight, CreditCard, Scale,
  User, Plus, Bot
} from 'lucide-react';

const sidebarLinks = [
  { to: '/dashboard', icon: LayoutDashboard, labelKey: 'nav.dashboard' },
  { to: '/assessment', icon: Plus, labelKey: 'nav.assessment' },
  { to: '/feasibility', icon: BarChart3, labelKey: 'nav.feasibility' },
  { to: '/financial', icon: Wallet, labelKey: 'nav.financial' },
  { to: '/schemes', icon: Building2, labelKey: 'nav.schemes' },
  { to: '/cashflow', icon: ArrowLeftRight, labelKey: 'nav.cashflow' },
  { to: '/credit', icon: CreditCard, labelKey: 'nav.credit' },
  { to: '/debt', icon: Scale, labelKey: 'nav.debt' },
  { to: '/profile', icon: User, labelKey: 'nav.profile' },
];

export default function Sidebar() {
  const { t } = useTranslation();
  const location = useLocation();

  return (
    <aside className="hidden lg:flex flex-col w-64 min-h-[calc(100vh-64px)] bg-surface-900/50 border-r border-white/5 pt-4 pb-6 px-3">
      {/* Section Label */}
      <div className="px-3 mb-3">
        <p className="text-xs font-semibold text-white/30 uppercase tracking-wider">
          Navigation
        </p>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 space-y-1">
        {sidebarLinks.map((link) => {
          const isActive = location.pathname === link.to;
          const Icon = link.icon;

          return (
            <NavLink
              key={link.to}
              to={link.to}
              className="relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 group"
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 bg-primary-600/15 border border-primary-500/20 rounded-xl"
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.5 }}
                />
              )}
              <Icon
                size={18}
                className={`relative z-10 transition-colors ${
                  isActive ? 'text-primary-400' : 'text-white/40 group-hover:text-white/70'
                }`}
              />
              <span
                className={`relative z-10 transition-colors ${
                  isActive ? 'text-primary-300' : 'text-white/60 group-hover:text-white/80'
                }`}
              >
                {t(link.labelKey)}
              </span>
              {isActive && (
                <motion.div
                  layoutId="sidebar-dot"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full bg-primary-400"
                />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* AI Assistant Quick Access */}
      <div className="mt-4 mx-1">
        <div className="glass-card-static p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg gradient-accent flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">{t('ai.title')}</p>
              <p className="text-xs text-white/40">Ask anything</p>
            </div>
          </div>
          <p className="text-xs text-white/50 mb-3">
            Get instant answers about your business viability and schemes.
          </p>
        </div>
      </div>

      {/* Bhashini Badge */}
      <div className="mt-3 mx-1 px-3 py-2 rounded-lg bg-accent-500/5 border border-accent-500/10">
        <p className="text-[10px] text-accent-400/60 font-medium text-center">
          🇮🇳 Translations powered by Bhashini
        </p>
      </div>
    </aside>
  );
}
