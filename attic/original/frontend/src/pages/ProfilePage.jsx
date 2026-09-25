import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { User, Building2, Save, Edit3, CheckCircle } from 'lucide-react';

const containerVariants = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);

  const [profileData, setProfileData] = useState(() => {
    try {
      const savedProf = localStorage.getItem('gramsahayak_profile');
      if (savedProf) return JSON.parse(savedProf);
    } catch (e) {
      console.error(e);
    }
    return {
      name: user?.displayName || 'Entrepreneur',
      phone: '',
      email: user?.email || '',
      community: 'General',
      businessName: '',
      businessType: '',
      location: '',
      registration: '',
    };
  });

  const handleChange = (field, value) => {
    setProfileData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    localStorage.setItem('gramsahayak_profile', JSON.stringify(profileData));
    setEditing(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="max-w-3xl mx-auto space-y-6">
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">{t('profile.title')}</h1>
        <p className="text-white/40">Manage your entrepreneur profile, social category, and enterprise details</p>
      </motion.div>

      {/* Avatar Section */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-8 flex flex-col sm:flex-row items-center gap-6">
          <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center shadow-lg flex-shrink-0">
            <span className="text-3xl font-black text-white">
              {profileData.name ? profileData.name[0].toUpperCase() : 'E'}
            </span>
          </div>
          <div className="text-center sm:text-left min-w-0 flex-1">
            <h2 className="text-xl font-bold text-white truncate">{profileData.name}</h2>
            <p className="text-sm text-white/40 truncate">{profileData.email || 'No email registered'}</p>
            <p className="text-xs text-white/30 mt-1 truncate">
              {profileData.businessName ? `${profileData.businessName} · ` : ''}{profileData.location || 'Location Not Set'}
            </p>
          </div>
          <button
            onClick={() => editing ? handleSave() : setEditing(true)}
            className={`btn btn-sm ${editing ? 'btn-accent' : 'btn-outline'} cursor-pointer`}
            id="edit-profile-btn"
          >
            {editing ? <><Save size={14} /> {t('profile.save')}</> : <><Edit3 size={14} /> {t('profile.edit')}</>}
          </button>
        </div>
      </motion.div>

      {saved && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 p-3 rounded-xl bg-success-500/10 border border-success-500/20 text-success-400 text-sm"
        >
          <CheckCircle size={16} />
          {t('profile.saved_success')}
        </motion.div>
      )}

      {/* Personal Info */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <User size={20} className="text-primary-400" />
            {t('profile.personal_info')}
          </h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="input-label">{t('profile.name')}</label>
              {editing ? (
                <input
                  type="text"
                  value={profileData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="input-field"
                />
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.name || '-'}
                </p>
              )}
            </div>

            <div>
              <label className="input-label">{t('profile.phone')}</label>
              {editing ? (
                <input
                  type="tel"
                  placeholder="+91 98765 43210"
                  value={profileData.phone}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  className="input-field"
                />
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.phone || '-'}
                </p>
              )}
            </div>

            <div>
              <label className="input-label">{t('profile.email')}</label>
              {editing ? (
                <input
                  type="email"
                  value={profileData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  className="input-field"
                />
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.email || '-'}
                </p>
              )}
            </div>

            <div>
              <label className="input-label">{t('profile.community')}</label>
              {editing ? (
                <select
                  value={profileData.community}
                  onChange={(e) => handleChange('community', e.target.value)}
                  className="input-field"
                >
                  <option value="General">General</option>
                  <option value="OBC">Other Backward Classes (OBC)</option>
                  <option value="SC">Scheduled Caste (SC)</option>
                  <option value="ST">Scheduled Tribe (ST)</option>
                  <option value="Minority">Minority Community</option>
                  <option value="Women">Women Entrepreneur</option>
                </select>
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.community || '-'}
                </p>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Business Info */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Building2 size={20} className="text-accent-400" />
            {t('profile.business_info')}
          </h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="input-label">{t('profile.business_name')}</label>
              {editing ? (
                <input
                  type="text"
                  placeholder="Proposed / Registered Entity Name"
                  value={profileData.businessName}
                  onChange={(e) => handleChange('businessName', e.target.value)}
                  className="input-field"
                />
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.businessName || 'Not yet specified'}
                </p>
              )}
            </div>

            <div>
              <label className="input-label">{t('profile.business_type')}</label>
              {editing ? (
                <input
                  type="text"
                  placeholder="e.g., Retail Store, Food Processing"
                  value={profileData.businessType}
                  onChange={(e) => handleChange('businessType', e.target.value)}
                  className="input-field"
                />
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.businessType || 'Not yet specified'}
                </p>
              )}
            </div>

            <div>
              <label className="input-label">{t('profile.location')}</label>
              {editing ? (
                <input
                  type="text"
                  placeholder="Village / Block / District"
                  value={profileData.location}
                  onChange={(e) => handleChange('location', e.target.value)}
                  className="input-field"
                />
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.location || 'Not yet specified'}
                </p>
              )}
            </div>

            <div>
              <label className="input-label">{t('profile.registration')}</label>
              {editing ? (
                <input
                  type="text"
                  placeholder="Udyam / MSME Registration (Optional)"
                  value={profileData.registration}
                  onChange={(e) => handleChange('registration', e.target.value)}
                  className="input-field"
                />
              ) : (
                <p className="text-sm text-white/80 py-3 px-4 rounded-xl bg-white/3 border border-white/5">
                  {profileData.registration || 'None'}
                </p>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
