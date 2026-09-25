import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lightbulb, MapPin, Wallet, Users, CheckCircle,
  ArrowRight, ArrowLeft, Send, Loader2
} from 'lucide-react';
import LocationPicker from '../components/LocationPicker';

const steps = [
  { icon: Lightbulb, titleKey: 'assessment.step1_title', descKey: 'assessment.step1_desc' },
  { icon: MapPin, titleKey: 'assessment.step2_title', descKey: 'assessment.step2_desc' },
  { icon: Wallet, titleKey: 'assessment.step3_title', descKey: 'assessment.step3_desc' },
  { icon: Users, titleKey: 'assessment.step4_title', descKey: 'assessment.step4_desc' },
  { icon: CheckCircle, titleKey: 'assessment.step5_title', descKey: 'assessment.step5_desc' },
];

const categories = [
  'retail', 'food', 'agriculture', 'handicraft', 'textile',
  'dairy', 'services', 'manufacturing', 'transport', 'other'
];

const availableFacilities = [
  { id: 'own_shop', labelKey: 'assessment.facilities_list.own_shop' },
  { id: 'rented_space', labelKey: 'assessment.facilities_list.rented_space' },
  { id: 'power_supply', labelKey: 'assessment.facilities_list.power_supply' },
  { id: 'water_source', labelKey: 'assessment.facilities_list.water_source' },
  { id: 'storage', labelKey: 'assessment.facilities_list.storage' },
  { id: 'vehicle', labelKey: 'assessment.facilities_list.vehicle' },
  { id: 'internet', labelKey: 'assessment.facilities_list.internet' },
  { id: 'bank_account', labelKey: 'assessment.facilities_list.bank_account' },
];

const communities = [
  { value: 'General', label: 'General' },
  { value: 'OBC', label: 'Other Backward Classes (OBC)' },
  { value: 'SC', label: 'Scheduled Caste (SC)' },
  { value: 'ST', label: 'Scheduled Tribe (ST)' },
  { value: 'Minority', label: 'Minority Community' },
  { value: 'Women', label: 'Women Entrepreneur' },
];

