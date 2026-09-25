// Bhashini API Translation Service
// Government of India's AI-powered language translation platform
// Docs: https://bhashini.gov.in

const BHASHINI_PIPELINE_URL = 'https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline';
const BHASHINI_COMPUTE_URL = 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline';

// Bhashini credentials - set via environment variables
const BHASHINI_USER_ID = import.meta.env.VITE_BHASHINI_USER_ID || '';
const BHASHINI_API_KEY = import.meta.env.VITE_BHASHINI_API_KEY || '';
const BHASHINI_PIPELINE_ID = import.meta.env.VITE_BHASHINI_PIPELINE_ID || '64392f96daac500b55c543cd';

// Supported Bhashini language codes (ISO 639-1)
export const BHASHINI_LANGUAGES = {
  en: { name: 'English', nativeName: 'English', flag: '🇬🇧' },
  hi: { name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  ta: { name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳' },
  te: { name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳' },
  kn: { name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳' },
  bn: { name: 'Bengali', nativeName: 'বাংলা', flag: '🇮🇳' },
  mr: { name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳' },
  gu: { name: 'Gujarati', nativeName: 'ગુજરાતી', flag: '🇮🇳' },
  ml: { name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳' },
  pa: { name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
  or: { name: 'Odia', nativeName: 'ଓଡ଼ିଆ', flag: '🇮🇳' },
  as: { name: 'Assamese', nativeName: 'অসমীয়া', flag: '🇮🇳' },
};

// Cache for pipeline configs per language pair
const pipelineCache = {};

// Cache for translations - persisted in localStorage
const TRANSLATION_CACHE_KEY = 'bhashini_translations';

function getTranslationCache() {
  try {
    const cached = localStorage.getItem(TRANSLATION_CACHE_KEY);
    return cached ? JSON.parse(cached) : {};
  } catch {
    return {};
  }
}

function setTranslationCache(cache) {
  try {
    localStorage.setItem(TRANSLATION_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // localStorage full or unavailable
  }
}

/**
 * Get pipeline configuration for a language pair from Bhashini
 */
async function getPipelineConfig(sourceLang, targetLang) {
  const cacheKey = `${sourceLang}-${targetLang}`;
  if (pipelineCache[cacheKey]) return pipelineCache[cacheKey];

  const response = await fetch(BHASHINI_PIPELINE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'ulcaApiKey': BHASHINI_API_KEY,
      'userID': BHASHINI_USER_ID,
    },
    body: JSON.stringify({
      pipelineTasks: [
        {
          taskType: 'translation',
          config: {
            language: {
              sourceLanguage: sourceLang,
              targetLanguage: targetLang,
            },
          },
        },
      ],
      pipelineRequestConfig: {
        pipelineId: BHASHINI_PIPELINE_ID,
      },
    }),
  });

  if (!response.ok) throw new Error(`Pipeline config failed: ${response.status}`);

  const data = await response.json();
  const config = {
    serviceId: data.pipelineResponseConfig?.[0]?.config?.[0]?.serviceId,
    callbackUrl: data.pipelineInferenceAPIEndPoint?.callbackUrl || BHASHINI_COMPUTE_URL,
    inferenceApiKey: data.pipelineInferenceAPIEndPoint?.inferenceApiKey?.value,
  };

  pipelineCache[cacheKey] = config;
  return config;
}

/**
 * Translate text using Bhashini API
 * @param {string} text - Text to translate
 * @param {string} sourceLang - Source language code (e.g., 'en')
 * @param {string} targetLang - Target language code (e.g., 'hi')
 * @returns {Promise<string>} Translated text
 */
export async function translateText(text, sourceLang = 'en', targetLang = 'hi') {
  if (!text || sourceLang === targetLang) return text;

  // Check cache first
  const cache = getTranslationCache();
  const cacheKey = `${sourceLang}:${targetLang}:${text}`;
  if (cache[cacheKey]) return cache[cacheKey];

  try {
    const config = await getPipelineConfig(sourceLang, targetLang);

    const response = await fetch(config.callbackUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': config.inferenceApiKey || '',
      },
      body: JSON.stringify({
        pipelineTasks: [
          {
            taskType: 'translation',
            config: {
              language: {
                sourceLanguage: sourceLang,
                targetLanguage: targetLang,
              },
              serviceId: config.serviceId,
            },
          },
        ],
        inputData: {
          input: [{ source: text }],
        },
      }),
    });

    if (!response.ok) throw new Error(`Translation failed: ${response.status}`);

    const data = await response.json();
    const translated = data.pipelineResponse?.[0]?.output?.[0]?.target || text;

    // Cache the result
    cache[cacheKey] = translated;
    setTranslationCache(cache);

    return translated;
  } catch (error) {
    console.warn('Bhashini translation failed, falling back:', error.message);
    return text;
  }
}

/**
 * Batch translate multiple texts
 * @param {string[]} texts - Array of texts to translate
 * @param {string} sourceLang - Source language code
 * @param {string} targetLang - Target language code
 * @returns {Promise<string[]>} Array of translated texts
 */
export async function translateBatch(texts, sourceLang = 'en', targetLang = 'hi') {
  if (sourceLang === targetLang) return texts;

  const cache = getTranslationCache();
  const uncachedTexts = [];
  const uncachedIndices = [];

  // Check cache for each text
  const results = texts.map((text, index) => {
    const cacheKey = `${sourceLang}:${targetLang}:${text}`;
    if (cache[cacheKey]) return cache[cacheKey];
    uncachedTexts.push(text);
    uncachedIndices.push(index);
    return null;
  });

  if (uncachedTexts.length === 0) return results;

  try {
    const config = await getPipelineConfig(sourceLang, targetLang);

    const response = await fetch(config.callbackUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': config.inferenceApiKey || '',
      },
      body: JSON.stringify({
        pipelineTasks: [
          {
            taskType: 'translation',
            config: {
              language: {
                sourceLanguage: sourceLang,
                targetLanguage: targetLang,
              },
              serviceId: config.serviceId,
            },
          },
        ],
        inputData: {
          input: uncachedTexts.map((text) => ({ source: text })),
        },
      }),
    });

    if (!response.ok) throw new Error(`Batch translation failed: ${response.status}`);

    const data = await response.json();
    const outputs = data.pipelineResponse?.[0]?.output || [];

    outputs.forEach((output, i) => {
      const translated = output.target || uncachedTexts[i];
      results[uncachedIndices[i]] = translated;
      const cacheKey = `${sourceLang}:${targetLang}:${uncachedTexts[i]}`;
      cache[cacheKey] = translated;
    });

    setTranslationCache(cache);
  } catch (error) {
    console.warn('Bhashini batch translation failed:', error.message);
    uncachedIndices.forEach((idx, i) => {
      results[idx] = uncachedTexts[i]; // fallback to original
    });
  }

  return results;
}

/**
 * Check if Bhashini API is configured and available
 */
export function isBhashiniConfigured() {
  return !!(BHASHINI_USER_ID && BHASHINI_API_KEY);
}

/**
 * Clear the translation cache
 */
export function clearTranslationCache() {
  localStorage.removeItem(TRANSLATION_CACHE_KEY);
}

export default {
  translateText,
  translateBatch,
  isBhashiniConfigured,
  clearTranslationCache,
  BHASHINI_LANGUAGES,
};
