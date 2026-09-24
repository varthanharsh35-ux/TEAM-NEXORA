import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import ta from './locales/ta.json';
import hi from './locales/hi.json';
let language='en';
try { const saved=localStorage.getItem('gs-language'); if(['en','ta','hi'].includes(saved)) language=saved; } catch {}
i18n.use(initReactI18next).init({resources:{en:{translation:en},ta:{translation:ta},hi:{translation:hi}},lng:language,fallbackLng:false,keySeparator:false,interpolation:{escapeValue:false}});
i18n.on('languageChanged',lang=>{document.documentElement.lang=lang;document.title=i18n.t('brand');try{localStorage.setItem('gs-language',lang)}catch{}});
document.documentElement.lang=language;
export default i18n;
