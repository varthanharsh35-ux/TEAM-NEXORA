import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  TrendingUp, AlertTriangle, Shield, Target,
  Download, ChevronRight, MapPin, Building2,
  ExternalLink, RefreshCw, FileText, CheckCircle2,
  ThumbsUp, ThumbsDown, ArrowRight, Crosshair
} from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { jsPDF } from 'jspdf';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';

const userPinIcon = L.divIcon({
  className: 'custom-user-pin',
  html: `<div style="background-color: #3b5bdb; width: 32px; height: 32px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(59,91,219,0.5);"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg></div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

const competitorPinIcon = L.divIcon({
  className: 'custom-comp-pin',
  html: `<div style="background-color: #f97316; width: 26px; height: 26px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(249,115,22,0.4);"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><path d="m15 9-6 6"></path><path d="m9 9 6 6"></path></svg></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 26],
  popupAnchor: [0, -26]
});

const amenityPinIcon = L.divIcon({
  className: 'custom-amenity-pin',
  html: `<div style="background-color: #10b981; width: 26px; height: 26px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(16,185,129,0.4);"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 26],
  popupAnchor: [0, -26]
});

const bankPinIcon = L.divIcon({
  className: 'custom-bank-pin',
  html: `<div style="background-color: #8b5cf6; width: 26px; height: 26px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(139,92,246,0.4);"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M3 21h18M3 10h18M5 10v11M9 10v11M15 10v11M19 10v11M12 2l10 5H2l10-5z"></path></svg></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 26],
  popupAnchor: [0, -26]
});

const categoriesList = [
  'retail', 'food', 'agriculture', 'handicraft', 'textile',
  'dairy', 'services', 'manufacturing', 'transport', 'other'
];

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } }
};
const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } }
};

