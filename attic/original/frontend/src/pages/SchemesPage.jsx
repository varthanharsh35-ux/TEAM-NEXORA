import { useState, useEffect, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2, Search, Filter, Calculator, ExternalLink,
  IndianRupee, Clock, ShieldCheck, MapPin, Calendar, Check,
  Info, Lock, ArrowRight, X
} from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const bankPinIcon = L.divIcon({
  className: 'custom-bank-pin',
  html: `<div style="background-color: #8b5cf6; width: 28px; height: 28px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(139,92,246,0.4);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M3 21h18M3 10h18M5 10v11M9 10v11M15 10v11M19 10v11M12 2l10 5H2l10-5z"></path></svg></div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -28]
});

const userPinIcon = L.divIcon({
  className: 'custom-user-pin',
  html: `<div style="background-color: #3b5bdb; width: 28px; height: 28px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(59,91,219,0.4);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="10" r="3"></circle></svg></div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -28]
});

const containerVariants = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const itemVariants = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

export default function SchemesPage() {
  const { t } = useTranslation();
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  const [schemes, setSchemes] = useState([]);
  const [banks, setBanks] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [filterCommunity, setFilterCommunity] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [filterAmount, setFilterAmount] = useState(0);
  const [userBusinessType, setUserBusinessType] = useState('retail');

  // EMI Calculator State
  const [emiScheme, setEmiScheme] = useState(null);
  const [calcMode, setCalcMode] = useState('tenure'); // 'tenure' or 'desiredEmi'
  const [emiAmount, setEmiAmount] = useState(100000);
  const [emiTenure, setEmiTenure] = useState(36);
  const [desiredEmi, setDesiredEmi] = useState(3500);
  const [loanStartDate, setLoanStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);

  // Formal Financial Intake Modal (Spec §9 - separate from browsing)
  const [intakeScheme, setIntakeScheme] = useState(null);
  const [intakeData, setIntakeData] = useState({
    cibilScore: 720,
    turnover: 45000,
    accountType: 'current',
    hasConsent: false
  });

  const [userLocation, setUserLocation] = useState({
    lat: 20.7453,
    lon: 78.6022,
    location: 'Wardha, Maharashtra',
    radiusKm: 5.0
  });

  useEffect(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_assessment');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.lat && parsed.lon) {
          setUserLocation({
            lat: Number(parsed.coordinates?.lat || parsed.lat),
            lon: Number(parsed.coordinates?.lon || parsed.lon),
            location: parsed.location || 'Your Catchment',
            radiusKm: Number(parsed.radiusKm || 5.0)
          });
        }
        if (parsed.community) {
          setFilterCommunity(parsed.community.toLowerCase());
        }
        if (parsed.businessType || parsed.category) {
          setUserBusinessType(parsed.businessType || parsed.category);
        }
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Fetch schemes from backend — filtered by business type
  useEffect(() => {
    async function fetchSchemes() {
      try {
        const res = await fetch(`http://127.0.0.1:8000/schemes?businessType=${userBusinessType}`);
        if (res.ok) {
          const data = await res.json();
          setSchemes(data.schemes || []);
        }
      } catch (err) {
        console.warn('Schemes API fallback:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchSchemes();
  }, [userBusinessType]);

  // Fetch nearby banks & post offices
  useEffect(() => {
    async function fetchBanks() {
      try {
        const res = await fetch(`http://127.0.0.1:8000/financial-institutions?lat=${userLocation.lat}&lon=${userLocation.lon}&radiusKm=${userLocation.radiusKm}`);
        if (res.ok) {
          const data = await res.json();
          setBanks(data.institutions || []);
        }
      } catch (err) {
        console.warn('Banks API fallback:', err);
      }
    }
    fetchBanks();
  }, [userLocation]);

  // Leaflet Map for Financial Institutions
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = L.map(mapContainerRef.current, {
      center: [userLocation.lat, userLocation.lon],
      zoom: 13,
      scrollWheelZoom: false
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map);

    const userMarker = L.marker([userLocation.lat, userLocation.lon], { icon: userPinIcon }).addTo(map);
    userMarker.bindPopup(`<b>${t('schemes.your_location')}</b><br/>${userLocation.location}`).openPopup();

    L.circle([userLocation.lat, userLocation.lon], {
      radius: userLocation.radiusKm * 1000,
      color: '#8b5cf6',
      fillColor: '#8b5cf6',
      fillOpacity: 0.08,
      weight: 2,
      dashArray: '5, 5'
    }).addTo(map);

    banks.forEach(b => {
      const bMarker = L.marker([b.lat, b.lon], { icon: bankPinIcon }).addTo(map);
      bMarker.bindPopup(`
        <div style="font-size: 12px;">
          <b style="color: #8b5cf6;">🏛️ ${b.name}</b><br/>
          <span>Distance: ${b.distanceKm} km</span><br/>
          ${b.contact ? `<span>Phone: ${b.contact}</span><br/>` : ''}
          <a href="${b.gmapsUrl}" target="_blank" rel="noopener noreferrer" style="color: #3b5bdb; font-weight: bold; text-decoration: underline;">Open in Google Maps</a>
        </div>
      `);
    });

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [banks, userLocation]);

  // Bidirectional EMI calculation with start date
  useEffect(() => {
    if (!emiScheme) return;

    async function calculateEMI() {
      setCalcLoading(true);
      const params = new URLSearchParams();
      params.append('principal', String(emiAmount));
      params.append('rate', String(emiScheme.interestRate));
      params.append('startDate', loanStartDate);

      if (calcMode === 'desiredEmi') {
        params.append('desiredEmi', String(desiredEmi));
      } else {
        params.append('tenure', String(emiTenure));
      }

      try {
        const res = await fetch(`http://127.0.0.1:8000/schemes/${emiScheme.id}/emi?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          setCalcResult(data);
        }
      } catch (e) {
        console.warn('EMI calc error:', e);
      } finally {
        setCalcLoading(false);
      }
    }

    calculateEMI();
  }, [emiScheme, emiAmount, emiTenure, desiredEmi, calcMode, loanStartDate]);

  const openEMI = (scheme) => {
    setEmiScheme(scheme);
    setEmiAmount(Math.min(scheme.maxAmount, 100000));
    setEmiTenure(scheme.tenure || 36);
    setDesiredEmi(3500);
    setCalcMode('tenure');
    setLoanStartDate(new Date().toISOString().split('T')[0]);
  };

  const filteredSchemes = useMemo(() => {
    return schemes.filter(scheme => {
      const matchSearch = scheme.name.toLowerCase().includes(search.toLowerCase()) ||
                          scheme.fullName.toLowerCase().includes(search.toLowerCase()) ||
                          scheme.eligibility.toLowerCase().includes(search.toLowerCase());

      const matchCommunity = filterCommunity === 'all' ||
                             (scheme.community || []).includes('all') ||
                             (scheme.community || []).some(c => c.toLowerCase() === filterCommunity.toLowerCase());

      const matchType = filterType === 'all' || scheme.category === filterType;
      const matchAmount = filterAmount === 0 || scheme.maxAmount >= filterAmount;

      return matchSearch && matchCommunity && matchType && matchAmount;
    });
  }, [schemes, search, filterCommunity, filterType, filterAmount]);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="max-w-6xl mx-auto space-y-6"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">{t('schemes.title')}</h1>
        <p className="text-white/40">{t('schemes.subtitle')}</p>
      </motion.div>

      {/* Interactive Banks & Post Offices Map */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <MapPin size={18} className="text-purple-400" />
                {t('schemes.banks_map_title')} ({banks.length} {t('common.found')})
              </h3>
              <p className="text-xs text-white/40">{t('schemes.banks_subtitle')} ({userLocation.radiusKm} km around {userLocation.location})</p>
            </div>
          </div>

          <div
            ref={mapContainerRef}
            className="h-64 sm:h-72 rounded-xl overflow-hidden border border-white/10 shadow-inner z-0"
            id="banks-map"
          />

          {/* Banks list */}
          {banks.length > 0 && (
            <div className="grid sm:grid-cols-3 gap-2.5 max-h-40 overflow-y-auto pr-1">
              {banks.map((b, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-white/2 border border-white/5 flex flex-col justify-between">
                  <div>
                    <p className="text-xs font-semibold text-white truncate">{b.name}</p>
                    <p className="text-[11px] text-white/40">{t('common.distance')}: {b.distanceKm} km</p>
                  </div>
                  <a
                    href={b.gmapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1.5 text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium"
                  >
                    <span>{t('schemes.open_in_gmaps')}</span>
                    <ExternalLink size={10} />
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </motion.div>

      {/* Filters — NO CIBIL input here (Spec §6.3) */}
      <motion.div variants={itemVariants} className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-11"
            placeholder={t('schemes.search')}
            id="scheme-search-input"
          />
        </div>

        <select
          value={filterCommunity}
          onChange={(e) => setFilterCommunity(e.target.value)}
          className="input-field w-auto min-w-[150px]"
          id="scheme-community-filter"
        >
          <option value="all">{t('common.all')} {t('schemes.communities')}</option>
          <option value="general">General</option>
          <option value="obc">OBC</option>
          <option value="sc">SC</option>
          <option value="st">ST</option>
          <option value="women">{t('schemes.women')}</option>
          <option value="minority">{t('schemes.minority')}</option>
        </select>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="input-field w-auto min-w-[150px]"
          id="scheme-type-filter"
        >
          <option value="all">{t('common.all')} {t('schemes.categories_label')}</option>
          <option value="microloan">{t('schemes.microloan')}</option>
          <option value="business_loan">{t('schemes.business_credit')}</option>
          <option value="subsidy_grant">{t('schemes.subsidy_grant')}</option>
          <option value="agro_business">{t('schemes.agro_processing')}</option>
          <option value="women_shg">{t('schemes.women_shg')}</option>
        </select>
      </motion.div>

      {/* Schemes Grid */}
      <div className="grid md:grid-cols-2 gap-4">
        {filteredSchemes.map((scheme) => (
          <motion.div key={scheme.id} variants={itemVariants}>
            <div className="glass-card-static p-6 h-full flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-white">{scheme.name}</h3>
                    <p className="text-xs text-white/40">{scheme.fullName}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                    scheme.category === 'subsidy_grant' ? 'bg-success-500/10 text-success-400' :
                    scheme.category === 'microloan' ? 'bg-accent-500/10 text-accent-400' :
                    'bg-primary-500/10 text-primary-400'
                  }`}>
                    {scheme.category.replace('_', ' ')}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2.5 mb-4">
                  <div className="p-2 rounded-lg bg-white/3">
                    <p className="text-[10px] text-white/30">{t('schemes.max_amount')}</p>
                    <p className="text-sm font-bold text-white">₹{(scheme.maxAmount / 100000).toFixed(scheme.maxAmount >= 100000 ? 0 : 1)} {t('schemes.lakh')}</p>
                  </div>
                  <div className="p-2 rounded-lg bg-white/3">
                    <p className="text-[10px] text-white/30">{t('schemes.interest_rate')}</p>
                    <p className="text-sm font-bold text-white">{scheme.interestRate}% p.a.</p>
                  </div>
                  <div className="p-2 rounded-lg bg-white/3">
                    <p className="text-[10px] text-white/30">{t('schemes.max_tenure')}</p>
                    <p className="text-sm font-bold text-white">{scheme.tenure} {t('schemes.months')}</p>
                  </div>
                </div>

                <div className="mb-3">
                  <p className="text-xs font-semibold text-white/50 mb-1">{t('schemes.eligibility')}</p>
                  <p className="text-xs text-white/70 leading-relaxed">{scheme.eligibility}</p>
                </div>

                {/* Eligibility Criteria as Informational Messages (Spec §6.3) */}
                {scheme.eligibilityCriteria && scheme.eligibilityCriteria.length > 0 && (
                  <div className="mb-3 p-3 rounded-lg bg-primary-500/5 border border-primary-500/10 space-y-1.5">
                    <p className="text-[11px] font-bold text-primary-400 flex items-center gap-1">
                      <Info size={12} />
                      {t('schemes.eligibility_requirements')}
                    </p>
                    {scheme.eligibilityCriteria.map((criteria, idx) => (
                      <p key={idx} className="text-[11px] text-white/60 flex items-start gap-1.5">
                        <span className="text-primary-400 mt-0.5">•</span>
                        {criteria}
                      </p>
                    ))}
                  </div>
                )}

                <div className="mb-3">
                  <p className="text-xs font-semibold text-white/50 mb-1">{t('schemes.benefits')}</p>
                  <p className="text-xs text-white/70 leading-relaxed">{scheme.benefits}</p>
                </div>

                {/* Explicit Moratorium Schedule */}
                <div className="mb-4 px-3 py-2 rounded-lg bg-warning-500/5 border border-warning-500/15 flex items-start gap-2">
                  <Clock size={14} className="text-warning-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-warning-400/90 font-medium leading-relaxed">
                    {scheme.moratoriumSchedule || (scheme.moratorium > 0 ? `No payment due for months 1–${scheme.moratorium}. Your first payment begins in month ${scheme.moratorium + 1}.` : 'Repayments start from month 1.')}
                  </p>
                </div>
              </div>

              <div className="flex gap-2 pt-2 border-t border-white/5">
                <button
                  type="button"
                  onClick={() => openEMI(scheme)}
                  className="btn btn-sm btn-outline flex-1 flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Calculator size={14} />
                  <span>{t('schemes.emi_calculator')}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIntakeScheme(scheme)}
                  className="btn btn-sm btn-primary flex-1 flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <span>{t('schemes.proceed_to_apply')}</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {filteredSchemes.length === 0 && (
        <div className="glass-card-static p-12 text-center">
          <Building2 size={40} className="mx-auto text-white/20 mb-3" />
          <p className="text-sm text-white/40">{t('schemes.no_schemes_found')}</p>
        </div>
      )}

      {/* ─── Bidirectional EMI Calculator Modal (Spec §7 Redesign) ─── */}
      <AnimatePresence>
        {emiScheme && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setEmiScheme(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card-static p-6 sm:p-8 max-w-lg w-full space-y-5 max-h-[90vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Calculator size={20} className="text-accent-400" />
                    {t('schemes.emi_calculator')}
                  </h3>
                  <p className="text-xs text-white/40">{emiScheme.name} — {emiScheme.interestRate}% {t('schemes.annual_interest')}</p>
                </div>
                <button
                  onClick={() => setEmiScheme(null)}
                  className="p-1.5 rounded-lg hover:bg-white/5 text-white/40 hover:text-white cursor-pointer"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Mode Switcher */}
              <div className="grid grid-cols-2 gap-1 p-1 bg-white/5 rounded-xl border border-white/5 text-xs">
                <button
                  type="button"
                  onClick={() => setCalcMode('tenure')}
                  className={`py-2.5 rounded-lg font-medium transition-all cursor-pointer ${
                    calcMode === 'tenure' ? 'bg-primary-600 text-white shadow-lg' : 'text-white/50 hover:text-white'
                  }`}
                >
                  {t('schemes.desired_tenure_mode')}
                </button>
                <button
                  type="button"
                  onClick={() => setCalcMode('desiredEmi')}
                  className={`py-2.5 rounded-lg font-medium transition-all cursor-pointer ${
                    calcMode === 'desiredEmi' ? 'bg-accent-600 text-white shadow-lg' : 'text-white/50 hover:text-white'
                  }`}
                >
                  {t('schemes.desired_emi_mode')}
                </button>
              </div>

              {/* Loan Amount */}
              <div>
                <label className="input-label flex justify-between">
                  <span>{t('schemes.loan_amount')}</span>
                  <span className="text-accent-400 font-bold">₹{emiAmount.toLocaleString('en-IN')}</span>
                </label>
                <input
                  type="range"
                  min="10000"
                  max={emiScheme.maxAmount}
                  step="5000"
                  value={emiAmount}
                  onChange={(e) => setEmiAmount(parseInt(e.target.value))}
                  className="w-full accent-accent-500"
                />
              </div>

              {calcMode === 'tenure' ? (
                <div>
                  <label className="input-label flex justify-between">
                    <span>{t('schemes.tenure')}</span>
                    <span className="text-primary-400 font-bold">{emiTenure} {t('schemes.months')}</span>
                  </label>
                  <input
                    type="range"
                    min="6"
                    max={emiScheme.tenure || 60}
                    step="6"
                    value={emiTenure}
                    onChange={(e) => setEmiTenure(parseInt(e.target.value))}
                    className="w-full accent-primary-500"
                  />
                </div>
              ) : (
                <div>
                  <label className="input-label flex justify-between">
                    <span>{t('schemes.target_emi')}</span>
                    <span className="text-accent-400 font-bold">₹{desiredEmi.toLocaleString('en-IN')}/{t('schemes.month_short')}</span>
                  </label>
                  <input
                    type="range"
                    min={Math.round(emiAmount * 0.015)}
                    max={Math.round(emiAmount * 0.2)}
                    step="250"
                    value={desiredEmi}
                    onChange={(e) => setDesiredEmi(parseInt(e.target.value))}
                    className="w-full accent-accent-500"
                  />
                </div>
              )}

              {/* Loan Start Date (Spec §7: explicit, not silently assumed) */}
              <div>
                <label className="input-label flex justify-between">
                  <span>{t('schemes.loan_start_date')}</span>
                  <Calendar size={14} className="text-primary-400" />
                </label>
                <input
                  type="date"
                  value={loanStartDate}
                  onChange={(e) => setLoanStartDate(e.target.value)}
                  className="input-field"
                  id="emi-start-date"
                />
              </div>

              {/* Calculated Outputs */}
              <div className="grid grid-cols-3 gap-2.5 p-4 rounded-xl bg-white/3 border border-white/5 text-center">
                {calcLoading ? (
                  [0, 1, 2].map(i => (
                    <div key={i} className="space-y-2">
                      <div className="h-2.5 bg-white/10 rounded-full animate-pulse mx-auto w-16" />
                      <div className="h-6 bg-white/10 rounded-lg animate-pulse" />
                    </div>
                  ))
                ) : (
                  <>
                    <div>
                      <p className="text-[10px] text-white/40 mb-1">{t('schemes.monthly_emi')}</p>
                      <p className="text-lg font-bold text-accent-400">
                        ₹{calcResult?.monthlyEMI?.toLocaleString('en-IN') || '0'}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-white/40 mb-1">{t('schemes.total_tenure')}</p>
                      <p className="text-lg font-bold text-primary-400">
                        {calcResult?.tenureMonths || emiTenure} {t('schemes.months_short')}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-white/40 mb-1">{t('schemes.total_interest')}</p>
                      <p className="text-sm font-bold text-white">
                        ₹{calcResult?.totalInterest?.toLocaleString('en-IN') || '0'}
                      </p>
                    </div>
                  </>
                )}
              </div>

              {/* Explicit Start/End Date Framing (Spec §7) */}
              {calcResult?.dateFramingStatement && (
                <div className="p-4 rounded-xl bg-primary-500/5 border border-primary-500/15">
                  <p className="text-sm text-primary-300 font-medium leading-relaxed">
                    📅 {calcResult.dateFramingStatement}
                  </p>
                </div>
              )}

              {/* Moratorium Detail — plain language schedule (Spec §7) */}
              <div className="p-3 rounded-xl bg-warning-500/5 border border-warning-500/10 flex items-start gap-2 text-xs text-warning-400">
                <Clock size={14} className="mt-0.5 flex-shrink-0" />
                <span>{calcResult?.moratoriumSchedule || t('schemes.regular_repayment')}</span>
              </div>

              <button
                type="button"
                onClick={() => setEmiScheme(null)}
                className="btn btn-primary w-full cursor-pointer"
              >
                {t('common.close')}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Formal Financial Intake Modal (Spec §9 - separate from browsing) ─── */}
      <AnimatePresence>
        {intakeScheme && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setIntakeScheme(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card-static p-6 sm:p-8 max-w-lg w-full space-y-5 max-h-[90vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <ShieldCheck size={20} className="text-primary-400" />
                    {t('schemes.financial_verification')}
                  </h3>
                  <p className="text-xs text-white/40">{t('schemes.applying_for')}: {intakeScheme.name}</p>
                </div>
                <button
                  onClick={() => setIntakeScheme(null)}
                  className="p-1.5 rounded-lg hover:bg-white/5 text-white/40 hover:text-white cursor-pointer"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Security Notice */}
              <div className="p-3 rounded-xl bg-primary-500/5 border border-primary-500/15 flex items-start gap-2">
                <Lock size={14} className="text-primary-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-primary-300/80 leading-relaxed">
                  {t('schemes.security_notice')}
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs text-white/50 block mb-1">{t('schemes.cibil_score')}</label>
                  <input
                    type="number"
                    min="300"
                    max="900"
                    value={intakeData.cibilScore}
                    onChange={(e) => setIntakeData(p => ({...p, cibilScore: Number(e.target.value)}))}
                    className="input-field"
                    id="intake-cibil"
                  />
                </div>
                <div>
                  <label className="text-xs text-white/50 block mb-1">{t('schemes.monthly_turnover')}</label>
                  <input
                    type="number"
                    value={intakeData.turnover}
                    onChange={(e) => setIntakeData(p => ({...p, turnover: Number(e.target.value)}))}
                    className="input-field"
                    id="intake-turnover"
                  />
                </div>
                <div>
                  <label className="text-xs text-white/50 block mb-1">{t('schemes.bank_account_type')}</label>
                  <select
                    value={intakeData.accountType}
                    onChange={(e) => setIntakeData(p => ({...p, accountType: e.target.value}))}
                    className="input-field"
                    id="intake-account-type"
                  >
                    <option value="current">{t('schemes.business_current')}</option>
                    <option value="savings">{t('schemes.individual_savings')}</option>
                    <option value="jan_dhan">{t('schemes.jan_dhan')}</option>
                  </select>
                </div>
              </div>

              {/* Privacy Consent */}
              <label className="flex items-start gap-2.5 text-xs text-white/60 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={intakeData.hasConsent}
                  onChange={(e) => setIntakeData(p => ({...p, hasConsent: e.target.checked}))}
                  className="mt-0.5 accent-primary-500"
                  id="intake-consent"
                />
                <span>{t('schemes.consent_text')}</span>
              </label>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setIntakeScheme(null)}
                  className="btn btn-outline flex-1 cursor-pointer"
                >
                  {t('common.cancel')}
                </button>
                <a
                  href={intakeScheme.applyUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`btn btn-primary flex-1 flex items-center justify-center gap-1.5 ${!intakeData.hasConsent ? 'opacity-40 pointer-events-none' : ''}`}
                >
                  <span>{t('schemes.submit_application')}</span>
                  <ExternalLink size={14} />
                </a>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