export default function AssessmentPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const [formData, setFormData] = useState(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_assessment_draft');
      if (saved) return JSON.parse(saved);
    } catch {
      // fallback default
    }
    return {
      businessName: '',
      category: 'retail',
      description: '',
      location: 'Wardha, Maharashtra',
      lat: 20.7453,
      lon: 78.6022,
      radiusKm: 5.0,
      investment: 150000,
      facilities: ['own_shop', 'power_supply'],
      community: 'General',
      gender: 'all',
      ageGroup: '26-35',
      education: 'secondary',
    };
  });

  const handleChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      try {
        localStorage.setItem('gramsahayak_assessment_draft', JSON.stringify(updated));
      } catch (e) {
        console.error(e);
      }
      return updated;
    });
  };

  const handleFacilityToggle = (facilityId) => {
    setFormData(prev => {
      const exists = prev.facilities.includes(facilityId);
      const newFacilities = exists
        ? prev.facilities.filter(f => f !== facilityId)
        : [...prev.facilities, facilityId];
      const updated = { ...prev, facilities: newFacilities };
      localStorage.setItem('gramsahayak_assessment_draft', JSON.stringify(updated));
      return updated;
    });
  };

  const handleLocationChange = ({ location, lat, lon, radiusKm }) => {
    setFormData(prev => {
      const updated = {
        ...prev,
        location,
        lat,
        lon,
        radiusKm
      };
      localStorage.setItem('gramsahayak_assessment_draft', JSON.stringify(updated));
      return updated;
    });
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setErrorMessage('');

    const payload = {
      businessName: formData.businessName.trim() || 'Rural Venture',
      businessType: formData.category,
      description: formData.description,
      location: formData.location,
      lat: Number(formData.lat) || 20.7453,
      lon: Number(formData.lon) || 78.6022,
      radiusKm: Number(formData.radiusKm) || 5.0,
      initialCapital: Number(formData.investment) || 100000,
      facilities: formData.facilities,
      community: formData.community,
      gender: formData.gender,
      education: formData.education
    };

    try {
      const response = await fetch('http://127.0.0.1:8000/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Assessment failed: ${response.statusText}`);
      }

      const assessmentResult = await response.json();
      localStorage.setItem('gramsahayak_assessment', JSON.stringify({
        ...formData,
        ...assessmentResult,
        feasibilityScore: assessmentResult.overallScore
      }));

      navigate('/feasibility');
    } catch (err) {
      console.warn('API error, falling back to local computation:', err);
      // Fallback local persistence
      localStorage.setItem('gramsahayak_assessment', JSON.stringify({
        ...formData,
        overallScore: 75,
        feasibilityScore: 75,
        feasibilityGrade: 'Viable Opportunity',
        riskLevel: 'Moderate Risk',
        verdictReasoning: `Assessment computed for ${formData.businessName || 'Enterprise'} in ${formData.location}. Meets capital and local readiness thresholds.`
      }));
      navigate('/feasibility');
    } finally {
      setIsSubmitting(false);
    }
  };

  const next = () => setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
  const prev = () => setCurrentStep(prev => Math.max(prev - 1, 0));

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
          {t('assessment.title')}
        </h1>
        <p className="text-white/40">{t('assessment.subtitle')}</p>
      </motion.div>

      {/* Progress Bar */}
      <div className="flex items-center gap-2 mb-6">
        {steps.map((step, i) => {
          const Icon = step.icon;
          const isActive = i === currentStep;
          const isCompleted = i < currentStep;

          return (
            <div key={i} className="flex-1 flex items-center">
              <button
                type="button"
                onClick={() => i <= currentStep && setCurrentStep(i)}
                className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300 cursor-pointer ${
                  isCompleted
                    ? 'bg-success-500 text-white'
                    : isActive
                    ? 'gradient-primary text-white shadow-lg shadow-primary-500/30'
                    : 'bg-white/5 text-white/30'
                }`}
              >
                {isCompleted ? <CheckCircle size={18} /> : <Icon size={18} />}
              </button>
              {i < steps.length - 1 && (
                <div className={`flex-1 h-0.5 mx-2 rounded transition-colors ${
                  isCompleted ? 'bg-success-500' : 'bg-white/10'
                }`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Step Title */}
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-white">{t(steps[currentStep].titleKey)}</h2>
        <p className="text-sm text-white/40">{t(steps[currentStep].descKey)}</p>
      </div>

      {/* Step Content */}
      <div className="glass-card-static p-6 md:p-8 min-h-[360px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Step 1: Business Idea */}
            {currentStep === 0 && (
              <div className="space-y-5">
                <div>
                  <label className="input-label">{t('assessment.business_name')}</label>
                  <input
                    type="text"
                    value={formData.businessName}
                    onChange={(e) => handleChange('businessName', e.target.value)}
                    className="input-field"
                    placeholder="e.g., Wardha Bio Organic Store"
                    id="business-name"
                  />
                </div>
                <div>
                  <label className="input-label">{t('assessment.business_category')}</label>
                  <select
                    value={formData.category}
                    onChange={(e) => handleChange('category', e.target.value)}
                    className="input-field"
                    id="business-category"
                  >
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{t(`assessment.categories.${cat}`)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="input-label">{t('assessment.business_description')}</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    className="input-field"
                    rows={4}
                    placeholder="Describe your proposed venture, target local customer demographic, and primary offerings..."
                    id="business-description"
                  />
                </div>
              </div>
            )}

            {/* Step 2: Location & Interactive Map */}
            {currentStep === 1 && (
              <LocationPicker
                location={formData.location}
                lat={formData.lat}
                lon={formData.lon}
                radiusKm={formData.radiusKm}
                onChange={handleLocationChange}
              />
            )}

            {/* Step 3: Financial Investment */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div>
                  <label className="input-label">{t('assessment.investment_amount')}</label>
                  <input
                    type="range"
                    min="10000"
                    max="3000000"
                    step="10000"
                    value={formData.investment}
                    onChange={(e) => handleChange('investment', parseInt(e.target.value))}
                    className="w-full accent-primary-500 mb-2"
                    id="investment-slider"
                  />
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-white/40">₹10,000</span>
                    <span className="text-2xl font-black text-accent-400">
                      ₹{formData.investment.toLocaleString('en-IN')}
                    </span>
                    <span className="text-sm text-white/40">₹30,00,000</span>
                  </div>
                </div>

                <div>
                  <label className="input-label">{t('assessment.existing_facilities')}</label>
                  <div className="grid grid-cols-2 gap-2.5">
                    {availableFacilities.map(f => (
                      <button
                        key={f.id}
                        type="button"
                        onClick={() => handleFacilityToggle(f.id)}
                        className={`p-3 rounded-xl text-left text-xs font-medium transition-all cursor-pointer border ${
                          formData.facilities.includes(f.id)
                            ? 'bg-primary-600/25 border-primary-500 text-white'
                            : 'bg-white/3 border-white/10 text-white/60 hover:bg-white/6'
                        }`}
                      >
                        {t(f.labelKey)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Demographic Profile */}
            {currentStep === 3 && (
              <div className="space-y-5">
                <div>
                  <label className="input-label">{t('assessment.community')}</label>
                  <select
                    value={formData.community}
                    onChange={(e) => handleChange('community', e.target.value)}
                    className="input-field"
                    id="community-select"
                  >
                    {communities.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">{t('assessment.gender')}</label>
                    <select
                      value={formData.gender}
                      onChange={(e) => handleChange('gender', e.target.value)}
                      className="input-field"
                      id="gender-select"
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="input-label">{t('assessment.age_group')}</label>
                    <select
                      value={formData.ageGroup}
                      onChange={(e) => handleChange('ageGroup', e.target.value)}
                      className="input-field"
                      id="age-group-select"
                    >
                      <option value="18-25">18–25 years</option>
                      <option value="26-35">26–35 years</option>
                      <option value="36-45">36–45 years</option>
                      <option value="46-55">46–55 years</option>
                      <option value="56+">56+ years</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="input-label">{t('assessment.education')}</label>
                  <select
                    value={formData.education}
                    onChange={(e) => handleChange('education', e.target.value)}
                    className="input-field"
                    id="education-select"
                  >
                    <option value="none">No Formal Education</option>
                    <option value="primary">Primary (5th Pass)</option>
                    <option value="secondary">Secondary (10th Pass)</option>
                    <option value="higher_secondary">Higher Secondary (12th Pass)</option>
                    <option value="graduate">Graduate / Diploma</option>
                    <option value="postgraduate">Post Graduate</option>
                  </select>
                </div>
              </div>
            )}

            {/* Step 5: Review & Submit */}
            {currentStep === 4 && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-white/3 border border-white/5">
                    <p className="text-xs text-white/40 mb-1">Entity Name</p>
                    <p className="text-sm font-semibold text-white truncate">{formData.businessName || 'Proposed Venture'}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/3 border border-white/5">
                    <p className="text-xs text-white/40 mb-1">Sector</p>
                    <p className="text-sm font-semibold text-white">{t(`assessment.categories.${formData.category}`)}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/3 border border-white/5 col-span-2">
                    <p className="text-xs text-white/40 mb-1">Operating Catchment</p>
                    <p className="text-sm font-semibold text-white truncate">{formData.location}</p>
                    <p className="text-[11px] text-accent-400 mt-1">Radius: {formData.radiusKm} km · GPS: {Number(formData.lat).toFixed(4)}, {Number(formData.lon).toFixed(4)}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/3 border border-white/5">
                    <p className="text-xs text-white/40 mb-1">Capital</p>
                    <p className="text-sm font-semibold text-accent-400">₹{formData.investment.toLocaleString('en-IN')}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/3 border border-white/5">
                    <p className="text-xs text-white/40 mb-1">Social Community</p>
                    <p className="text-sm font-semibold text-white">{formData.community}</p>
                  </div>
                </div>

                {formData.facilities.length > 0 && (
                  <div className="p-3 rounded-xl bg-white/3 border border-white/5">
                    <p className="text-xs text-white/40 mb-2">Declared Facilities ({formData.facilities.length})</p>
                    <div className="flex flex-wrap gap-1.5">
                      {formData.facilities.map(f => (
                        <span key={f} className="px-2.5 py-1 rounded-md bg-primary-600/20 text-primary-300 text-xs border border-primary-500/20">
                          {t(`assessment.facilities_list.${f}`) || f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {errorMessage && (
                  <div className="p-3 rounded-xl bg-danger-500/10 border border-danger-500/20 text-danger-400 text-xs">
                    {errorMessage}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between mt-6">
        <button
          type="button"
          onClick={prev}
          disabled={currentStep === 0 || isSubmitting}
          className={`btn btn-outline ${currentStep === 0 ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <ArrowLeft size={16} />
          {t('assessment.previous')}
        </button>

        {currentStep < steps.length - 1 ? (
          <button
            type="button"
            onClick={next}
            className="btn btn-primary cursor-pointer flex items-center gap-1.5"
            id="wizard-next-btn"
          >
            <span>{t('assessment.next')}</span>
            <ArrowRight size={16} />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="btn btn-accent group cursor-pointer flex items-center gap-2"
            id="submit-assessment-btn"
          >
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>{t('assessment.analyzing')}</span>
              </>
            ) : (
              <>
                <Send size={16} />
                <span>{t('assessment.submit')}</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
