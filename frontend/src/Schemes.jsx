import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from './api';

// Backend (schemes.py) emits "reasons.<field>_mismatch" for any eligibility
// field (age, gender, community, religion, sector, ...), plus a handful of
// fixed keys (reasons.sector_mismatch, reasons.income_above, ...). Rather
// than hardcode English text per field, translate the fixed keys directly
// via i18n and build the generic "<field> requirement not met" sentence
// from a field-name translation table (field.*) for everything else, so a
// new eligibility field in scheme_catalog.json is translated automatically.
function reasonLabel(t, k) {
  const direct = t(k, { defaultValue: '' });
  if (direct) return direct;
  const m = /^reasons\.(.+)_mismatch$/.exec(k);
  if (m) {
    const fieldName = t(`field.${m[1]}`, { defaultValue: m[1].replace(/_/g, ' ') });
    return t('reason_mismatch', { field: fieldName });
  }
  return k.replace(/^reasons\./, '').replace(/_/g, ' ');
}

function missingLabel(t, k) {
  const fieldName = t(`field.${k}`, { defaultValue: k.replace(/_/g, ' ') });
  return `${t('need_details')}: ${fieldName}`;
}

export default function Schemes({ form, onUse, onProfile }) {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState([]),
    [status, setStatus] = useState('all'),
    [community, setCommunity] = useState('all'),
    [gender, setGender] = useState('all'),
    [error, setError] = useState(false);

  const money = (v) =>
    new Intl.NumberFormat(`${i18n.language}-IN`, {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(v);

  useEffect(() => {
    let stale = false;
    setError(false);
    api('/schemes', {
      ...form,
      margin: Number(form.margin),
      location: form.location || 'Tamil Nadu',
      business: form.business || 'other',
    })
      .then((r) => {
        if (!stale) setItems(r.schemes || []);
      })
      .catch(() => {
        if (!stale) setError(true);
      });
    return () => {
      stale = true;
    };
  }, [form]);

  const candidates = items.filter((s) => s.status === 'potential' || s.status === 'eligible');
  const recommended = candidates.find(
    (s) =>
      s.id ===
      (form.community === 'obc'
        ? 'nbcfdc.micro'
        : form.community === 'sc'
          ? 'nsfdc.micro'
          : items.find((x) => x.id === 'mudra.shishu')?.status === 'potential'
            ? 'mudra.shishu'
            : 'pmegp.new')
  );

  const matchesCommunity = (s, comm) => {
    if (comm === 'all') return true;
    const c = s.eligibility?.community ?? s.community;
    if (c === 'any' || c == null) return true;
    if (Array.isArray(c)) return c.includes(comm);
    return c === comm;
  };

  const matchesGender = (s, g) => {
    if (g === 'all') return true;
    const itemG = s.eligibility?.gender ?? s.gender;
    if (itemG === 'any' || itemG == null) return true;
    return itemG === g;
  };

  const visible = items.filter(
    (s) =>
      (status === 'all' || s.status === status) &&
      matchesCommunity(s, community) &&
      matchesGender(s, gender)
  );

  return (
    <section className="scheme-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
        <div>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🏛️</span>
            {t('nav_schemes') || 'Government Credit Schemes & Subsidies'}
          </h2>
          <p style={{ margin: '4px 0 0 0', color: '#475569', fontSize: '0.9rem' }}>
            {t('scheme_intro') || 'Concessional government loan and margin subsidy schemes matched to your profile and sector.'}
          </p>
        </div>
        <button
          type="button"
          onClick={onProfile}
          style={{
            background: '#f1f5f9',
            color: '#1e293b',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            padding: '8px 14px',
            fontWeight: 600,
            cursor: 'pointer',
            fontSize: '0.85rem'
          }}
        >
          👤 {t('check_profile') || 'Update My Profile & Community'}
        </button>
      </div>

      <div className="form-grid" style={{ marginBottom: '1.5rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <div>
          <label htmlFor="scheme-status" style={{ fontWeight: 600, fontSize: '0.85rem' }}>{t('filter_status') || 'Eligibility Status'}</label>
          <select id="scheme-status" value={status} onChange={(e) => setStatus(e.target.value)}>
            {['all', 'potential', 'need_details', 'not_eligible'].map((v) => (
              <option key={v} value={v}>
                {t(v === 'all' ? 'all_schemes' : v)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="scheme-community" style={{ fontWeight: 600, fontSize: '0.85rem' }}>{t('filter_community') || 'Target Community'}</label>
          <select
            id="scheme-community"
            value={community}
            onChange={(e) => setCommunity(e.target.value)}
          >
            {[
              ['all', t('all_communities') || 'All Schemes & Communities'],
              ['sc', t('community_filter_sc')],
              ['obc', t('community_filter_obc')],
              ['st', t('community_filter_st')],
              ['general', t('community_filter_general')],
            ].map(([val, label]) => (
              <option key={val} value={val}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="scheme-gender" style={{ fontWeight: 600, fontSize: '0.85rem' }}>{t('gender') || 'Target Beneficiary'}</label>
          <select id="scheme-gender" value={gender} onChange={(e) => setGender(e.target.value)}>
            {['all', 'female', 'male', 'other_gender'].map((k) => (
              <option key={k} value={k}>
                {t(k === 'all' ? 'all_people' : k)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <p role="alert" style={{ color: '#dc2626' }}>{t('invalid_input')}</p>}

      <div className="report-grid">
        {visible.map((s) => {
          const isEligible = s.status === 'eligible' || s.status === 'potential';
          return (
            <article className={`panel scheme-card ${isEligible ? 'eligible' : ''}`} key={s.id} style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span
                    className="badge"
                    style={{
                      background: isEligible ? '#dcfce7' : s.status === 'need_details' ? '#fef3c7' : '#fee2e2',
                      color: isEligible ? '#166534' : s.status === 'need_details' ? '#92400e' : '#991b1b',
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontSize: '0.75rem'
                    }}
                  >
                    {s.status === 'potential' ? '✓ ' + t('eligible_good_match') : t(s.status) || s.status}
                  </span>
                  {s.terms?.interest_rate != null && (
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#165f49' }}>
                      {(s.terms.interest_rate * (s.terms.interest_rate < 1 ? 100 : 1)).toFixed(1)}% p.a.
                    </span>
                  )}
                </div>

                <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: '#0f172a' }}>
                  {s.name?.[i18n.language] || s.name?.en || t(s.id) || s.id}
                </h3>

                {s.agency && (
                  <p style={{ margin: '0 0 10px 0', fontSize: '0.82rem', color: '#64748b' }}>
                    {t('administered_by')}: <strong>{s.agency}</strong>
                  </p>
                )}

                {recommended?.id === s.id && (
                  <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '6px 10px', borderRadius: '6px', fontSize: '0.82rem', color: '#065f46', marginBottom: '10px' }}>
                    ⭐ <strong>{t('recommended_match')}</strong>
                  </div>
                )}

                <dl className="cost-list" style={{ fontSize: '0.85rem', margin: '0.75rem 0' }}>
                  <div>
                    <dt>{t('community') || 'Target Community'}</dt>
                    <dd>
                      {Array.isArray(s.eligibility?.community)
                        ? s.eligibility.community.map((c) => c.toUpperCase()).join(', ')
                        : (s.eligibility?.community || s.community || t('all_communities_value'))}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('income_limit') || 'Income Ceiling'}</dt>
                    <dd>
                      {(s.eligibility?.income_limit_rural || s.eligibility?.income_limit_urban || s.income_limit)
                        ? t('per_year_value', { amount: money(s.eligibility?.income_limit_rural || s.eligibility?.income_limit_urban || s.income_limit) })
                        : t('no_income_ceiling')}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('loan_cap') || 'Max Loan Support'}</dt>
                    <dd>
                      {(s.terms?.loan_cap || s.loan_cap)
                        ? money(s.terms?.loan_cap || s.loan_cap)
                        : t('project_need_based')}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('tenure') || 'Loan Tenure'}</dt>
                    <dd>
                      {s.terms?.tenure_months ? t('tenure_months_years', { months: s.terms.tenure_months, years: (s.terms.tenure_months/12).toFixed(0) }) : t('standard_bank_tenure')}
                    </dd>
                  </div>
                </dl>

                {((s.reasons && s.reasons.length > 0) || (s.missing && s.missing.length > 0)) && (
                  <div style={{ background: '#fffbeb', border: '1px solid #fef3c7', padding: '8px 10px', borderRadius: '6px', fontSize: '0.8rem', color: '#92400e', margin: '0.5rem 0' }}>
                    <div style={{ fontWeight: 600, marginBottom: '4px' }}>{t('eligibility_checklist')}</div>
                    <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
                      {s.reasons?.map((k) => (
                        <li key={k}>
                          {reasonLabel(t, k)}
                        </li>
                      ))}
                      {s.missing?.map((k) => (
                        <li key={k}>
                          {missingLabel(t, k)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div style={{ marginTop: '1rem', borderTop: '1px solid #e2e8f0', paddingTop: '0.75rem' }}>
                <button
                  type="button"
                  className="primary"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    cursor: isEligible ? 'pointer' : 'not-allowed',
                    opacity: isEligible ? 1 : 0.6
                  }}
                  disabled={!isEligible}
                  onClick={() => onUse(s.id)}
                >
                  ✓ {t('use_scheme') || 'Use this Scheme in My Plan'}
                </button>
                <div className="source-links" style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.8rem' }}>
                  {(s.source_url || s.source) && (
                    <a href={s.source_url || s.source} target="_blank" rel="noreferrer">
                      {t('official_details')} ↗
                    </a>
                  )}
                  {(s.apply_url || s.apply) && (
                    <a href={s.apply_url || s.apply} target="_blank" rel="noreferrer">
                      {t('apply_portal')} ↗
                    </a>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {!visible.length && !error && (
        <div style={{ padding: '2rem', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px dashed #cbd5e1', marginTop: '1rem' }}>
          <p style={{ color: '#64748b', fontSize: '1rem', margin: 0 }}>
            {t('no_scheme_results') || 'No schemes match the selected filters. Change filters or click "Update My Profile" to adjust demographics.'}
          </p>
        </div>
      )}
    </section>
  );
}
