import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Compass, X, Send, MessageCircle } from 'lucide-react';

const quickPrompts = [
  { key: 'how_to_assess', text: 'How do I run a business assessment?' },
  { key: 'where_schemes', text: 'Where do I find matching schemes?' },
  { key: 'how_emi_works', text: 'How does the EMI calculator work?' },
  { key: 'how_export_works', text: 'How can I export my report?' },
];

export default function AIAssistant() {
  const { t, i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: t('ai.greeting'), timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const userMsg = { role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, language: i18n.language || 'en' })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.reply, timestamp: new Date() }]);
      } else {
        throw new Error('API request failed');
      }
    } catch {
      // Offline fallback site navigation guide
      let fallback = "Here is how to navigate the platform:\n- **New Assessment**: Complete the 5-step wizard to evaluate location viability.\n- **Schemes**: Filter by loan amount or community to see active subsidies.\n- **EMI Calculator**: Calculate required tenure from your desired monthly budget.";
      if (text.toLowerCase().includes('assess')) {
        fallback = "To start a **Feasibility Assessment**, click **'New Assessment'** in the navigation bar, input your business idea, pin your location on the map, and submit to generate real POIs and scores.";
      } else if (text.toLowerCase().includes('scheme')) {
        fallback = "To explore government schemes, click **'Government Schemes'** in the navigation bar. You can view official application links, moratorium timelines, and nearby banks.";
      } else if (text.toLowerCase().includes('emi')) {
        fallback = "Open the **'Government Schemes'** page and click **'EMI Calculator'** to adjust either the loan tenure or your target monthly EMI bidirectionally.";
      } else if (text.toLowerCase().includes('export') || text.toLowerCase().includes('pdf') || text.toLowerCase().includes('docx')) {
        fallback = "On the **'Feasibility Report'** page, click **'Export PDF'** or **'Export Word (.docx)'** at the top right to download your complete consulting dossier.";
      }
      setMessages(prev => [...prev, { role: 'assistant', content: fallback, timestamp: new Date() }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="chat-widget">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ type: 'spring', bounce: 0.2 }}
            className="absolute bottom-16 right-0 w-[380px] h-[520px] rounded-2xl bg-surface-800/95 backdrop-blur-xl border border-white/10 shadow-2xl flex flex-col overflow-hidden z-50"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/5 bg-gradient-to-r from-primary-600/20 to-accent-500/10">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl gradient-accent flex items-center justify-center">
                  <Compass size={18} className="text-white" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">{t('ai.title')}</p>
                  <p className="text-[10px] text-white/40">Platform Navigation & Feature Guide</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-lg hover:bg-white/5 text-white/40 hover:text-white transition-all cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-primary-600/30 text-white rounded-br-sm'
                      : 'bg-white/5 text-white/80 rounded-bl-sm'
                  }`}>
                    {msg.content.split('\n').map((line, j) => (
                      <p key={j} className={j > 0 ? 'mt-1.5' : ''}>
                        {line.split('**').map((part, k) =>
                          k % 2 === 1 ? <strong key={k} className="text-white font-semibold">{part}</strong> : part
                        )}
                      </p>
                    ))}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white/5 px-4 py-3 rounded-2xl rounded-bl-sm">
                    <div className="flex gap-1">
                      {[0, 1, 2].map(i => (
                        <motion.div
                          key={i}
                          className="w-2 h-2 rounded-full bg-white/30"
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.2 }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Prompts */}
            {messages.length <= 2 && (
              <div className="px-4 pb-2 flex flex-wrap gap-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt.key}
                    onClick={() => sendMessage(prompt.text)}
                    className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/60 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
                  >
                    🧭 {prompt.text}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-3 border-t border-white/5 flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={t('ai.placeholder')}
                className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-white/30 focus:outline-none focus:border-primary-500/50"
                id="ai-chat-input"
              />
              <button
                type="submit"
                disabled={!input.trim()}
                className="btn btn-icon btn-accent disabled:opacity-30 cursor-pointer"
                id="ai-send-btn"
              >
                <Send size={16} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        className="chat-bubble cursor-pointer"
        id="ai-assistant-toggle"
      >
        {isOpen ? <X size={24} className="text-white" /> : <MessageCircle size={24} className="text-white" />}
      </motion.button>
    </div>
  );
}
