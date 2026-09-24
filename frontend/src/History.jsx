import { useTranslation } from 'react-i18next';
export default function History({ history, onOpen }) {
  const { t, i18n } = useTranslation();
  return (
    <section className="panel history-page">
      <h1>{t('report_history')}</h1>
      <p>{t('history_note')}</p>
      {history.length === 0 ? (
        <p>{t('history_empty')}</p>
      ) : (
        <div className="report-grid">
          {history.map((r) => (
            <article className="panel" key={r.id}>
              <h2>{r.input.business_name || t(`sector.${r.business.category}`)}</h2>
              <p>{r.input.location}</p>
              <p>
                {new Intl.DateTimeFormat(`${i18n.language}-IN`, { dateStyle: 'medium' }).format(
                  new Date(r.created_at)
                )}
              </p>
              <p>
                {t('project_cost')}:{' '}
                {new Intl.NumberFormat(`${i18n.language}-IN`, {
                  style: 'currency',
                  currency: 'INR',
                }).format(r.finance.project_cost)}
              </p>
              <button onClick={() => onOpen(r)}>{t('open_report')}</button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
