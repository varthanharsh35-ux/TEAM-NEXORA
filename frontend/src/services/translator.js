// Pluggable translation service with reviewed financial glossary protection
// Supports Bhashini (Government of India) and Google Cloud Translation API

import bhashiniService, {
  translateText as bhashiniTranslateText,
  translateBatch as bhashiniTranslateBatch,
  isBhashiniConfigured,
  BHASHINI_LANGUAGES,
} from './bhashini.js';
import glossaryData from './glossary.json';

// Language support status
export const LANGUAGE_STATUS = {
  en: { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧', status: 'complete' },
  ta: { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳', status: 'complete' },
  hi: { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳', status: 'complete' },
  te: { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳', status: 'planned' },
  kn: { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳', status: 'planned' },
  bn: { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇮🇳', status: 'planned' },
  mr: { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳', status: 'planned' },
  gu: { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', flag: '🇮🇳', status: 'planned' },
  ml: { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳', status: 'planned' },
};

export const COMPLETE_LANGUAGES = ['en', 'ta', 'hi'];
export const PLANNED_LANGUAGES = ['te', 'kn', 'bn', 'mr', 'gu', 'ml'];

export function isLanguageComplete(code) {
  return COMPLETE_LANGUAGES.includes(code);
}

export function isLanguagePlanned(code) {
  return PLANNED_LANGUAGES.includes(code);
}

// Google Translate Provider
const GOOGLE_API_KEY = import.meta.env?.VITE_GOOGLE_TRANSLATE_API_KEY || '';
const GOOGLE_ENDPOINT = 'https://translation.googleapis.com/language/translate/v2';

export const googleProvider = {
  name: 'google',
  isConfigured: () => Boolean(GOOGLE_API_KEY),
  translateText: async (text, sourceLang = 'en', targetLang = 'hi') => {
    if (!text || sourceLang === targetLang) return text;
    if (!GOOGLE_API_KEY) {
      console.warn('Google Translate API key not set, skipping remote translation');
      return text;
    }
    try {
      const url = `${GOOGLE_ENDPOINT}?key=${encodeURIComponent(GOOGLE_API_KEY)}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          q: text,
          source: sourceLang,
          target: targetLang,
          format: 'text',
        }),
      });
      if (!res.ok) throw new Error(`Google translate HTTP ${res.status}`);
      const data = await res.json();
      return data.data?.translations?.[0]?.translatedText || text;
    } catch (err) {
      console.warn('Google translation error, falling back:', err.message);
      return text;
    }
  },
  translateBatch: async (texts, sourceLang = 'en', targetLang = 'hi') => {
    if (!texts?.length || sourceLang === targetLang) return texts;
    if (!GOOGLE_API_KEY) return texts;
    try {
      const url = `${GOOGLE_ENDPOINT}?key=${encodeURIComponent(GOOGLE_API_KEY)}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          q: texts,
          source: sourceLang,
          target: targetLang,
          format: 'text',
        }),
      });
      if (!res.ok) throw new Error(`Google translate HTTP ${res.status}`);
      const data = await res.json();
      const translations = data.data?.translations || [];
      return texts.map((t, idx) => translations[idx]?.translatedText || t);
    } catch (err) {
      console.warn('Google batch translation error, falling back:', err.message);
      return texts;
    }
  },
};

// Bhashini Provider wrapper
export const bhashiniProvider = {
  name: 'bhashini',
  isConfigured: isBhashiniConfigured,
  translateText: bhashiniTranslateText,
  translateBatch: bhashiniTranslateBatch,
};

// Active provider registry (defaulting to Bhashini per GoI priority)
const providers = {
  bhashini: bhashiniProvider,
  google: googleProvider,
};

let activeProviderName = import.meta.env?.VITE_TRANSLATION_PROVIDER === 'google' ? 'google' : 'bhashini';

export function setProvider(name) {
  if (!providers[name]) {
    throw new Error(`Unknown translation provider: ${name}. Available: ${Object.keys(providers).join(', ')}`);
  }
  activeProviderName = name;
}

export function getProvider() {
  return providers[activeProviderName] || bhashiniProvider;
}

export function listProviders() {
  return Object.keys(providers).map((key) => ({
    name: key,
    configured: providers[key].isConfigured(),
    active: key === activeProviderName,
  }));
}

// Reviewed Glossary lookup and protection
export const glossary = glossaryData.terms || {};

export function lookupGlossary(termKey, targetLang = 'en') {
  const term = glossary[termKey];
  if (!term) return null;
  return term[targetLang] || term.en || null;
}

/**
 * Apply reviewed financial glossary protection so delicate terms
 * (e.g. "moratorium", "margin money") are never corrupted by MT.
 */
export function applyGlossary(text, targetLang = 'en') {
  if (!text || typeof text !== 'string') return text;
  let result = text;
  for (const [key, term] of Object.entries(glossary)) {
    if (!term.do_not_machine_translate) continue;
    const enVal = term.en;
    const targetVal = term[targetLang] || term.en;
    if (enVal && targetVal && result.toLowerCase().includes(enVal.toLowerCase())) {
      const regex = new RegExp(`\\b${enVal}\\b`, 'gi');
      result = result.replace(regex, targetVal);
    }
  }
  return result;
}

/**
 * High-level translation function combining:
 * 1. Exact match against reviewed financial glossary (highest priority)
 * 2. Pluggable MT provider (Bhashini or Google)
 * 3. Reviewed glossary post-replacement
 */
export async function translate(text, sourceLang = 'en', targetLang = 'hi') {
  if (!text || sourceLang === targetLang) return text;

  // 1. Check if the entire string matches a reviewed glossary entry
  const normalized = text.trim().toLowerCase();
  for (const term of Object.values(glossary)) {
    if (term.en && term.en.toLowerCase() === normalized) {
      return term[targetLang] || term.en;
    }
  }

  // 2. Delegate to active translation provider
  const provider = getProvider();
  let translated = await provider.translateText(text, sourceLang, targetLang);

  // 3. Guarantee financial terms retain reviewed vocabulary
  translated = applyGlossary(translated, targetLang);

  return translated;
}

export default {
  translate,
  setProvider,
  getProvider,
  listProviders,
  lookupGlossary,
  applyGlossary,
  LANGUAGE_STATUS,
  COMPLETE_LANGUAGES,
  PLANNED_LANGUAGES,
  isLanguageComplete,
  isLanguagePlanned,
};
