import { useRef, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, useInView, useScroll, useTransform } from 'framer-motion';
import {
  Brain, Landmark, Calculator, ShieldCheck,
  ArrowRight, Sparkles, TrendingUp, Users,
  MapPin, ChevronDown
} from 'lucide-react';
import LanguageSelector from '../components/LanguageSelector';

function AnimatedNumber({ value }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const duration = 1200;
    const steps = 24;
    const increment = value / steps;
    const stepTime = duration / steps;
    const timer = setInterval(() => {
      start += increment;
      if (start >= value) {
        setDisplay(value);
        clearInterval(timer);
      } else {
        setDisplay(Math.floor(start));
      }
    }, stepTime);
    return () => clearInterval(timer);
  }, [value]);
  return <>{display.toLocaleString()}</>;
}

function AnimatedSection({ children, className = '', delay = 0 }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const features = [
  {
    icon: Brain,
    titleKey: 'landing.feature1_title',
    descKey: 'landing.feature1_desc',
    gradient: 'from-blue-500 to-purple-600',
    bgGlow: 'bg-blue-500/10'
  },
  {
    icon: Landmark,
    titleKey: 'landing.feature2_title',
    descKey: 'landing.feature2_desc',
    gradient: 'from-emerald-500 to-teal-600',
    bgGlow: 'bg-emerald-500/10'
  },
  {
    icon: Calculator,
    titleKey: 'landing.feature3_title',
    descKey: 'landing.feature3_desc',
    gradient: 'from-orange-500 to-amber-600',
    bgGlow: 'bg-orange-500/10'
  },
  {
    icon: ShieldCheck,
    titleKey: 'landing.feature4_title',
    descKey: 'landing.feature4_desc',
    gradient: 'from-rose-500 to-pink-600',
    bgGlow: 'bg-rose-500/10'
  },
];

const stats = [
  { value: 15000, suffix: '+', labelKey: 'landing.stats_businesses', icon: Users },
  { value: 120, suffix: '+', labelKey: 'landing.stats_schemes', icon: Landmark },
  { value: 28, suffix: '', labelKey: 'landing.stats_states', icon: MapPin },
  { value: 45, suffix: '%', labelKey: 'landing.stats_savings', icon: TrendingUp },
];

export default function LandingPage() {
  const { t } = useTranslation();
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start']
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 1], [1, 0.95]);

  return (
    <div className="min-h-screen bg-surface-900 overflow-hidden">
      {/* Fixed Language Selector */}
      <div className="fixed top-4 right-4 z-50">
        <LanguageSelector />
      </div>

      {/* ============ HERO ============ */}
      <section ref={heroRef} className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 gradient-hero" />

        {/* Floating Orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 rounded-full bg-primary-500/10 blur-3xl animate-float" />
        <div className="absolute bottom-20 right-10 w-96 h-96 rounded-full bg-accent-500/8 blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary-600/5 blur-3xl" />

        {/* Grid Pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
          backgroundSize: '60px 60px'
        }} />

        <motion.div
          style={{ opacity: heroOpacity, scale: heroScale }}
          className="relative z-10 max-w-5xl mx-auto px-4 text-center"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8"
          >
            <Sparkles size={14} className="text-accent-400" />
            <span className="text-xs font-medium text-white/70">
              🇮🇳 SIH 2026 — Team Nexora
            </span>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black mb-6 leading-[0.9] tracking-tight"
          >
            <span className="gradient-text">{t('app.name')}</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="text-xl sm:text-2xl md:text-3xl font-medium text-white/50 mb-4"
          >
            {t('app.tagline')}
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="max-w-2xl mx-auto text-base sm:text-lg text-white/40 mb-10 leading-relaxed"
          >
            {t('landing.hero_subtitle')}
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/login?mode=signup" className="btn btn-lg btn-accent group">
              {t('landing.cta_start')}
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link to="/existing-business" className="btn btn-lg btn-outline">
              {t('landing.cta_existing')}
            </Link>
          </motion.div>
        </motion.div>

        {/* Scroll Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="text-xs text-white/30">Scroll to explore</span>
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
          >
            <ChevronDown size={20} className="text-white/30" />
          </motion.div>
        </motion.div>
      </section>

      {/* ============ STATS ============ */}
      <section className="py-16 border-y border-white/5 bg-surface-800/30">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
            {stats.map((stat, i) => (
              <AnimatedSection key={i} delay={i * 0.1} className="text-center">
                <stat.icon size={24} className="mx-auto mb-3 text-primary-400" />
                <div className="text-3xl md:text-4xl font-black text-white mb-1">
                  <AnimatedNumber value={stat.value} />
                  <span className="text-accent-400">{stat.suffix}</span>
                </div>
                <p className="text-sm text-white/40">{t(stat.labelKey)}</p>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </section>

      {/* ============ FEATURES ============ */}
      <section className="py-24 relative">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/5 rounded-full blur-3xl" />

        <div className="max-w-6xl mx-auto px-4">
          <AnimatedSection className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-black text-white mb-4">
              Everything You Need to{' '}
              <span className="gradient-text">Succeed</span>
            </h2>
            <p className="text-lg text-white/40 max-w-2xl mx-auto">
              AI-powered tools designed specifically for India's rural micro-entrepreneurs
            </p>
          </AnimatedSection>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <AnimatedSection key={i} delay={i * 0.15}>
                  <div className="glass-card p-8 h-full group">
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform shadow-lg`}>
                      <Icon size={24} className="text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3">{t(feature.titleKey)}</h3>
                    <p className="text-white/50 leading-relaxed">{t(feature.descKey)}</p>
                  </div>
                </AnimatedSection>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============ CTA SECTION ============ */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 gradient-primary opacity-20" />
        <div className="absolute inset-0 bg-surface-900/80" />

        <AnimatedSection className="relative z-10 max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-5xl font-black text-white mb-6">
            Ready to Transform Your{' '}
            <span className="gradient-text">Business Idea</span>?
          </h2>
          <p className="text-lg text-white/40 mb-10 max-w-2xl mx-auto">
            Join thousands of rural entrepreneurs who are using AI to build viable businesses and access government support.
          </p>
          <Link to="/login?mode=signup" className="btn btn-lg btn-accent group">
            {t('landing.cta_start')}
            <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </AnimatedSection>
      </section>

      {/* ============ FOOTER ============ */}
      <footer className="border-t border-white/5 py-8">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <span className="text-white font-bold text-sm">G</span>
            </div>
            <span className="text-sm font-semibold text-white/60">GramSahayak</span>
          </div>
          <p className="text-xs text-white/30">
            © 2026 Team Nexora — Smart India Hackathon. Powered by Bhashini 🇮🇳
          </p>
        </div>
      </footer>
    </div>
  );
}