export default function FeasibilityDashboard() {
  const { t } = useTranslation();
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  const [assessment, setAssessment] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('retail');
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [poiTab, setPoiTab] = useState('competitors'); // 'competitors' | 'amenities' | 'banks'
  const [animatedDashOffset, setAnimatedDashOffset] = useState(0);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('gramsahayak_assessment');
      if (saved) {
        const parsed = JSON.parse(saved);
        setAssessment(parsed);
        setSelectedCategory(parsed.businessType || parsed.category || 'retail');
      }
    } catch (e) {
      console.error('Error reading assessment:', e);
    }
  }, []);

  // Map rendering with markers and boundary circle
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (!assessment) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const lat = Number(assessment.coordinates?.lat || assessment.lat || 20.7453);
    const lon = Number(assessment.coordinates?.lon || assessment.lon || 78.6022);
    const radius = Number(assessment.radiusKm || 5.0);

    const map = L.map(mapContainerRef.current, {
      center: [lat, lon],
      zoom: 13,
      scrollWheelZoom: false
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18
    }).addTo(map);

    // User Business Pin — label synced from assessment.location (single source of truth)
    const userMarker = L.marker([lat, lon], { icon: userPinIcon }).addTo(map);
    userMarker.bindPopup(`<b>${assessment.businessName || 'Your Business'}</b><br/>${assessment.location || ''}<br/><small>GPS: ${lat.toFixed(4)}, ${lon.toFixed(4)}</small>`).openPopup();

    // Catchment Boundary Circle
    L.circle([lat, lon], {
      radius: radius * 1000,
      color: '#3b5bdb',
      fillColor: '#3b5bdb',
      fillOpacity: 0.08,
      weight: 2,
      dashArray: '5, 5'
    }).addTo(map);

    // Render Competitors
    (assessment.nearbyCompetitors || []).forEach(comp => {
      const compMarker = L.marker([comp.lat, comp.lon], { icon: competitorPinIcon }).addTo(map);
      compMarker.bindPopup(`
        <div style="font-size: 12px;">
          <b style="color: #f97316;">🏢 ${comp.name}</b><br/>
          <span>Type: ${comp.category}</span><br/>
          <span>Distance: ${comp.distanceKm} km</span><br/>
          ${comp.contact ? `<span>Contact: ${comp.contact}</span><br/>` : ''}
          <a href="${comp.gmapsUrl}" target="_blank" rel="noopener noreferrer" style="color: #3b5bdb; font-weight: bold; text-decoration: underline;">Directions on Google Maps</a>
        </div>
      `);
    });

    // Render Amenities
    (assessment.nearbyAmenities || []).forEach(amenity => {
      const amMarker = L.marker([amenity.lat, amenity.lon], { icon: amenityPinIcon }).addTo(map);
      amMarker.bindPopup(`
        <div style="font-size: 12px;">
          <b style="color: #10b981;">🏫 ${amenity.name}</b><br/>
          <span>Type: ${amenity.category}</span><br/>
          <span>Distance: ${amenity.distanceKm} km</span><br/>
          <a href="${amenity.gmapsUrl}" target="_blank" rel="noopener noreferrer" style="color: #3b5bdb; font-weight: bold; text-decoration: underline;">Directions on Google Maps</a>
        </div>
      `);
    });

    // Render Banks
    (assessment.nearbyBanks || []).forEach(bank => {
      const bMarker = L.marker([bank.lat, bank.lon], { icon: bankPinIcon }).addTo(map);
      bMarker.bindPopup(`
        <div style="font-size: 12px;">
          <b style="color: #8b5cf6;">🏛️ ${bank.name}</b><br/>
          <span>Type: Financial Access Point</span><br/>
          <span>Distance: ${bank.distanceKm} km</span><br/>
          <a href="${bank.gmapsUrl}" target="_blank" rel="noopener noreferrer" style="color: #3b5bdb; font-weight: bold; text-decoration: underline;">Open in Google Maps</a>
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
  }, [assessment]);

  const handleRecalculateCategory = async (newCat) => {
    setSelectedCategory(newCat);
    setIsRecalculating(true);

    const lat = Number(assessment.coordinates?.lat || assessment.lat || 20.7453);
    const lon = Number(assessment.coordinates?.lon || assessment.lon || 78.6022);

    const payload = {
      businessName: assessment.businessName || 'Proposed Enterprise',
      businessType: newCat,
      description: assessment.description || '',
      location: assessment.location || 'Wardha, Maharashtra',
      lat,
      lon,
      radiusKm: Number(assessment.radiusKm || 5.0),
      initialCapital: Number(assessment.initialCapital || assessment.investment || 100000),
      facilities: assessment.facilities || [],
      community: assessment.community || 'General',
      gender: assessment.gender || 'all',
      education: assessment.education || 'secondary'
    };

    try {
      const res = await fetch('http://127.0.0.1:8000/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const updated = await res.json();
        setAssessment(updated);
        localStorage.setItem('gramsahayak_assessment', JSON.stringify(updated));
      }
    } catch (e) {
      console.warn('Re-evaluation error:', e);
    } finally {
      setIsRecalculating(false);
    }
  };

  const score = assessment?.overallScore || assessment?.feasibilityScore || 0;
  const circumference = 2 * Math.PI * 65;
  const dashOffset = circumference - (score / 100) * circumference;

  // Re-animate score circle whenever assessment data changes
  useEffect(() => {
    setAnimatedDashOffset(circumference); // reset to 0 fill
    const raf = requestAnimationFrame(() => {
      setTimeout(() => setAnimatedDashOffset(dashOffset), 50);
    });
    return () => cancelAnimationFrame(raf);
  }, [assessment?.overallScore, circumference, dashOffset]);

  const getScoreColor = (s) => {
    if (s >= 75) return '#10b981';
    if (s >= 55) return '#f59e0b';
    return '#ef4444';
  };

  // 6-dimension radar data
  const radarData = [
    { subject: 'Market Fit', value: assessment?.dimensionScores?.market || 0 },
    { subject: 'Footfall Synergy', value: assessment?.dimensionScores?.synergy || 0 },
    { subject: 'Financial Runway', value: assessment?.dimensionScores?.financial || 0 },
    { subject: 'Operations', value: assessment?.dimensionScores?.operations || 0 },
    { subject: 'Accessibility', value: assessment?.dimensionScores?.accessibility || 0 },
    { subject: 'Demand Potential', value: assessment?.dimensionScores?.demand || 0 },
  ];

  // Dimension bar data for sub-score breakdown
  const dimBarData = radarData.map(d => ({
    name: d.subject,
    score: d.value,
    fill: d.value >= 75 ? '#10b981' : d.value >= 50 ? '#f59e0b' : '#ef4444'
  }));

  const sv = assessment?.structuredVerdict;

  // Export PDF with jsPDF
  const exportPDF = () => {
    if (!assessment) return;
    const doc = new jsPDF();
    const primaryColor = [59, 91, 219];

    doc.setFillColor(...primaryColor);
    doc.rect(0, 0, 210, 28, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(18);
    doc.setTextColor(255, 255, 255);
    doc.text('GramSahayak AI — Business Feasibility Dossier', 14, 18);

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(50, 50, 50);

    let y = 38;
    doc.setFont('helvetica', 'bold');
    doc.text(`Entity: ${assessment.businessName || 'Proposed Venture'}`, 14, y);
    doc.text(`Sector: ${assessment.businessType || assessment.category || 'Retail'}`, 120, y);
    y += 7;
    doc.text(`Location: ${assessment.location || 'Unknown'}`, 14, y);
    doc.text(`Catchment Radius: ${assessment.radiusKm || 5} km`, 120, y);
    y += 7;
    doc.text(`Overall Feasibility Score: ${score}/100 (${assessment.feasibilityGrade || 'Viable'})`, 14, y);
    doc.text(`Risk Assessment: ${assessment.riskLevel || 'Moderate Risk'}`, 120, y);

    // Structured Verdict
    y += 12;
    if (sv) {
      doc.setFillColor(240, 243, 250);
      doc.roundedRect(14, y, 182, 10, 2, 2, 'F');
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.setTextColor(...primaryColor);
      doc.text(`Verdict: ${sv.headline}`, 18, y + 7);
      y += 14;

      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(40, 40, 40);
      const splitSummary = doc.splitTextToSize(sv.summary, 174);
      doc.text(splitSummary, 18, y);
      y += 5 * splitSummary.length + 4;

      doc.setFont('helvetica', 'bold');
      doc.text('Positive Factors:', 14, y);
      doc.setFont('helvetica', 'normal');
      (sv.positiveFactors || []).forEach(f => { y += 5; doc.text(`✓ ${f}`, 18, y); });
      y += 6;

      doc.setFont('helvetica', 'bold');
      doc.text('Risk Factors:', 14, y);
      doc.setFont('helvetica', 'normal');
      (sv.negativeFactors || []).forEach(f => { y += 5; doc.text(`⚠ ${f}`, 18, y); });
      y += 6;

      doc.setFont('helvetica', 'bold');
      doc.text('Competitor Landscape:', 14, y);
      doc.setFont('helvetica', 'normal');
      y += 5;
      const splitComp = doc.splitTextToSize(sv.competitorComparison, 174);
      doc.text(splitComp, 18, y);
      y += 5 * splitComp.length + 4;
    } else {
      doc.setFillColor(240, 243, 250);
      doc.roundedRect(14, y, 182, 22, 2, 2, 'F');
      doc.setFont('helvetica', 'italic');
      doc.setFontSize(9);
      doc.setTextColor(40, 40, 40);
      const splitReasoning = doc.splitTextToSize(assessment.verdictReasoning || 'Assessment evaluated.', 174);
      doc.text(splitReasoning, 18, y + 6);
      y += 30;
    }

    // SWOT
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(...primaryColor);
    doc.text('SWOT Analysis', 14, y);
    y += 7;
    doc.setFontSize(9);
    doc.setTextColor(30, 30, 30);

    const swot = assessment.swot || { strengths: assessment.strengths || [], weaknesses: [], opportunities: [], threats: [] };

    ['strengths', 'weaknesses', 'opportunities', 'threats'].forEach(key => {
      doc.setFont('helvetica', 'bold');
      doc.text(`${key.charAt(0).toUpperCase() + key.slice(1)}:`, 14, y);
      doc.setFont('helvetica', 'normal');
      (swot[key] || []).forEach(item => {
        y += 5;
        if (y > 275) { doc.addPage(); y = 20; }
        const split = doc.splitTextToSize(`• ${item}`, 174);
        doc.text(split, 18, y);
        y += (split.length - 1) * 4;
      });
      y += 6;
    });

    // Recommendations
    if (y > 240) { doc.addPage(); y = 20; }
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(...primaryColor);
    doc.text('Strategic Recommendations', 14, y);
    y += 7;
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(30, 30, 30);
    (assessment.recommendations || []).forEach(r => {
      if (y > 270) { doc.addPage(); y = 20; }
      const splitRec = doc.splitTextToSize(`✓ ${r}`, 178);
      doc.text(splitRec, 14, y);
      y += 6 * splitRec.length;
    });

    // Nearby POIs
    if (y > 240) { doc.addPage(); y = 20; }
    y += 4;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(...primaryColor);
    doc.text(`Verified POIs (${(assessment.nearbyCompetitors || []).length} Competitors, ${(assessment.nearbyAmenities || []).length} Anchors, ${(assessment.nearbyBanks || []).length} Banks)`, 14, y);
    y += 7;
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    (assessment.nearbyCompetitors || []).slice(0, 8).forEach((c, idx) => {
      if (y > 275) { doc.addPage(); y = 20; }
      doc.text(`${idx + 1}. ${c.name} (${c.category}) — ${c.distanceKm} km away`, 16, y);
      y += 5;
    });

    doc.save(`GramSahayak_Feasibility_${assessment.businessName || 'Report'}.pdf`);
  };

  // Export Word (.docx)
  const exportDOCX = async () => {
    if (!assessment) return;

    const swot = assessment.swot || { strengths: assessment.strengths || [], weaknesses: [], opportunities: [], threats: [] };

    const children = [
      new Paragraph({ text: 'GramSahayak AI — Business Feasibility & Market Dossier', heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER }),
      new Paragraph({ children: [new TextRun({ text: `Entity: ${assessment.businessName || 'Proposed Venture'} | Sector: ${assessment.businessType || 'Retail'}`, bold: true })], alignment: AlignmentType.CENTER }),
      new Paragraph({ children: [new TextRun({ text: `Location: ${assessment.location || 'Unknown'} | Catchment: ${assessment.radiusKm || 5} km`, italics: true })], alignment: AlignmentType.CENTER }),
      new Paragraph({ text: '' }),
      new Paragraph({ text: `Executive Verdict: ${score}/100 — ${assessment.feasibilityGrade || 'Viable Opportunity'} (${assessment.riskLevel || 'Low Risk'})`, heading: HeadingLevel.HEADING_1 }),
    ];

    if (sv) {
      children.push(new Paragraph({ children: [new TextRun({ text: `Headline: ${sv.headline}`, bold: true, size: 26 })] }));
      children.push(new Paragraph({ children: [new TextRun({ text: sv.summary, italics: true })] }));
      children.push(new Paragraph({ text: '' }));
      children.push(new Paragraph({ text: 'Positive Factors:', heading: HeadingLevel.HEADING_3 }));
      (sv.positiveFactors || []).forEach(f => children.push(new Paragraph({ text: `✓ ${f}` })));
      children.push(new Paragraph({ text: 'Risk Factors:', heading: HeadingLevel.HEADING_3 }));
      (sv.negativeFactors || []).forEach(f => children.push(new Paragraph({ text: `⚠ ${f}` })));
      children.push(new Paragraph({ text: 'Competitor Analysis:', heading: HeadingLevel.HEADING_3 }));
      children.push(new Paragraph({ text: sv.competitorComparison }));
      children.push(new Paragraph({ text: 'Recommended Next Steps:', heading: HeadingLevel.HEADING_3 }));
      (sv.nextSteps || []).forEach(s => children.push(new Paragraph({ text: `→ ${s}` })));
    } else {
      children.push(new Paragraph({ children: [new TextRun({ text: assessment.verdictReasoning || '', italics: true })] }));
    }

    children.push(new Paragraph({ text: '' }));
    children.push(new Paragraph({ text: 'SWOT Analysis', heading: HeadingLevel.HEADING_2 }));
    ['strengths', 'weaknesses', 'opportunities', 'threats'].forEach(key => {
      children.push(new Paragraph({ text: key.charAt(0).toUpperCase() + key.slice(1) + ':', heading: HeadingLevel.HEADING_3 }));
      (swot[key] || []).forEach(item => children.push(new Paragraph({ text: `• ${item}` })));
    });

    children.push(new Paragraph({ text: '' }));
    children.push(new Paragraph({ text: 'Strategic Recommendations', heading: HeadingLevel.HEADING_2 }));
    (assessment.recommendations || []).forEach(r => children.push(new Paragraph({ text: `✓ ${r}` })));

    children.push(new Paragraph({ text: '' }));
    children.push(new Paragraph({ text: 'Nearby Commercial Landscape', heading: HeadingLevel.HEADING_2 }));
    (assessment.nearbyCompetitors || []).slice(0, 10).map((c, i) =>
      children.push(new Paragraph({ text: `${i + 1}. ${c.name} — Category: ${c.category} | Distance: ${c.distanceKm} km` }))
    );

    const doc = new Document({ sections: [{ properties: {}, children }] });
    const blob = await Packer.toBlob(doc);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GramSahayak_Feasibility_${assessment.businessName || 'Report'}.docx`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const competitors = assessment?.nearbyCompetitors || [];
  const amenities = assessment?.nearbyAmenities || [];
  const banks = assessment?.nearbyBanks || [];

  if (!assessment) {
    return (
      <div className="max-w-6xl mx-auto flex items-center justify-center min-h-[60vh]">
        <div className="glass-card-static p-12 text-center">
          <Crosshair size={48} className="mx-auto text-white/20 mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">{t('feasibility.no_assessment')}</h2>
          <p className="text-white/40 text-sm mb-6">{t('feasibility.run_assessment_first')}</p>
          <a href="/assessment" className="btn btn-primary">{t('feasibility.start_assessment')}</a>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="max-w-6xl mx-auto space-y-6"
    >
      {/* Header with Export buttons & Sector Switcher */}
      <motion.div variants={itemVariants} className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">
            {t('feasibility.title')}
          </h1>
          <p className="text-white/40">
            {assessment?.businessName ? `${assessment.businessName} — ${assessment.location}` : t('feasibility.subtitle')}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Sector Switcher */}
          <div className="flex items-center gap-1.5 bg-white/5 border border-white/10 rounded-xl px-2 py-1">
            <RefreshCw size={14} className={`text-accent-400 ${isRecalculating ? 'animate-spin' : ''}`} />
            <select
              value={selectedCategory}
              onChange={(e) => handleRecalculateCategory(e.target.value)}
              disabled={isRecalculating}
              className="bg-transparent text-white text-xs font-medium focus:outline-none cursor-pointer pr-2"
              id="sector-switch-dropdown"
            >
              {categoriesList.map(cat => (
                <option key={cat} value={cat} className="bg-surface-800 text-white">
                  {t(`assessment.categories.${cat}`)}
                </option>
              ))}
            </select>
          </div>

          <button onClick={exportDOCX} className="btn btn-sm btn-outline flex items-center gap-1.5 cursor-pointer" id="export-docx-btn">
            <FileText size={14} />
            {t('feasibility.export_docx')}
          </button>
          <button onClick={exportPDF} className="btn btn-sm btn-primary flex items-center gap-1.5 cursor-pointer" id="export-pdf-btn">
            <Download size={14} />
            {t('feasibility.export_pdf')}
          </button>
        </div>
      </motion.div>

      {/* Top Grid: Score & Multi-Dimensional Radar */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Score Circle & Grade */}
        <motion.div variants={itemVariants}>
          <div className="glass-card-static p-6 text-center h-full flex flex-col justify-between">
            <div>
              <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-4">
                {t('feasibility.overall_score')}
              </h3>
              <div className="score-circle mx-auto mb-4">
                <svg width="170" height="170" viewBox="0 0 160 160">
                  <circle cx="80" cy="80" r="65" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
                  <circle
                    cx="80" cy="80" r="65" fill="none"
                    stroke={getScoreColor(score)}
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={animatedDashOffset}
                    style={{ transition: 'stroke-dashoffset 1.2s ease-out' }}
                  />
                </svg>
                <div className="score-value">
                  <span style={{ color: getScoreColor(score) }}>{score}</span>
                  <span className="score-label">out of 100</span>
                </div>
              </div>

              <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold ${
                score >= 75 ? 'bg-success-500/10 text-success-400' :
                score >= 55 ? 'bg-warning-500/10 text-warning-400' :
                'bg-danger-500/10 text-danger-400'
              }`}>
                <TrendingUp size={14} />
                <span>{assessment?.feasibilityGrade || t('feasibility.viable')}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 6-Dimension Radar */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <div className="glass-card-static p-6 h-full flex flex-col">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Target size={18} className="text-primary-400" />
              {t('feasibility.market_opportunity')}
            </h3>
            <div className="flex-1">
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} domain={[0, 100]} />
                  <Radar dataKey="value" stroke="#3b5bdb" fill="#3b5bdb" fillOpacity={0.25} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Dimension Sub-Score Breakdown Bars */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6">
          <h3 className="text-base font-bold text-white mb-4">{t('feasibility.dimension_breakdown')}</h3>
          <div className="space-y-3">
            {dimBarData.map((dim, i) => (
              <div key={`${dim.name}-${assessment?.overallScore || 0}`}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/60">{dim.name}</span>
                  <span className="font-bold" style={{ color: dim.fill }}>{dim.score}/100</span>
                </div>
                <div className="h-2.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    key={`bar-${dim.name}-${assessment?.overallScore || 0}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${dim.score}%` }}
                    transition={{ duration: 0.8, delay: i * 0.08 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: dim.fill }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* ─── Structured Verdict Panel (§4: detailed justified narrative) ─── */}
      {sv && (
        <motion.div variants={itemVariants}>
          <div className="glass-card-static p-6 space-y-5 border-l-4 border-l-primary-500">
            {/* Headline */}
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                score >= 75 ? 'bg-success-500/15' : score >= 55 ? 'bg-warning-500/15' : 'bg-danger-500/15'
              }`}>
                {score >= 62 ? <ThumbsUp size={20} className="text-success-400" /> : <ThumbsDown size={20} className="text-danger-400" />}
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">{sv.headline}</h3>
                <p className="text-xs text-white/40">{t('feasibility.viability_recommendation')}</p>
              </div>
            </div>

            {/* Summary */}
            <p className="text-sm text-white/70 leading-relaxed bg-white/2 p-4 rounded-xl border border-white/5">
              {sv.summary}
            </p>

            {/* Positive & Negative Factors */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-success-500/5 border border-success-500/15">
                <h4 className="text-xs font-bold uppercase tracking-wider text-success-400 mb-3 flex items-center gap-1.5">
                  <ThumbsUp size={14} />
                  {t('feasibility.positive_factors')}
                </h4>
                <ul className="space-y-2">
                  {(sv.positiveFactors || []).map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-white/70">
                      <span className="text-success-400 mt-0.5">✓</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="p-4 rounded-xl bg-danger-500/5 border border-danger-500/15">
                <h4 className="text-xs font-bold uppercase tracking-wider text-danger-400 mb-3 flex items-center gap-1.5">
                  <AlertTriangle size={14} />
                  {t('feasibility.risk_factors')}
                </h4>
                <ul className="space-y-2">
                  {(sv.negativeFactors || []).map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-white/70">
                      <span className="text-danger-400 mt-0.5">⚠</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Competitor Comparison */}
            <div className="p-4 rounded-xl bg-white/2 border border-white/5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-primary-400 mb-2">{t('feasibility.competitor_landscape')}</h4>
              <p className="text-xs text-white/70 leading-relaxed">{sv.competitorComparison}</p>
            </div>

            {/* Next Steps */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-accent-400">{t('feasibility.next_steps')}</h4>
              {(sv.nextSteps || []).map((step, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/2 hover:bg-white/4 transition-colors">
                  <ArrowRight size={14} className="text-accent-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-white/80">{step}</p>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Fallback verdict for old data without structuredVerdict */}
      {!sv && assessment?.verdictReasoning && (
        <motion.div variants={itemVariants}>
          <div className="glass-card-static p-6">
            <h3 className="text-lg font-bold text-white mb-3">{t('feasibility.viability_recommendation')}</h3>
            <p className="text-sm text-white/60 leading-relaxed bg-white/2 p-4 rounded-xl border border-white/5">
              {assessment.verdictReasoning}
            </p>
          </div>
        </motion.div>
      )}

      {/* Interactive Catchment Area Map & POIs */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MapPin size={20} className="text-primary-400" />
                {t('feasibility.catchment_title')}
              </h3>
              <p className="text-xs text-white/40">
                {assessment?.radiusKm || 5} km radius around {assessment?.location || 'selected coordinates'}
              </p>
            </div>

            {/* Map Legend */}
            <div className="flex flex-wrap gap-1.5 text-xs">
              <span className="px-2.5 py-1 rounded-lg bg-primary-600/20 text-primary-300 border border-primary-500/20 flex items-center gap-1">
                📍 You
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-orange-500/20 text-orange-300 border border-orange-500/20">
                🏢 {competitors.length} {t('feasibility.competitors_label')}
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/20">
                🏫 {amenities.length} {t('feasibility.anchors_label')}
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/20">
                🏛️ {banks.length} {t('feasibility.banks_label')}
              </span>
            </div>
          </div>

          {/* Leaflet Map */}
          <div
            ref={mapContainerRef}
            className="h-80 rounded-xl overflow-hidden border border-white/10 shadow-inner z-0"
            id="feasibility-results-map"
          />

          {/* POI List Cards — tab switcher: Competitors / Anchors / Banks */}
          <div className="space-y-3">
            {/* Tab Switcher */}
            <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 w-fit">
              {[
                { key: 'competitors', label: `${t('feasibility.competitors_label')} (${competitors.length})`, color: 'text-orange-400', activeBg: 'bg-orange-500/20' },
                { key: 'amenities', label: `${t('feasibility.anchors_label')} (${amenities.length})`, color: 'text-emerald-400', activeBg: 'bg-emerald-500/20' },
                { key: 'banks', label: `${t('feasibility.banks_label')} (${banks.length})`, color: 'text-purple-400', activeBg: 'bg-purple-500/20' },
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setPoiTab(tab.key)}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all cursor-pointer ${
                    poiTab === tab.key ? `${tab.activeBg} ${tab.color}` : 'text-white/40 hover:text-white/60'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Competitors Tab */}
            {poiTab === 'competitors' && (
              competitors.length > 0 ? (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto pr-1">
                  {competitors.slice(0, 12).map((comp, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/2 border border-white/5 flex flex-col justify-between hover:bg-white/4 transition-colors">
                      <div>
                        <div className="flex items-start justify-between gap-1 mb-1">
                          <p className="text-xs font-semibold text-white truncate">{comp.name}</p>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/15 text-orange-400 font-medium whitespace-nowrap">
                            {comp.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-white/40">{t('feasibility.distance')}: {comp.distanceKm} km</p>
                        {comp.contact && <p className="text-[10px] text-white/30 truncate">Ph: {comp.contact}</p>}
                      </div>
                      <a href={comp.gmapsUrl} target="_blank" rel="noopener noreferrer"
                        className="mt-2 text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium">
                        <span>{t('feasibility.directions')}</span><ExternalLink size={10} />
                      </a>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-white/2 text-center text-xs text-white/40">
                  {t('feasibility.no_competitors_found')}
                </div>
              )
            )}

            {/* Amenities / Anchors Tab */}
            {poiTab === 'amenities' && (
              amenities.length > 0 ? (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto pr-1">
                  {amenities.slice(0, 12).map((am, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/2 border border-white/5 flex flex-col justify-between hover:bg-white/4 transition-colors">
                      <div>
                        <div className="flex items-start justify-between gap-1 mb-1">
                          <p className="text-xs font-semibold text-white truncate">{am.name}</p>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-medium whitespace-nowrap">
                            {am.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-white/40">{t('feasibility.distance')}: {am.distanceKm} km</p>
                      </div>
                      <a href={am.gmapsUrl} target="_blank" rel="noopener noreferrer"
                        className="mt-2 text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium">
                        <span>{t('feasibility.directions')}</span><ExternalLink size={10} />
                      </a>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-white/2 text-center text-xs text-white/40">
                  No footfall anchors found in this radius.
                </div>
              )
            )}

            {/* Banks / Financial Tab */}
            {poiTab === 'banks' && (
              banks.length > 0 ? (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto pr-1">
                  {banks.slice(0, 12).map((bank, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/2 border border-white/5 flex flex-col justify-between hover:bg-white/4 transition-colors">
                      <div>
                        <div className="flex items-start justify-between gap-1 mb-1">
                          <p className="text-xs font-semibold text-white truncate">{bank.name}</p>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-400 font-medium whitespace-nowrap">
                            Financial
                          </span>
                        </div>
                        <p className="text-[11px] text-white/40">{t('feasibility.distance')}: {bank.distanceKm} km</p>
                        {bank.contact && <p className="text-[10px] text-white/30 truncate">Ph: {bank.contact}</p>}
                      </div>
                      <a href={bank.gmapsUrl} target="_blank" rel="noopener noreferrer"
                        className="mt-2 text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium">
                        <span>{t('feasibility.directions')}</span><ExternalLink size={10} />
                      </a>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-white/2 text-center text-xs text-white/40">
                  No banks or post offices found in this radius.
                </div>
              )
            )}
          </div>
        </div>
      </motion.div>

      {/* SWOT Analysis */}
      <motion.div variants={itemVariants}>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Shield size={20} className="text-accent-400" />
          {t('feasibility.swot')}
        </h3>
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            { key: 'strengths', items: assessment?.swot?.strengths || [], color: 'text-success-400', bg: 'bg-success-500/5', border: 'border-success-500/20' },
            { key: 'weaknesses', items: assessment?.swot?.weaknesses || [], color: 'text-danger-400', bg: 'bg-danger-500/5', border: 'border-danger-500/20' },
            { key: 'opportunities', items: assessment?.swot?.opportunities || [], color: 'text-primary-400', bg: 'bg-primary-500/5', border: 'border-primary-500/20' },
            { key: 'threats', items: assessment?.swot?.threats || [], color: 'text-warning-400', bg: 'bg-warning-500/5', border: 'border-warning-500/20' },
          ].map((sec) => (
            <div key={sec.key} className={`p-5 rounded-2xl ${sec.bg} border ${sec.border}`}>
              <h4 className={`text-xs font-bold uppercase tracking-wider ${sec.color} mb-3`}>
                {t(`feasibility.${sec.key}`)}
              </h4>
              <ul className="space-y-2">
                {sec.items.length > 0 ? sec.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs sm:text-sm text-white/70">
                    <span className="text-white/30">•</span>
                    <span>{item}</span>
                  </li>
                )) : (
                  <li className="text-xs text-white/30 italic">No data available</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Actionable Recommendations */}
      <motion.div variants={itemVariants}>
        <div className="glass-card-static p-6 space-y-4">
          <h3 className="text-lg font-bold text-white">{t('feasibility.recommendations')}</h3>
          <div className="space-y-2.5">
            {(assessment?.recommendations || []).map((rec, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/2 hover:bg-white/4 transition-colors">
                <ChevronRight size={16} className="text-accent-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-white/80">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Alternative Business Ideas */}
      {assessment?.alternativeIdeas?.length > 0 && (
        <motion.div variants={itemVariants}>
          <div className="glass-card-static p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <CheckCircle2 size={18} className="text-success-400" />
              {t('feasibility.alternative_ideas')}
            </h3>
            <div className="grid sm:grid-cols-3 gap-3">
              {assessment.alternativeIdeas.map((alt, i) => (
                <div key={i} className="p-4 rounded-xl bg-white/3 border border-white/5 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-accent-400">{alt.category}</span>
                    <h4 className="text-sm font-semibold text-white mt-1 mb-2">{alt.title}</h4>
                    <p className="text-xs text-white/50">{alt.rationale}</p>
                  </div>
                  <button
                    onClick={() => handleRecalculateCategory(alt.category)}
                    className="mt-3 text-xs text-primary-400 hover:text-primary-300 font-medium text-left cursor-pointer"
                  >
                    {t('feasibility.evaluate_idea')} →
                  </button>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
