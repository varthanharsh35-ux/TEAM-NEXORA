import { useState, useEffect, useRef, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Sprout,
  MapPin,
  ArrowRight,
  ArrowLeft,
  Wallet,
  FileText,
  Calculator,
  BookOpen,
  Printer,
  Download,
  Check,
  Info,
  AlertTriangle,
  ChevronDown,
  Mic,
  RefreshCw,
  Users,
  Store,
  ShieldCheck,
  Landmark,
  TrendingUp,
  GitCompare,
  Database,
  MessageCircle,
  Volume2,
  Square,
} from 'lucide-react';
import Account from './Account';
import Nearby from './Nearby';
import Schemes from './Schemes';
import Tracker, { saveRepaymentPlan } from './Tracker';
import { Facilities } from './Profile';
import History from './History';
import Compare from './Compare';
import NavHelper from './NavHelper';
import { api, restore, persist } from './api';
const categories = [
  'dairy',
  'retail',
  'food',
  'tailoring',
  'agriculture',
  'poultry',
  'fish',
  'repair',
  'craft',
  'manufacturing',
  'transport',
  'services',
  'other',
];
const sourceLinks = [
  ['source_directory', 'https://www.tnrd.tn.gov.in/databases/Villages.pdf'],
  ['source_districts', 'https://lokbhavan.tn.gov.in/districts-of-tamil-nadu/'],
  ['source_nabard', 'https://www.nabard.org/auth/writereaddata/tender/pub_0602250348211363.pdf'],
  ['source_scheme', 'https://nsfdc.nic.in/faqs'],
];
const initial = {
  person_name: '',
  business_name: '',
  funding_mode: 'savings',
  location: '',
  business: '',
  margin: '100000',
  radius: 15,
  category: 'auto',
  district: '',
  community: 'unspecified',
  facilities: [],
  scheme_id: 'auto',
  gender: 'unspecified',
  age: null,
  household_income: null,
  start_date: new Date().toLocaleDateString('en-CA'),
};
const LocationMap = lazy(() => import('./LocationMap'));
function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
initial.start_date = today();
function Icon({ as: Component, ...props }) {
  return <Component aria-hidden="true" size={20} strokeWidth={1.8} {...props} />;
}
function Notice({ children, danger = false }) {
  return (
    <div className={`notice ${danger ? 'warning' : ''}`}>
      <Icon as={danger ? AlertTriangle : Info} />
      <div>{children}</div>
    </div>
  );
}
function Section({ icon, title, children, className = '' }) {
  return (
    <section className={`panel ${className}`}>
      <h2>
        <Icon as={icon} />
        {title}
      </h2>
      {children}
    </section>
  );
}
function Metric({ label, value, detail, accent = false }) {
  return (
    <div className={`metric ${accent ? 'accent' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </div>
  );
}

function PlanReadinessWidget({ readiness, verdict }) {
  const score = Number(readiness?.score ?? 0);
  const maxScore = 10;
  const pct = Math.min(100, Math.max(0, (score / maxScore) * 100));
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  const scoreColor = score >= 8 ? '#165f49' : score >= 6 ? '#d97706' : '#dc2626';
  const tierTitle = score >= 8 ? 'High Viability Enterprise' : score >= 6 ? 'Moderate Viability' : 'Action Plan Needed';
  const tierDesc = score >= 8
    ? 'Your enterprise model demonstrates strong market demand coverage, achievable breakeven volume, and robust scheme/debt serviceability.'
    : score >= 6
      ? 'Viable rural enterprise with favorable demand conditions. Recommended to strengthen local infrastructure or verify margin subsidy.'
      : 'Core operating metrics indicate elevated initial capital risk. Consider reviewing pricing or choosing a lower-cost activity.';

  const checkLabels = {
    demand: 'Local Market Demand',
    break_even: 'Unit Break-Even Achievable',
    working_capital: 'Working Capital Adequacy',
    facilities: 'Production Infrastructure',
    climate: 'Climate & Monsoon Resilience',
  };

  return (
    <div className={`readiness-visual-card verdict-${verdict || 'viable'}`}>
      <div className="gauge-container">
        <svg className="radial-gauge-svg" width="110" height="110" viewBox="0 0 110 110">
          <circle cx="55" cy="55" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="10" />
          <circle
            cx="55"
            cy="55"
            r={radius}
            fill="none"
            stroke={scoreColor}
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform="rotate(-90 55 55)"
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />
          <text x="55" y="52" textAnchor="middle" fill="#0f172a" fontSize="20" fontWeight="bold">
            {score.toFixed(1)}
          </text>
          <text x="55" y="68" textAnchor="middle" fill="#64748b" fontSize="11">
            out of 10
          </text>
        </svg>
        <div className="gauge-info">
          <span className="readiness-badge" style={{ backgroundColor: scoreColor }}>
            {tierTitle}
          </span>
          <p className="readiness-lead">{tierDesc}</p>
        </div>
      </div>

      <div className="readiness-checks-grid">
        {Object.entries(readiness?.checks || {}).map(([key, passed]) => (
          <div key={key} className={`check-item ${passed ? 'passed' : 'pending'}`}>
            <span className="check-icon">{passed ? '✓' : '⚠️'}</span>
            <span className="check-label">{checkLabels[key] || key.replace(/_/g, ' ')}</span>
            <span className="check-status-pill">{passed ? 'Ready' : 'Verify'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const [form, setForm] = useState(() => ({ ...initial, ...restore('gs-draft', {}), radius: 15 }));
  const [report, setReport] = useState(() => {
    const r = restore('gs-report', null);
    return r?.version === 2 ? r : null;
  });
  const [editing, setEditing] = useState(false),
    [tab, setTab] = useState('plan'),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [coverage, setCoverage] = useState(null),
    [online, setOnline] = useState(false),
    [suggestions, setSuggestions] = useState([]),
    [voice, setVoice] = useState(false),
    [storageError, setStorageError] = useState(false);
  const [history, setHistory] = useState(() => restore('gs-history', []));
  const [showMap, setShowMap] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [stage, setStage] = useState('welcome');
  const [wizardStep, setWizardStep] = useState(1);
  const seq = useRef(0),
    aborter = useRef(null),
    timer = useRef(null),
    recognizer = useRef(null),
    reportHeading = useRef(null);
  const n = (v, dec = 0) =>
    new Intl.NumberFormat(`${lang}-IN`, { maximumFractionDigits: dec }).format(v);
  const money = (v) =>
    new Intl.NumberFormat(`${lang}-IN`, {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(v);
  const date = (d) =>
    new Intl.DateTimeFormat(`${lang}-IN`, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    }).format(new Date(`${d.slice(0, 10)}T12:00:00`));
  const snapshot = () => ({
    profile: form,
    report,
    entries: restore('gs-entries', []),
    plans: restore('gs-repayment-plans', []),
    history,
    loans: restore('gs-loans', []),
  });
  const loadWorkspace = (state) => {
    seq.current++;
    aborter.current?.abort();
    clearTimeout(timer.current);
    setBusy(false);
    const next = { ...initial, ...state.profile };
    setForm(next);
    setReport(state.report?.version === 2 ? state.report : null);
    setHistory(state.history || []);
    persist('gs-history', state.history || []);
    persist('gs-loans', state.loans || []);
    setEditing(false);
    setError('');
    persist('gs-draft', next);
    persist('gs-report', state.report || null);
    persist('gs-entries', state.entries || []);
    persist('gs-repayment-plans', state.plans || []);
  };
  const change = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  useEffect(() => {
    if (!persist('gs-draft', form)) setStorageError(true);
  }, [form]);
  useEffect(() => {
    const open = () =>
      document.querySelectorAll('details.print-open').forEach((d) => (d.open = true));
    window.addEventListener('beforeprint', open);
    return () => window.removeEventListener('beforeprint', open);
  }, []);
  useEffect(() => {
    api('/coverage')
      .then(setCoverage)
      .catch(() => {});
    api('/health')
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
    return () => {
      aborter.current?.abort();
      clearTimeout(timer.current);
      recognizer.current?.abort();
    };
  }, []);
  useEffect(() => {
    const on = () =>
      api('/health')
        .then(() => setOnline(true))
        .catch(() => setOnline(false));
    window.addEventListener('online', on);
    window.addEventListener('offline', on);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', on);
    };
  }, []);
  useEffect(() => {
    if (form.location.trim().length < 3) {
      setSuggestions([]);
      return;
    }
    const ctrl = new AbortController(),
      id = setTimeout(
        () =>
          api(
            `/locations?q=${encodeURIComponent(form.location)}&district=${encodeURIComponent(form.district)}`,
            undefined,
            ctrl.signal
          )
            .then(setSuggestions)
            .catch(() => {}),
        350
      );
    return () => {
      clearTimeout(id);
      ctrl.abort();
    };
  }, [form.location, form.district]);
  // Generation is non-blocking. Each language retains its own advice; fallback is instant.
  useEffect(() => {
    if (!report?.id || !online) return;
    let stopped = false,
      poll;
    const id = report.id;
    const update = (r) => {
      if (!stopped) {
        setReport((prev) => (prev?.id === id ? r : prev));
        persist('gs-report', r);
      }
    };
    api(`/reports/${id}/advice/${lang}`, {})
      .then((r) => {
        update(r);
        if (r.ai_status?.[lang]?.state !== 'done') {
          const started = Date.now();
          poll = setInterval(() => {
            if (Date.now() - started > 600000) {
              clearInterval(poll);
              return;
            }
            api(`/reports/${id}`)
              .then((v) => {
                update(v);
                if (v.ai_status?.[lang]?.state === 'done') clearInterval(poll);
              })
              .catch(() => clearInterval(poll));
          }, 4000);
        }
      })
      .catch(() => {});
    return () => {
      stopped = true;
      clearInterval(poll);
    };
  }, [report?.id, lang, online]);
  const run = async (data = form, focus = true) => {
    setError('');
    const prepData = {
      ...data,
      business: data.business || data.category || 'other',
      category: data.category || data.business || 'other',
      margin: String(data.margin ?? '100000'),
      radius: Number(data.radius) || 15,
    };
    if (
      !prepData.location.trim() ||
      !prepData.business.trim() ||
      !Number.isFinite(Number(prepData.margin)) ||
      Number(prepData.margin) < 0 ||
      Number(prepData.margin) > 100000000 ||
      !prepData.start_date
    ) {
      setError('invalid_input');
      return;
    }
    const current = ++seq.current;
    aborter.current?.abort();
    aborter.current = new AbortController();
    setBusy(true);
    try {
      let finalData = { ...prepData };
      if (finalData.lat == null) {
        try {
          const found = await api(
            `/map/search?q=${encodeURIComponent(finalData.location)}`,
            undefined,
            aborter.current.signal
          );
          if (found.items.length === 1) {
            const { lat, lon, district, location } = found.items[0];
            finalData = { ...finalData, lat, lon, district, location };
          }
        } catch {}
      }
      const r = await api(
        '/reports',
        { ...finalData, margin: Number(finalData.margin), radius: finalData.radius, language: lang },
        aborter.current.signal
      );
      if (current !== seq.current) return;
      setReport(r);
      setForm({ ...r.input, margin: String(r.input.margin), radius: r.input.radius || finalData.radius });
      setEditing(false);
      setOnline(true);
      setStage('app');
      setTab('plan');
      if (!persist('gs-report', r)) setStorageError(true);
      const saved = [r, ...restore('gs-history', []).filter((x) => x.id !== r.id)].slice(0, 20);
      setHistory(saved);
      persist('gs-history', saved);
      api('/account/workspace', {
        ...snapshot(),
        profile: r.input,
        report: r,
        history: saved,
      }).catch(() => {});
      if (focus) {
        setTimeout(() => reportHeading.current?.focus(), 0);
      }
    } catch (e) {
      if (current === seq.current) {
        setError(e.message);
        if (e.message === 'server_error') setOnline(false);
      }
    } finally {
      if (current === seq.current) setBusy(false);
    }
  };
  const example = () =>
    setForm({
      ...initial,
      location: t('example_location'),
      business: 'dairy',
      category: 'dairy',
      district: 'Madurai',
      margin: '100000',
    });
  const clear = () => {
    seq.current++;
    aborter.current?.abort();
    clearTimeout(timer.current);
    setBusy(false);
    setReport(null);
    setEditing(false);
    setForm({ ...initial });
    setError('');
    setTab('plan');
    persist('gs-report', null);
  };
  const openHistory = (r) => {
    seq.current++;
    aborter.current?.abort();
    setBusy(false);
    setReport(r);
    setForm({ ...r.input, margin: String(r.input.margin) });
    persist('gs-report', r);
    setEditing(false);
    setTab('plan');
  };
  const print = () => {
    document.querySelectorAll('details.print-open').forEach((d) => (d.open = true));
    window.print();
  };
  const handleWhatsAppShare = () => {
    if (!report) return;
    const message = [
      `${t('business_name')}: ${report.input.business_name || t('business_plan')}`,
      `${t('location')}: ${report.input.location}`,
      `${t('selected_scheme')}: ${t(report.finance.scheme, { defaultValue: report.finance.scheme_name || report.finance.scheme })}`,
      `${t('loan')}: ${money(report.finance.loan)}`,
      `${t('monthly_operating_surplus')}: ${money(report.metrics.operating_profit)}`,
    ].join('\n');
    window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(message)}`, '_blank', 'noopener,noreferrer');
  };
  const handleVoiceSummary = () => {
    const synthesis = window.speechSynthesis;
    if (!synthesis) return;
    if (isSpeaking || synthesis.speaking) {
      synthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    if (!report || !window.SpeechSynthesisUtterance) return;
    const language = i18n.language?.split('-')[0];
    const summaryLanguage = ['ta', 'hi'].includes(language) ? language : 'en';
    const locale = { ta: 'ta-IN', hi: 'hi-IN', en: 'en-US' }[summaryLanguage];
    const translate = i18n.getFixedT(summaryLanguage);
    const currency = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'INR',
      currencyDisplay: 'name',
      maximumFractionDigits: 2,
    });
    const summary = [
      `${translate('business_name')}: ${report.input.business_name || translate('business_plan')}`,
      `${translate('location')}: ${report.input.location}`,
      `${translate('selected_scheme')}: ${translate(report.finance.scheme, { defaultValue: report.finance.scheme_name || report.finance.scheme })}`,
      `${translate('loan')}: ${currency.format(report.finance.loan)}`,
      `${translate('monthly_operating_surplus')}: ${currency.format(report.metrics.operating_profit)}`,
    ].join('. ');
    const utterance = new SpeechSynthesisUtterance(summary);
    utterance.lang = locale;
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    try {
      synthesis.speak(utterance);
    } catch {
      setIsSpeaking(false);
    }
  };
  const download = () => {
    const fields = ['month', 'due_date', 'opening', 'interest', 'principal', 'payment', 'balance'];
    const lines = [
      fields.map((x) => t(x)),
      ...(report?.finance?.schedule || []).map((r) =>
        fields.map((k) => (k === 'due_date' ? date(r[k]) : n(r[k], 2)))
      ),
    ];
    const csv =
      '\ufeff' +
      lines
        .map((row) => row.map((v) => `"${String(v).replaceAll('"', '""')}"`).join(','))
        .join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `${t('brand')}-${t('schedule')}.csv`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const f = report?.finance,
    m = report?.metrics;
  const ai = report?.ai_status?.[lang],
    advice = report?.advice?.[lang];
  const text = (key) => advice?.[key] || t(`advice.${key}`);
  const getDynamicSwot = (key) => {
    if (advice?.[key]) return advice[key];
    const cat = report?.business?.category || 'other';
    const margin = Number(report?.input?.margin || 0);
    const hasLoan = f?.loan > 0;
    const missingFacs = report?.readiness?.missing || [];
    const households = m?.households || 1000;
    const competitors = m?.competitors || 0;

    if (key === 'strengths') {
      const parts = [];
      if (margin >= 75000) {
        parts.push(`Solid owner equity of ${money(margin)} provides strong safety margin and covers initial inventory.`);
      } else {
        parts.push(`Low capital barrier enables lean startup operations with fast break-even capability.`);
      }
      if (!hasLoan || f?.scheme === 'self_funded') {
        parts.push(`Self-funded structure carries zero debt service burden, leaving operating cash flows fully retained.`);
      } else {
        parts.push(`Concessional debt rate (${n(f?.annual_rate || 6.5, 1)}%) structured with moratorium grace period.`);
      }
      parts.push(`Direct access to an immediate catchment of ${n(households)} local households within ${report?.input?.radius || 15} km.`);
      return parts.join(' ');
    }

    if (key === 'weaknesses') {
      const parts = [];
      if (missingFacs.length > 0) {
        const facNames = missingFacs.map((fc) => t(`facility.${fc}`) || fc).join(', ');
        parts.push(`Pending infrastructure arrangements: ${facNames}. Arranging these before launch is essential.`);
      } else {
        parts.push(`Full baseline production facilities already secured, reducing pre-launch capital expenditure.`);
      }
      if (cat === 'fish') {
        parts.push(`Fresh marine catch is highly perishable; lack of deep insulated ice storage can risk daily 5–8% spoilage.`);
      } else if (cat === 'dairy') {
        parts.push(`Strict daily shelf life requires disciplined twice-daily collection logistics and temperature control.`);
      } else if (cat === 'tailoring') {
        parts.push(`High reliance on individual craft speed; peak festival rush can strain single-tailor delivery commitments.`);
      } else {
        parts.push(`Initial customer acquisition requires trial discounts until repeat ordering patterns stabilize.`);
      }
      return parts.join(' ');
    }

    if (key === 'opportunity') {
      const parts = [];
      if (cat === 'fish') {
        parts.push(`High demand for cleaned, dressed, and pre-weighed fresh fish delivery to residential households and local eateries.`);
        parts.push(`Value-add: Sun-drying and spice-marinated packets during surplus catch periods to boost realization.`);
      } else if (cat === 'dairy') {
        parts.push(`Strong demand for morning doorstep delivery of pure, unadulterated milk and fresh curd.`);
      } else if (cat === 'tailoring') {
        parts.push(`Bulk orders for school uniforms, festive apparel (Pongal/Deepavali), and express alteration services.`);
      } else {
        parts.push(`Convenient evening doorstep delivery and small affordable pack sizes capture underserved rural consumers.`);
      }
      parts.push(`Eligible for government margin assistance under ${f?.scheme_name || t(f?.scheme) || 'verified state schemes'}.`);
      return parts.join(' ');
    }

    if (key === 'threats') {
      const parts = [];
      if (cat === 'fish') {
        parts.push(`Annual 61-day Coromandel marine fishing ban (Apr 15 – Jun 14) and monsoon weather restrict sea catch, requiring alternative freshwater sourcing.`);
      } else if (cat === 'agriculture' || cat === 'dairy') {
        parts.push(`Monsoon delays or seasonal fodder cost escalations can compress operating gross margins.`);
      } else {
        parts.push(`Monsoon transport disruptions and localized supplier price volatility.`);
      }
      if (competitors > 5) {
        parts.push(`Presence of ${n(competitors)} established competitors in the block requires strict quality consistency and prompt service to avoid price wars.`);
      } else {
        parts.push(`Low competitor density reduces direct price competition, allowing healthy margin capture.`);
      }
      return parts.join(' ');
    }

    return advice?.[key] || t(`advice.${key}`);
  };
  const showForm = !report || editing;
  const errKey = [
    'invalid_input',
    'clarify',
    'ambiguous',
    'outside_state',
    'server_error',
    'voice_error',
    'report_missing',
    'scheme_project_limit',
  ].includes(error)
    ? error
    : 'invalid_input';
  return (
    <>
      <a className="skip-link" href="#main">
        {t('skip')}
      </a>
      <div className="masthead">
        <div>
          <span>{t('prototype')}</span>
          <span>{t('not_government')}</span>
        </div>
      </div>
      <header className="header">
        <div className="header-inner">
          <a
            href="#"
            className="brand"
            onClick={(e) => {
              e.preventDefault();
              setTab('plan');
            }}
          >
            <span className="brand-icon">
              <Icon as={Sprout} size={28} />
            </span>
            <span>
              <b>{t('brand')}</b>
              <small>{t('tagline')}</small>
            </span>
          </a>
          <nav hidden={stage !== 'app'} aria-label={t('nav_plan')}>
            {[
              ['plan', FileText],
              ['finance', Calculator],
              ['profile', Users],
              ['tracker', BookOpen],
              // ['compare', GitCompare], -- temporarily removed, re-add this line to restore
              ['account', ShieldCheck],
            ].map(([key, icon]) => (
              <button key={key} className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>
                <Icon as={icon} />
                {t(`nav_${key}`)}
              </button>
            ))}
          </nav>
          <div className="languages" role="group" aria-label={t('language')}>
            {[
              ['en', 'english'],
              ['ta', 'tamil'],
              ['hi', 'hindi'],
            ].map(([code, label]) => (
              <button
                key={code}
                lang={code}
                aria-pressed={lang === code}
                onClick={() => i18n.changeLanguage(code)}
              >
                {t(label)}
              </button>
            ))}
          </div>
        </div>
      </header>
      <main id="main" className="main">
        {stage === 'welcome' && (
          <section className="panel welcome">
            <div className="eyebrow">{t('brand')}</div>
            <h1>{t('brand')}</h1>
            <p className="welcome-tagline" style={{ fontSize: '1.05rem', color: '#165f49', fontWeight: '600', marginBottom: '0.75rem' }}>
              {t('tagline') || 'Local insight, financial planning, and government scheme navigator for rural & semi-urban enterprises.'}
            </p>
            <p>{t('welcome_intro')}</p>
            <div className="report-grid">
              {['benefit_market', 'benefit_finance', 'benefit_action'].map((k) => (
                <article key={k}>
                  <h2>{t(k)}</h2>
                  <p>{t(`${k}_desc`)}</p>
                </article>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
              <button
                className="primary"
                onClick={() => {
                  setStage('auth');
                }}
              >
                {t('start_business') || 'Start Your Business'}
                <Icon as={ArrowRight} />
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setStage('auth');
                }}
              >
                {t('explore_schemes') || 'Explore GramSahayak'}
              </button>
            </div>
          </section>
        )}
        {stage === 'auth' && (
          <div className="auth-wrap">
            <Account
              snapshot={snapshot}
              onLoad={loadWorkspace}
                onContinue={(workspace) => {
                  setStage(workspace?.report?.version === 2 ? 'app' : 'wizard');
                  setTab('plan');
                  setWizardStep(1);
              }}
            />
            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <button
                type="button"
                style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => setStage('welcome')}
              >
                ← {t('back_to_home') || 'Back to Home'}
              </button>
            </div>
          </div>
        )}
        {stage === 'wizard' && (
          <div className="wizard-container">
            <div className="wizard-progress-bar">
              {[
                { step: 1, title: t('wizard_step_1_title') },
                { step: 2, title: t('wizard_step_2_title') },
                { step: 3, title: t('wizard_step_3_title') },
                { step: 4, title: t('wizard_step_4_title') },
              ].map((s) => (
                <div
                  key={s.step}
                  className={`wizard-step-node ${wizardStep === s.step ? 'active' : ''} ${wizardStep > s.step ? 'completed' : ''}`}
                  onClick={() => {
                    if (s.step < wizardStep) setWizardStep(s.step);
                  }}
                >
                  <div className="step-number-circle">
                    {wizardStep > s.step ? '✓' : s.step}
                  </div>
                  <span className="step-title">{s.title}</span>
                </div>
              ))}
            </div>

            <div className="wizard-card">
              {wizardStep === 1 && (
                <div className="wizard-step-1">
                  <h2>1. {t('business_information') || 'Business Information'}</h2>
                  <p className="step-subtitle">{t('step1_subtitle')}</p>

                  <label htmlFor="wizard-person-name">{t('person_name')}</label>
                  <input
                    id="wizard-person-name"
                    maxLength={100}
                    autoComplete="name"
                    placeholder={t('placeholder_person_name')}
                    value={form.person_name || ''}
                    onChange={(e) => change('person_name', e.target.value)}
                  />

                  <label htmlFor="wizard-business-name">{t('business_name')}</label>
                  <input
                    id="wizard-business-name"
                    maxLength={120}
                    placeholder={t('placeholder_business_name')}
                    value={form.business_name || ''}
                    onChange={(e) => change('business_name', e.target.value)}
                  />

                  <label htmlFor="wizard-business-type">
                    <Icon as={Store} /> {t('business_type') || 'Type of Business'}
                  </label>
                  <select
                    id="wizard-business-type"
                    value={form.category === 'auto' ? '' : form.category}
                    onChange={(e) => {
                      change('category', e.target.value);
                      change('business', e.target.value);
                    }}
                  >
                    <option value="">{t('choose_business')}</option>
                    {categories.map((c) => (
                      <option key={c} value={c}>
                        {t(`sector.${c}`)}
                      </option>
                    ))}
                  </select>

                  <div className="step-actions">
                    <button type="button" onClick={() => setStage('auth')}>
                      ← {t('back_to_login')}
                    </button>
                    <button
                      type="button"
                      className="primary"
                      disabled={!form.person_name?.trim() || !form.category || form.category === 'auto'}
                      onClick={() => setWizardStep(2)}
                    >
                      {t('next_location_radius')} →
                    </button>
                  </div>
                </div>
              )}

              {wizardStep === 2 && (
                <div className="wizard-step-2">
                  <h2>2. {t('location_and_radius') || 'Location & Coverage Radius'}</h2>
                  <p className="step-subtitle">
                    {t('step2_subtitle')}
                  </p>

                  <label htmlFor="wizard-location">
                    <Icon as={MapPin} /> {t('location')}
                  </label>
                  <input
                    id="wizard-location"
                    autoComplete="off"
                    maxLength={200}
                    list="places"
                    value={form.location}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        location: e.target.value,
                        district: '',
                        lat: null,
                        lon: null,
                      }))
                    }
                    placeholder={t('location_placeholder')}
                  />
                  <datalist id="places">
                    {suggestions.map((s, i) => (
                      <option key={`${s.id || s.name}-${i}`} value={`${s.name}, ${s.district}`} />
                    ))}
                  </datalist>

                  <div className="radius-selector-group">
                    <label>{t('coverage_radius') || 'Coverage Radius (Only selectable here)'}</label>
                    <div className="radius-buttons">
                      {[5, 10, 15].map((r) => (
                        <button
                          key={r}
                          type="button"
                          className={`radius-pill ${form.radius === r ? 'active' : ''}`}
                          onClick={() => change('radius', r)}
                        >
                          {t('radius_km_button', { km: r })}
                        </button>
                      ))}
                    </div>
                    <small className="field-hint">
                      {form.radius === 5 && t('radius_hint_5')}
                      {form.radius === 10 && t('radius_hint_10')}
                      {form.radius === 15 && t('radius_hint_15')}
                    </small>
                  </div>

                  <Suspense fallback={<p>{t('map_loading')}</p>}>
                    <LocationMap
                      radius={form.radius || 15}
                      value={form}
                      onChoose={({ location, district, lat, lon }) =>
                        setForm((f) => ({ ...f, location, district, lat, lon }))
                      }
                    />
                  </Suspense>

                  <div className="step-actions">
                    <button type="button" onClick={() => setWizardStep(1)}>
                      ← {t('back')}
                    </button>
                    <button
                      type="button"
                      className="primary"
                      disabled={!form.location?.trim() && form.lat == null}
                      onClick={() => setWizardStep(3)}
                    >
                      {t('next_financing_savings')} →
                    </button>
                  </div>
                </div>
              )}

              {wizardStep === 3 && (
                <div className="wizard-step-3">
                  <h2>3. {t('funding_choice') || 'Business Investment & Savings'}</h2>
                  <p className="step-subtitle">
                    {t('step3_subtitle')}
                  </p>

                  <div className="choice-cards-grid">
                    <div
                      className={`choice-card ${form.funding_mode === 'savings' ? 'selected' : ''}`}
                      onClick={() => {
                        change('funding_mode', 'savings');
                        if (Number(form.margin) <= 0) change('margin', '100000');
                      }}
                    >
                      <div className="choice-card-icon">💰</div>
                      <h3>{t('funding_savings') || 'I have personal savings'}</h3>
                      <p>{t('funding_savings_desc')}</p>
                      <input
                        type="radio"
                        checked={form.funding_mode === 'savings'}
                        readOnly
                      />
                    </div>

                    <div
                      className={`choice-card ${form.funding_mode === 'loan' ? 'selected' : ''}`}
                      onClick={() => {
                        change('funding_mode', 'loan');
                        change('margin', '0');
                      }}
                    >
                      <div className="choice-card-icon">🤝</div>
                      <h3>{t('funding_loan') || 'No savings / Full loan funding'}</h3>
                      <p>{t('funding_loan_desc')}</p>
                      <input
                        type="radio"
                        checked={form.funding_mode === 'loan'}
                        readOnly
                      />
                    </div>
                  </div>

                  {form.funding_mode === 'savings' ? (
                    <div className="savings-input-wrap">
                      <label htmlFor="wizard-margin">{t('savings_amount') || 'Enter Your Savings Contribution (₹)'}</label>
                      <div className="currency-input">
                        <span aria-hidden="true">₹</span>
                        <input
                          id="wizard-margin"
                          type="number"
                          min="0"
                          max="100000000"
                          value={form.margin}
                          onChange={(e) => change('margin', e.target.value)}
                        />
                      </div>
                      <small className="field-hint">
                        {t('savings_allocation_hint')}
                      </small>
                    </div>
                  ) : (
                    <div className="notice">
                      <Icon as={Info} />
                      <div>
                        <strong>{t('zero_cash_required')}</strong>
                        <p>{t('zero_cash_desc')}</p>
                      </div>
                    </div>
                  )}

                  <div className="step-actions">
                    <button type="button" onClick={() => setWizardStep(2)}>
                      ← {t('back')}
                    </button>
                    <button
                      type="button"
                      className="primary"
                      onClick={() => setWizardStep(4)}
                    >
                      {t('next_community_eligibility')} →
                    </button>
                  </div>
                </div>
              )}

              {wizardStep === 4 && (
                <div className="wizard-step-4">
                  <h2>4. {t('community_and_demographics') || 'Community Category & Eligibility'}</h2>
                  <p className="step-subtitle">
                    {t('step4_subtitle')}
                  </p>

                  <div className="form-grid">
                    <div>
                      <label htmlFor="wizard-community">{t('community')}</label>
                      <select
                        id="wizard-community"
                        value={form.community}
                        onChange={(e) => change('community', e.target.value)}
                      >
                        <option value="unspecified">{t('unspecified') || 'Select Community'}</option>
                        <option value="sc">{t('sc') || 'Scheduled Caste (SC)'}</option>
                        <option value="st">{t('st') || 'Scheduled Tribe (ST)'}</option>
                        <option value="obc">{t('obc') || 'Backward Classes (OBC/BC/MBC)'}</option>
                        <option value="general">{t('general') || 'General Category'}</option>
                      </select>
                    </div>

                    <div>
                      <label htmlFor="wizard-gender">{t('gender')}</label>
                      <select
                        id="wizard-gender"
                        value={form.gender}
                        onChange={(e) => change('gender', e.target.value)}
                      >
                        <option value="unspecified">{t('unspecified') || 'Unspecified'}</option>
                        <option value="female">{t('female') || 'Female'}</option>
                        <option value="male">{t('male') || 'Male'}</option>
                        <option value="other_gender">{t('other_gender') || 'Other'}</option>
                      </select>
                    </div>

                    <div>
                      <label htmlFor="wizard-age">{t('age') || 'Applicant Age'}</label>
                      <input
                        id="wizard-age"
                        type="number"
                        min="18"
                        max="100"
                        placeholder="e.g. 28"
                        value={form.age ?? ''}
                        onChange={(e) => change('age', e.target.value === '' ? null : Number(e.target.value))}
                      />
                    </div>

                    <div>
                      <label htmlFor="wizard-district">{t('district')}</label>
                      <select
                        id="wizard-district"
                        value={form.district}
                        onChange={(e) => change('district', e.target.value)}
                      >
                        <option value="">{t('choose_district')}</option>
                        {coverage?.district_list?.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d?.names?.[lang] || d?.names?.en || d.id}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div style={{ marginTop: '1.25rem' }}>
                    <h3>{t('facilities') || 'Production Infrastructure & Utilities'}</h3>
                    <Facilities form={form} change={change} />
                  </div>

                  {error && (
                    <div role="alert" style={{ marginTop: '1rem' }}>
                      <Notice danger>{t(errKey)}</Notice>
                    </div>
                  )}

                  <div className="step-actions">
                    <button type="button" onClick={() => setWizardStep(3)}>
                      ← {t('back')}
                    </button>
                    <button
                      type="button"
                      className="primary submit"
                      disabled={busy}
                      onClick={() => run()}
                    >
                      {busy ? <Icon as={RefreshCw} className="spin" /> : <Icon as={FileText} />}
                      <span>{t(busy ? 'loading' : 'generate')}</span>
                      <Icon as={ArrowRight} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {stage === 'app' && (
          <>
            {tab === 'account' && (
              <Account
                snapshot={snapshot}
                onLoad={loadWorkspace}
                onContinue={() => {
                  setTab('plan');
                  setEditing(false);
                }}
              />
            )}
            {tab === 'tracker' && <Tracker />}
            {/* {tab === 'compare' && <Compare report={report} history={history} />} -- temporarily removed, re-add this line to restore */}
            {tab === 'profile' && <History history={history} onOpen={openHistory} />}
            {storageError && <Notice danger>{t('storage_error')}</Notice>}
            {error && (
              <div role="alert">
                <Notice danger>{t(errKey)}</Notice>
              </div>
            )}
            {report && !online && <Notice>{t('cached')}</Notice>}
            {!report && tab === 'plan' && (
              <div className="empty">
                <Icon as={FileText} size={48} />
                <h1>{t('no_active_plan_title')}</h1>
                <p>{t('no_active_plan_desc')}</p>
                <button className="primary" onClick={() => { setStage('wizard'); setWizardStep(1); }}>
                  {t('create_business_plan')}
                  <Icon as={ArrowRight} />
                </button>
              </div>
            )}
            {report && ['plan', 'finance', 'allocation', 'repayment', 'sources'].includes(tab) && (
              <div
                className={
                  tab === 'plan' && showForm ? 'report-wrap editing-report' : 'report-wrap'
                }
              >
                <div className="report-header">
                  <div>
                    <div className="eyebrow">
                      {t('report')} · {date(report.created_at)}
                    </div>
                    <h1 ref={reportHeading} tabIndex={-1}>
                      {report.input.business_name || t('business_plan')}
                    </h1>
                  </div>
                  <div className="actions">
                    <button
                      onClick={() => {
                        setForm({ ...report.input, margin: String(report.input.margin) });
                        setEditing(true);
                        setTab('plan');
                        setStage('wizard');
                        setWizardStep(1);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                    >
                      <Icon as={MapPin} />
                      {t('edit')}
                    </button>
                    <button onClick={print} title={t('print_tip')}>
                      <Icon as={Printer} />
                      {t('print')}
                    </button>
                    <button onClick={clear}>
                      <Icon as={RefreshCw} />
                      {t('reset')}
                    </button>
                    <button onClick={handleWhatsAppShare}>
                      <Icon as={MessageCircle} />
                      {t('whatsapp_share')}
                    </button>
                    <button onClick={handleVoiceSummary}>
                      <Icon as={isSpeaking ? Square : Volume2} />
                      {t(isSpeaking ? 'stop_voice' : 'listen_summary')}
                    </button>
                  </div>
                </div>
                <div className="report-context print-only">
                  <span>
                    <Icon as={MapPin} />
                    {report.input.location} · {n(report.input.radius)} {t('km')}
                  </span>
                  <span>
                    {t('equity')}: <b>{money(report.input.margin)}</b>
                  </span>
                  <span className="badge">{t('estimated')}</span>
                </div>
                <div className="print-only">
                  <p>
                    {t('input_preserved')}:{' '}
                    {report.business.method === 'user'
                      ? t(`sector.${report.business.category}`)
                      : report.input.business}
                  </p>
                </div>
                <div
                  className={`report-section ${tab !== 'plan' ? 'screen-hidden' : ''}`}
                >
                  <PlanReadinessWidget readiness={report.readiness} verdict={report.verdict} />
                  {report.readiness && (
                    <Section icon={Check} title={t('readiness')}>
                      <p>
                        {t(
                          (report.readiness.missing || []).length ? 'readiness_missing' : 'readiness_ready'
                        )}
                      </p>
                      <div className="district-chips">
                        {(report.readiness.missing || []).map((k) => (
                          <span key={k}>{t(`facility.${k}`)}</span>
                        ))}
                      </div>
                      <small>{t('readiness_note')}</small>
                    </Section>
                  )}
                  {report.business.uncertain && <Notice danger>{t('uncertain')}</Notice>}
                  <Notice>
                    {t(
                      report.location.status === 'district_proxy' ? 'district_proxy' : 'historical'
                    )}
                  </Notice>
                  <div className="metrics-grid window-grid">
                    <Metric
                      label={t('households')}
                      value={n(m.households)}
                      detail={t('estimated')}
                    />
                    <Metric
                      label={report.business.category === 'fish' ? t('fish_catch_benchmark') : t('price')}
                      value={money(m.price)}
                      detail={`${t(`unit_${m.unit}`)} · ${report.business.category === 'fish' ? t('retail_benchmark') : t('estimated')}`}
                    />
                    <Metric
                      label={t('competitors')}
                      value={n(m.competitors)}
                      detail={t('estimated')}
                    />
                    <Metric
                      label={t('monthly_operating_surplus')}
                      value={money(m.operating_profit)}
                      detail={t('monthly_operating_surplus_desc')}
                      accent
                    />
                  </div>
                  <div className="ai-status" role="status">
                    <span className="status-dot" />
                    {t(
                      ai?.state === 'pending'
                        ? 'ai_pending'
                        : ai?.provider === 'api'
                          ? 'ai_api'
                          : ai?.provider === 'local'
                            ? 'ai_local'
                            : ai?.state === 'done'
                              ? 'ai_fallback'
                              : 'ai_curated'
                    )}
                  </div>
                  <div className="report-grid equal-height-grid" style={{ marginBottom: '22px' }}>
                    <Section icon={Users} title={t('market')}>
                      <p>
                        {report.input.location} · {t('radius_fixed')}
                      </p>
                      <p>{text('market')}</p>
                      <p>{t(`channels_${report.business.category}`)}</p>
                      <div className="inline-stat" style={{ marginTop: 'auto', paddingTop: '15px' }}>
                        <span>{t('households')}</span>
                        <b>{n(m.households)}</b>
                      </div>
                      <div className="region">
                        <small>{t('local_economy')}</small>
                        <p>{t(`region.${report.location.district.region}`)}</p>
                      </div>
                    </Section>
                    <Section icon={TrendingUp} title={t('opportunity')}>
                      <p>{getDynamicSwot('opportunity')}</p>
                      <div className="two-stats" style={{ marginTop: 'auto', paddingTop: '15px', borderTop: '1px solid var(--line)' }}>
                        <Metric label={t('reachable_monthly_volume')} value={`${n(m.units)} ${t(`unit_${m.unit}`)}`} />
                        <Metric label={t('break_even_monthly_target')} value={`${n(m.break_even_units)} ${t(`unit_${m.unit}`)}`} />
                      </div>
                      <div className="next-step" style={{ marginTop: '12px' }}>
                        <Icon as={Check} />
                        <span>{t('benefit_action_desc')}</span>
                      </div>
                    </Section>
                  </div>
                  <Section icon={ShieldCheck} title={t('swot')} className="full">
                    <div className="swot-grid">
                      {['strengths', 'weaknesses', 'opportunity', 'threats'].map((k) => (
                        <div key={k} className={`swot ${k}`}>
                          <h3>{t(k)}</h3>
                          <p style={{ lineHeight: 1.6, margin: 0 }}>{getDynamicSwot(k)}</p>
                        </div>
                      ))}
                    </div>
                  </Section>
                  <div className="report-grid equal-height-grid" style={{ marginTop: '22px', marginBottom: '22px' }}>
                    <Section icon={Store} title={t('competition')}>
                      <div className="two-stats">
                        <Metric label={t('competitors')} value={n(m.competitors)} />
                        <Metric label={t('block_competitors')} value={n(m.block_competitors)} />
                      </div>
                      <p>{text('competition')}</p>
                      <small style={{ marginTop: 'auto', display: 'block', paddingTop: '8px' }}>{t('competitor_map_note')}</small>
                    </Section>
                    <Section icon={Wallet} title={t('pricing')}>
                      <div className="price-callout">
                        {money(m.price_low)} – {money(m.price_high)}
                        <small>
                          {t('price_range')} · {t(`unit_${m.unit}`)}
                        </small>
                      </div>
                      <p>{text('pricing')}</p>
                      <small style={{ marginTop: 'auto', display: 'block', paddingTop: '8px' }}>{t('price_disclaimer')}</small>
                    </Section>
                  </div>
                  {report.pricing_strategy?.strategies && (
                    <Section icon={Wallet} title={t('pricing_strategies') || 'Pricing Strategy Options'}>
                      <p>{t('pricing_strategies_intro')}</p>
                      <div className="pricing-strategies-grid">
                        {(report.pricing_strategy.strategies || []).map((st) => (
                          <div
                            key={st.strategy_id}
                            className={`strategy-card ${st.strategy_id === 'match' ? 'recommended' : ''}`}
                          >
                            <h4>{st.label}</h4>
                            <div className="strategy-price">
                              {money(st.unit_price)}
                              <small> / {report.pricing_strategy.unit_label || t('unit_fallback')}</small>
                            </div>
                            <p style={{ fontSize: '0.85rem', color: '#64748b' }}>{st.description}</p>
                            <div style={{ marginTop: '0.5rem', fontSize: '0.82rem' }}>
                              <span>{t('break_even_volume_label')} </span>
                              <b>{t('units_per_month_value', { count: n(st.break_even_units) })}</b>
                            </div>
                          </div>
                        ))}
                      </div>
                    </Section>
                  )}
                  {report.seasonality && (
                    <Section icon={TrendingUp} title={t('seasonality_title') || 'Tamil Nadu Climate & Seasonal Cycles'}>
                      <p>
                        {report.seasonality_note_key ? t(report.seasonality_note_key) : t('seasonality_intro_fallback')}
                      </p>
                      <div className="seasonality-row">
                        {(report.seasonality || []).map((mItem) => {
                          const idx = mItem.index ?? 1.0;
                          const isPeak = idx > 1.05;
                          const isLean = idx < 0.95;
                          const MONTH_KEYS = ['month_1', 'month_2', 'month_3', 'month_4', 'month_5', 'month_6', 'month_7', 'month_8', 'month_9', 'month_10', 'month_11', 'month_12'];
                          const mName = t(MONTH_KEYS[mItem.month - 1]) || `M${mItem.month}`;
                          const reasonText = mItem.reasons?.map((r) => t(r) || r).join(', ');
                          return (
                            <div
                              key={mItem.month}
                              className={`season-month-cell ${isPeak ? 'peak' : isLean ? 'lean' : ''}`}
                              title={`${mName}: Demand ${(idx * 100).toFixed(0)}%${reasonText ? ' — ' + reasonText : ''}`}
                            >
                              <div><b>{mName}</b></div>
                              <div>{(idx * 100).toFixed(0)}%</div>
                              {isPeak && <small style={{ fontSize: '0.62rem', color: '#166534', fontWeight: 700 }}>{t('peak_label')}</small>}
                              {isLean && <small style={{ fontSize: '0.62rem', color: '#991b1b', fontWeight: 700 }}>{t('lean_label')}</small>}
                            </div>
                          );
                        })}
                      </div>
                      {report.business.category === 'fish' && (
                        <div style={{ marginTop: '0.75rem', fontSize: '0.82rem', color: '#475569', background: '#f8fafc', padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                          🐟 <strong>{t('fish_seasonality_note_title')}</strong> {t('fish_seasonality_note_desc')}
                        </div>
                      )}
                    </Section>
                  )}
                  <Section icon={AlertTriangle} title={t('threat_identification')}>
                    <p>{text('threats')}</p>
                    <p>{t(`risk_${report.business.category}`)}</p>
                    <p>{t('spatial_risk_note')}</p>
                    <Nearby key={report.id} report={report} />
                  </Section>
                  <p className="fineprint">{t('ai_disclaimer')}</p>
                  <button
                    className="primary next-finance"
                    onClick={() => {
                      setTab('finance');
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                  >
                    <Icon as={Calculator} />
                    {t('nav_finance')}
                    <Icon as={ArrowRight} />
                  </button>
                </div>
                <div className={`report-section ${tab !== 'finance' ? 'screen-hidden' : ''}`}>
                  <div className="section-intro">
                    <h2>{t('finance_intro')}</h2>
                  </div>
                  {report.funding && (
                    <Section
                      icon={Wallet}
                      title={t(f.scheme === 'self_funded' ? 'self_funded' : 'funding_plan')}
                    >
                      <p>
                        {t(
                          f.scheme === 'self_funded'
                            ? 'savings_enough'
                            : f.funding_gap > 0
                              ? 'contribution_needed'
                              : 'savings_and_loan'
                        )}
                      </p>
                      <dl className="cost-list">
                        {[
                          ['savings_amount', report.funding.savings],
                          ['savings_used', report.funding.used],
                          ['savings_left', report.funding.remaining],
                          ['funding_gap', f.funding_gap],
                        ].map(([key, value]) => (
                          <div key={key}>
                            <dt>{t(key)}</dt>
                            <dd>{money(value)}</dd>
                          </div>
                        ))}
                      </dl>
                    </Section>
                  )}
                  <p>{t('finance_plain')}</p>
                  <p>
                    {t('selected_scheme')}: <b>{t(f.scheme)}</b>
                  </p>
                  {f.scheme === 'nbcfdc' && <Notice>{t('nbcfdc_note')}</Notice>}
                  <p className="fineprint">{t('low_budget')}</p>
                  {busy && <p role="status">{t('loading')}</p>}
                  <div className="metrics-grid window-grid">
                    <Metric
                      label={t('loan')}
                      value={money(f.loan)}
                      detail={t('estimated')}
                      accent
                    />
                    <Metric
                      label={t('project_cost')}
                      value={money(f.project_cost)}
                      detail={t('estimated')}
                    />
                    <Metric
                      label={t('quarterly_payment')}
                      value={money(f.quarterly_payment)}
                      detail={t('calculated')}
                    />
                    <Metric
                      label={t('equity')}
                      value={money(f.margin)}
                      detail={t('savings_used')}
                    />
                  </div>
                  {f.scheme === 'self_funded' ? (
                    <Notice>{t('no_repayment')}</Notice>
                  ) : f.scheme === 'outside' ? (
                    <Notice danger>{t('outside_note')}</Notice>
                  ) : (
                    <>
                      <Section icon={Landmark} title={t(f.scheme)} className="scheme">
                        <div className="scheme-facts">
                          <div>
                            <small>{t('rate')}</small>
                            <b>{n(f.annual_rate, 1)}%</b>
                          </div>
                          <div>
                            <small>{t('tenure')}</small>
                            <b>
                              {n(f.tenure_months)} {t('months')}
                            </b>
                          </div>
                          <div>
                            <small>{t('moratorium')}</small>
                            <b>
                              {n(f.moratorium_months)} {t('months')}
                            </b>
                          </div>
                        </div>
                        <p>
                          {t('moratorium_note', {
                            grace: n(f.moratorium_months),
                            first: n(f.moratorium_months + 3),
                            last: n(f.tenure_months),
                          })}
                        </p>
                        <small>{t('interest_assumption')}</small>
                      </Section>
                      {f.cap_applied && <Notice danger>{t('cap_note')}</Notice>}
                    </>
                  )}
                  {report.budget && (
                    <Section icon={Wallet} title={t('starter_inventory') || 'Use of Funds & Starter Inventory'}>
                      <p>{t('inventory_note') || 'Itemized capital expenditure required to establish enterprise operations:'}</p>
                      <dl className="cost-list">
                        {(report.budget.items || []).map((item) => (
                          <div key={item.key}>
                            <dt>
                              {item.key === 'tools'
                                ? t(`tools_${report.business.category}`)
                                : t(`inventory_${item.key}`)}
                              {item.provided && <small> · {t('already_available')}</small>}
                            </dt>
                            <dd>{money(item.amount)}</dd>
                          </div>
                        ))}
                        <div className="total">
                          <dt>{t('project_cost')}</dt>
                          <dd>{money(report.budget.project_cost)}</dd>
                        </div>
                      </dl>
                    </Section>
                  )}

                  <Schemes
                    form={report.input}
                    onProfile={() => {
                      setStage('wizard');
                      setWizardStep(4);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    onUse={async (id) => {
                      await run({ ...report.input, scheme_id: id }, false);
                      setTab('finance');
                      setTimeout(() => {
                        const el = document.getElementById('repayment-schedule-section');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                      }, 150);
                    }}
                  />
                  <Nearby key={`${report.id}-bank`} report={report} mode="bank" scheme={f.scheme} />

                  {f.schedule.length > 0 && (
                    <Section id="repayment-schedule-section" icon={Calculator} title={t('nav_repayment') || 'Loan Repayment & Amortization Schedule'}>
                      <p>
                        {t('selected_scheme')}: <b>{f.scheme_name || t(f.scheme) || f.scheme}</b>
                      </p>

                      {f.loan > 0 && f.loan <= 15000 && (
                        <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '8px', padding: '1rem', marginBottom: '1.25rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, color: '#166534', marginBottom: '4px' }}>
                            <span>💡</span> Small Capital Gap ({money(f.loan)}) — Quick 3–6 Month Operating Clearance Viable
                          </div>
                          <p style={{ margin: 0, fontSize: '0.88rem', color: '#14532d', lineHeight: 1.5 }}>
                            {t('small_gap_guidance', { amount: money(f.loan), payment: money(f.loan / 3) })}
                          </p>
                        </div>
                      )}

                      <div className="schedule-summary" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1rem' }}>
                        <span>
                          {t('total_interest')}: <b>{money(f.total_interest)}</b>
                        </span>
                        <span>
                          {t('total_repayment')}: <b>{money(f.total_repayment)}</b>
                        </span>
                        <button type="button" onClick={download}>
                          <Icon as={Download} />
                          {t('csv') || 'Export CSV'}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (saveRepaymentPlan(report)) {
                              setTab('tracker');
                            } else setStorageError(true);
                          }}
                        >
                          <Icon as={BookOpen} />
                          {t('track_plan') || 'Track in Daily Accounts'}
                        </button>
                      </div>
                      <div className="table-wrap repayment-table" tabIndex={0}>
                        <table>
                          <caption>{t('schedule')}</caption>
                          <thead>
                            <tr>
                              {[
                                'month',
                                'due_date',
                                'opening',
                                'interest',
                                'principal',
                                'payment',
                                'balance',
                              ].map((k) => (
                                <th scope="col" key={k}>
                                  {t(k)}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {(f.schedule || []).slice(0, 12).map((row) => (
                              <tr key={row.month} className={row.moratorium ? 'grace-row' : ''}>
                                <th scope="row">
                                  {n(row.month)}
                                  {row.moratorium && <small>{t('grace')}</small>}
                                </th>
                                <td>{date(row.due_date)}</td>
                                {['opening', 'interest', 'principal', 'payment', 'balance'].map(
                                  (k) => (
                                    <td key={k}>{money(row[k])}</td>
                                  )
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {(f.schedule || []).length > 12 && (
                        <small style={{ color: '#64748b' }}>{t('schedule_preview_note')}</small>
                      )}
                    </Section>
                  )}
                  <Section icon={TrendingUp} title={t('projection')}>
                    <p>{t('projection_note')}</p>
                    <div className="projection-chart" role="img" aria-label={t('projection')}>
                      <div className="chart-legend">
                        <span className="sales">{t('revenue')}</span>
                        <span className="cost">{t('costs')}</span>
                      </div>
                      <div className="chart-bars">
                        {(m?.projection || []).map((row) => (
                          <div className="chart-column" key={row.month}>
                            <div className="bar-pair">
                              <i
                                style={{
                                  height: `${Math.max(2, (row.revenue / Math.max(...(m.projection || []).flatMap((x) => [x.revenue, x.costs]), 1)) * 120)}px`,
                                }}
                              />
                              <i
                                style={{
                                  height: `${Math.max(2, (row.costs / Math.max(...(m.projection || []).flatMap((x) => [x.revenue, x.costs]), 1)) * 120)}px`,
                                }}
                              />
                            </div>
                            <span>{n(row.month)}</span>
                          </div>
                        ))}
                      </div>
                      <small>{t('month')}</small>
                    </div>
                    <details className="print-open">
                      <summary>
                        {t('projection')} · {t('monthly')}
                      </summary>
                      <div className="table-wrap" tabIndex={0}>
                        <table>
                          <caption>{t('projection')}</caption>
                          <thead>
                            <tr>
                              {['month', 'revenue', 'costs', 'repayment', 'cash', 'balance'].map(
                                (k) => (
                                  <th scope="col" key={k}>
                                    {t(k)}
                                  </th>
                                )
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {(m?.projection || []).map((row) => (
                              <tr key={row.month}>
                                {['month', 'revenue', 'costs', 'repayment', 'cash', 'balance'].map(
                                  (k) => (
                                    <td key={k}>{k === 'month' ? n(row[k]) : money(row[k])}</td>
                                  )
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </details>
                  </Section>
                </div>
              </div>
            )}
            {!report && tab === 'finance' && (
              <div className="empty">
                <Icon as={Calculator} size={48} />
                <h1>{t('empty')}</h1>
                <button className="primary" onClick={() => setTab('plan')}>
                  {t('back')}
                  <Icon as={ArrowRight} />
                </button>
              </div>
            )}
            <div className={`report-section sources ${tab !== 'sources' ? 'screen-hidden' : ''}`}>
              <div className="section-intro">
                <div>
                  <div className="eyebrow">03 · {t('nav_sources')}</div>
                  <h1>{t('sources_title')}</h1>
                  <p>{t('sources_intro')}</p>
                </div>
              </div>
              <div className="report-grid">
                <Section icon={MapPin} title={t('coverage')}>
                  <p>
                    {coverage
                      ? t('coverage_detail', {
                          districts: n(coverage.districts),
                          blocks: n(coverage.blocks),
                          villages: n(coverage.villages),
                        })
                      : t('data_unavailable')}
                  </p>
                  <small>{t('named_places')}</small>
                  <div className="district-chips">
                    {(coverage?.district_list || []).map((d) => (
                      <span key={d.id}>{d?.names?.[lang] || d?.names?.en || d?.id}</span>
                    ))}
                  </div>
                </Section>
                <Section icon={BookOpen} title={t('nav_sources')}>
                  <ul className="sources-list">
                    {sourceLinks.map(([key, url]) => (
                      <li key={key}>
                        <a href={url} target="_blank" rel="noreferrer">
                          {t(key)} ↗
                        </a>
                      </li>
                    ))}
                    <li>{t('source_priors')}</li>
                  </ul>
                  <small>{t('source_date')}</small>
                </Section>
                <Section icon={Info} title={t('assumptions')}>
                  <ul className="assumptions">
                    {['population', 'market', 'cost'].map((k) => (
                      <li key={k}>{t(`assumptions_${k}`)}</li>
                    ))}
                  </ul>
                  <p>{t('interest_assumption')}</p>
                </Section>
                <Section icon={ShieldCheck} title={t('model_title')}>
                  <p>{t('model_desc')}</p>
                  {coverage?.metrics && (
                    <Notice>
                      {t('model_metric', {
                        count: n(coverage.metrics.holdout),
                        accuracy: n(coverage.metrics.accuracy * 100, 1) + '%',
                      })}
                    </Notice>
                  )}
                  {report && (
                    <>
                      <p>
                        {t('confidence')}:{' '}
                        {report.business.confidence === null
                          ? t('category')
                          : n((report.business.confidence || 0) * 100, 1) + '%'}
                      </p>
                      <h3>{t('retrieved')}</h3>
                      <ul>
                        {(report.retrieval || []).map((r) => (
                          <li key={r.id}>
                            {r.source === 'nabard' ? (
                              <a target="_blank" rel="noreferrer" href={`${r.url}#page=${r.page}`}>
                                {t('source_nabard')} · {t('page')} {n(r.page)}
                              </a>
                            ) : (
                              t(r.source === 'nsfdc' ? 'source_scheme' : 'source_priors')
                            )}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </Section>
              </div>
              <Section icon={Database} title={t('dataset_title')}>
                <p>{t('dataset_intro')}</p>
                <div className="dataset-grid">
                  {[
                    ['villages', '2024-09', 'official'],
                    ['districts', '2024-09', 'official'],
                    ['sectors', '2024-09', 'synthetic'],
                    ['knowledge', '2024-09', 'official'],
                    ['schemes', '2024-09', 'official'],
                    ['classifier', '2024-09', 'synthetic'],
                  ].map(([key, snap, kind]) => (
                    <div className="dataset-card" key={key}>
                      <h3>
                        <Icon as={Database} size={16} />
                        {t(`dataset_${key}`)}
                      </h3>
                      <small>{t('dataset_date', { date: snap })}</small>
                      <span className="badge">{t(`dataset_${kind}`)}</span>
                    </div>
                  ))}
                </div>
                <small>{t('dataset_refresh_note')}</small>
              </Section>
            </div>
          </>
        )}
        <details className="language-roadmap">
          <summary>{t('more_languages')}</summary>
          <p>{t('language_roadmap')}</p>
        </details>
      </main>
      <NavHelper
        navigate={(key) => {
          setStage('app');
          setTab(key);
        }}
      />
      <footer>
        <span>
          <Icon as={Sprout} />
          {t('footer')}
        </span>
        <span>{t(online ? 'online' : 'offline')}</span>
      </footer>
    </>
  );
}
