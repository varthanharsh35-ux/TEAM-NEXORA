import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  GitCompare,
  Trash2,
  Plus,
  TrendingUp,
  AlertTriangle,
  Wallet,
  ShieldCheck,
} from 'lucide-react';
import { persist, restore } from './api';

export default function Compare({ report, history }) {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState(() => restore('gs-compare', []));
  const [error, setError] = useState('');
  const money = (v) =>
    new Intl.NumberFormat(`${i18n.language}-IN`, {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(v);
  const n = (v, d = 0) =>
    new Intl.NumberFormat(`${i18n.language}-IN`, { maximumFractionDigits: d }).format(v);

  function add(r) {
    if (!r) return;
    if (items.length >= 3) {
      setError('compare_max');
      return;
    }
    if (items.find((x) => x.id === r.id)) {
      setError('compare_exists');
      return;
    }
    const entry = {
      id: r.id,
      name: r.input.business_name || t(`sector.${r.business.category}`),
      category: r.business.category,
      location: r.input.location,
      margin: r.input.margin,
      project_cost: r.finance.project_cost,
      loan: r.finance.loan,
      funding_gap: r.finance.funding_gap,
      quarterly_payment: r.finance.quarterly_payment,
      total_repayment: r.finance.total_repayment,
      total_interest: r.finance.total_interest,
      scheme: r.finance.scheme,
      annual_rate: r.finance.annual_rate,
      tenure_months: r.finance.tenure_months,
      moratorium_months: r.finance.moratorium_months,
      revenue: r.metrics.revenue,
      monthly_cost: r.metrics.monthly_cost,
      operating_profit: r.metrics.operating_profit,
      net_after_debt: r.metrics.net_after_debt,
      working_capital: r.metrics.working_capital,
      working_gap: r.metrics.working_gap,
      competitors: r.metrics.competitors,
      break_even_units: r.metrics.break_even_units,
      downside_profit: r.metrics.downside_profit,
      households: r.metrics.households,
      verdict: r.verdict,
      readiness_score: r.readiness?.score ?? 0,
      missing_facilities: r.readiness?.missing || [],
      created_at: r.created_at,
    };
    const next = [...items, entry];
    if (!persist('gs-compare', next)) {
      setError('storage_error');
      return;
    }
    setItems(next);
    setError('');
  }

  function remove(id) {
    const next = items.filter((x) => x.id !== id);
    persist('gs-compare', next);
    setItems(next);
    setError('');
  }

  function clear() {
    persist('gs-compare', []);
    setItems([]);
    setError('');
  }

  // Find best values for highlighting
  const best =
    items.length >= 2
      ? {
          project_cost: Math.min(...items.map((x) => x.project_cost)),
          net_after_debt: Math.max(...items.map((x) => x.net_after_debt)),
          quarterly_payment: Math.min(
            ...items.filter((x) => x.quarterly_payment > 0).map((x) => x.quarterly_payment)
          ),
          funding_gap: Math.min(...items.map((x) => x.funding_gap)),
          readiness_score: Math.max(...items.map((x) => x.readiness_score)),
        }
      : null;

  const available = (history || []).filter((r) => !items.find((x) => x.id === r.id));

  return (
    <section className="compare-page">
      <h1>
        <GitCompare size={28} strokeWidth={1.8} /> {t('nav_compare')}
      </h1>
      <p>{t('compare_intro')}</p>

      {error && (
        <p role="alert" className="compare-error">
          {t(error)}
        </p>
      )}

      <div className="compare-add">
        {report && !items.find((x) => x.id === report.id) && (
          <button className="primary" onClick={() => add(report)}>
            <Plus size={18} /> {t('compare_add_current')}
          </button>
        )}
        {available.length > 0 && (
          <details className="compare-history">
            <summary>{t('compare_add_history')}</summary>
            <div className="compare-history-list">
              {available.slice(0, 10).map((r) => (
                <button key={r.id} onClick={() => add(r)}>
                  <Plus size={16} /> {r.input.business_name || t(`sector.${r.business.category}`)} ·{' '}
                  {r.input.location}
                </button>
              ))}
            </div>
          </details>
        )}
      </div>

      {items.length === 0 && (
        <div className="compare-empty">
          <GitCompare size={48} strokeWidth={1} />
          <p>{t('compare_empty')}</p>
        </div>
      )}

      {items.length >= 1 && (
        <>
          <div className="compare-actions">
            <span>{t('compare_count', { count: n(items.length), max: n(3) })}</span>
            <button onClick={clear}>
              <Trash2 size={16} /> {t('compare_clear')}
            </button>
          </div>

          {/* Comparison grid */}
          <div className="compare-grid" style={{ '--cols': items.length }}>
            {/* Headers */}
            {items.map((item) => (
              <div className="compare-header" key={item.id}>
                <h2>{item.name}</h2>
                <small>{item.location}</small>
                <span className={`badge ${item.verdict}`}>{t(item.verdict)}</span>
                <button
                  className="compare-remove"
                  onClick={() => remove(item.id)}
                  title={t('compare_remove')}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}

            {/* Readiness */}
            <div className="compare-section-label" style={{ gridColumn: `1 / -1` }}>
              <ShieldCheck size={18} /> {t('plan_readiness')}
            </div>
            {items.map((item) => (
              <div
                className={`compare-cell ${best && item.readiness_score === best.readiness_score ? 'best' : ''}`}
                key={`ready-${item.id}`}
              >
                <span className="compare-value">
                  {n(item.readiness_score)} / {n(10)}
                </span>
                {item.missing_facilities.length > 0 && (
                  <small className="compare-warn">
                    {item.missing_facilities.map((k) => t(`facility.${k}`)).join(', ')}
                  </small>
                )}
              </div>
            ))}

            {/* Setup Costs */}
            <div className="compare-section-label" style={{ gridColumn: `1 / -1` }}>
              <Wallet size={18} /> {t('compare_setup')}
            </div>
            {[
              ['project_cost', 'project_cost'],
              ['margin', 'equity'],
              ['loan', 'loan'],
              ['funding_gap', 'funding_gap'],
            ].map(([field, label]) => (
              <>
                {items.map((item) => (
                  <div
                    className={`compare-cell ${best && field === 'funding_gap' && item[field] === best.funding_gap ? 'best' : field === 'project_cost' && item[field] === best.project_cost ? 'best' : ''}`}
                    key={`${field}-${item.id}`}
                  >
                    <small>{t(label)}</small>
                    <span className="compare-value">{money(item[field])}</span>
                  </div>
                ))}
              </>
            ))}

            {/* Repayment */}
            <div className="compare-section-label" style={{ gridColumn: `1 / -1` }}>
              <TrendingUp size={18} /> {t('compare_repayment')}
            </div>
            {items.map((item) => (
              <div
                className={`compare-cell ${best && item.quarterly_payment > 0 && item.quarterly_payment === best.quarterly_payment ? 'best' : ''}`}
                key={`scheme-${item.id}`}
              >
                <small>{t('selected_scheme')}</small>
                <span className="compare-value">{t(item.scheme)}</span>
                <div className="compare-detail">
                  <div>
                    <small>{t('quarterly_payment')}</small>
                    <b>{money(item.quarterly_payment)}</b>
                  </div>
                  <div>
                    <small>{t('total_repayment')}</small>
                    <b>{money(item.total_repayment)}</b>
                  </div>
                  <div>
                    <small>{t('total_interest')}</small>
                    <b>{money(item.total_interest)}</b>
                  </div>
                  {item.tenure_months > 0 && (
                    <div>
                      <small>{t('tenure')}</small>
                      <b>
                        {n(item.tenure_months)} {t('months')}
                      </b>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Operating Performance */}
            <div className="compare-section-label" style={{ gridColumn: `1 / -1` }}>
              <TrendingUp size={18} /> {t('compare_performance')}
            </div>
            {items.map((item) => (
              <div
                className={`compare-cell ${best && item.net_after_debt === best.net_after_debt ? 'best' : ''}`}
                key={`perf-${item.id}`}
              >
                <div className="compare-detail">
                  <div>
                    <small>{t('revenue')}</small>
                    <b>{money(item.revenue)}</b>
                  </div>
                  <div>
                    <small>{t('monthly_cost')}</small>
                    <b>{money(item.monthly_cost)}</b>
                  </div>
                  <div>
                    <small>{t('operating_profit')}</small>
                    <b>{money(item.operating_profit)}</b>
                  </div>
                  <div className="compare-highlight">
                    <small>{t('net_after_debt')}</small>
                    <b>{money(item.net_after_debt)}</b>
                  </div>
                </div>
              </div>
            ))}

            {/* Risks */}
            <div className="compare-section-label" style={{ gridColumn: `1 / -1` }}>
              <AlertTriangle size={18} /> {t('compare_risks')}
            </div>
            {items.map((item) => (
              <div className="compare-cell" key={`risk-${item.id}`}>
                <div className="compare-detail">
                  <div>
                    <small>{t('competitors')}</small>
                    <b>{n(item.competitors)}</b>
                  </div>
                  <div>
                    <small>{t('households')}</small>
                    <b>{n(item.households)}</b>
                  </div>
                  <div>
                    <small>{t('working_capital')}</small>
                    <b>{money(item.working_capital)}</b>
                  </div>
                  <div>
                    <small>{t('working_gap')}</small>
                    <b className={item.working_gap > 0 ? 'text-warn' : ''}>
                      {money(item.working_gap)}
                    </b>
                  </div>
                  <div>
                    <small>{t('downside')}</small>
                    <b className={item.downside_profit < 0 ? 'text-warn' : ''}>
                      {money(item.downside_profit)}
                    </b>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <p className="fineprint">{t('compare_note')}</p>
        </>
      )}
    </section>
  );
}
