"""Single authoring table emits separate, complete EN/TA/HI translation files."""
from pathlib import Path
import json
ROWS='''
brand|GramSahayak|கிராமசகாயக்|ग्रामसहायक
tagline|Local insight. A stronger start.|உள்ளூர் தகவல். உறுதியான தொடக்கம்.|स्थानीय जानकारी। मजबूत शुरुआत।
prototype|SIH 26091 · Tamil Nadu prototype|SIH 26091 · தமிழ்நாடு முன்மாதிரி|SIH 26091 · तमिलनाडु नमूना
not_government|Independent student prototype. Not a government portal.|மாணவர் முன்மாதிரி. அரசு இணையதளம் அல்ல.|स्वतंत्र छात्र नमूना। सरकारी पोर्टल नहीं।
language|Language|மொழி|भाषा
english|English|English|English
tamil|தமிழ்|தமிழ்|தமிழ்
hindi|हिन्दी|हिन्दी|हिन्दी
skip|Skip to main content|முக்கிய உள்ளடக்கத்திற்குச் செல்க|मुख्य सामग्री पर जाएं
nav_plan|Business plan|தொழில் திட்டம்|व्यवसाय योजना
nav_finance|Financial plan|நிதித் திட்டம்|वित्तीय योजना
nav_sources|Data & assumptions|தரவு மற்றும் அனுமானங்கள்|डेटा और मान्यताएं
eyebrow|YOUR IDEA. YOUR VILLAGE. YOUR NEXT STEP.|உங்கள் யோசனை. உங்கள் ஊர். அடுத்த படி.|आपका विचार। आपका गांव। अगला कदम।
headline|Start a business with a clearer plan.|தெளிவான திட்டத்துடன் தொழில் தொடங்குங்கள்.|स्पष्ट योजना के साथ व्यवसाय शुरू करें।
intro|Understand your local market, plan your investment and see what repayment could look like.|உள்ளூர் சந்தையை அறிந்து, முதலீட்டைத் திட்டமிட்டு, தவணைத் தொகையைப் பாருங்கள்.|स्थानीय बाजार समझें, निवेश की योजना बनाएं और चुकौती का अनुमान देखें।
coverage_badge|38 districts · Works without internet|38 மாவட்டங்கள் · இணையமின்றி இயங்கும்|38 जिले · बिना इंटरनेट काम करता है
new_plan|Your business details|உங்கள் தொழில் விவரங்கள்|आपके व्यवसाय का विवरण
required_hint|Three details to get started. No sign-up needed.|தொடங்க மூன்று விவரங்கள். பதிவு தேவையில்லை.|शुरू करने के लिए तीन जानकारियां। पंजीकरण जरूरी नहीं।
location|Village, block or district|கிராமம், வட்டாரம் அல்லது மாவட்டம்|गांव, ब्लॉक या जिला
location_placeholder|e.g. Alanganallur, Madurai|எ.கா. அலங்காநல்லூர், மதுரை|जैसे अलंगानल्लूर, मदुरै
location_hint|Tamil Nadu is assumed. Add a district for an unfamiliar village.|தமிழ்நாடு என எடுத்துக்கொள்ளப்படும். தெரியாத ஊருக்கு மாவட்டத்தையும் சேர்க்கவும்.|राज्य न लिखने पर तमिलनाडु माना जाएगा। अनजान गांव के साथ जिला जोड़ें।
district|District (optional)|மாவட்டம் (விருப்பம்)|जिला (वैकल्पिक)
choose_district|Detect from location|இடத்திலிருந்து கண்டறி|स्थान से पहचानें
business|What business do you have in mind?|என்ன தொழில் செய்ய விரும்புகிறீர்கள்?|आप कौन सा व्यवसाय करना चाहते हैं?
business_placeholder|e.g. Sell fresh milk and curd in my village|எ.கா. என் ஊரில் பால், தயிர் விற்க வேண்டும்|जैसे गांव में ताजा दूध और दही बेचना
business_hint|Write naturally in English, Tamil or Hindi. Spelling need not be perfect.|ஆங்கிலம், தமிழ் அல்லது இந்தியில் எழுதலாம். எழுத்துப் பிழைகள் பரவாயில்லை.|अंग्रेजी, तमिल या हिंदी में लिखें। छोटी वर्तनी की गलतियां चलेंगी।
margin|Your available margin capital|உங்கள் சொந்த முதலீட்டுத் தொகை|आपकी उपलब्ध स्वयं की पूंजी
margin_hint|Your own contribution, not the loan amount.|இது உங்கள் பங்களிப்பு; கடன் தொகை அல்ல.|यह आपका अंशदान है, ऋण राशि नहीं।
generate|Prepare my business plan|என் தொழில் திட்டத்தை உருவாக்கு|मेरी व्यवसाय योजना बनाएं
loading|Preparing your plan…|உங்கள் திட்டம் தயாராகிறது…|आपकी योजना तैयार हो रही है…
more_options|More options|மேலும் விருப்பங்கள்|अन्य विकल्प
category|Business category|தொழில் வகை|व्यवसाय श्रेणी
auto|Understand my description|என் விளக்கத்திலிருந்து கண்டறி|मेरे विवरण से पहचानें
radius|Market reach|சந்தை எல்லை|बाजार पहुंच
km|km|கி.மீ.|कि.मी.
community|Community (for scheme guidance)|சமூகப் பிரிவு (திட்ட வழிகாட்டலுக்கு)|सामाजिक वर्ग (योजना मार्गदर्शन के लिए)
unspecified|Prefer not to say|குறிப்பிட விரும்பவில்லை|बताना नहीं चाहते
sc|Scheduled Caste|பட்டியல் சாதி|अनुसूचित जाति
st|Scheduled Tribe|பழங்குடியினர்|अनुसूचित जनजाति
obc|Backward Classes|பிற்படுத்தப்பட்ட வகுப்பினர்|अन्य पिछड़ा वर्ग
general|General category|பொதுப் பிரிவு|सामान्य वर्ग
own_space|I already have a workspace|எனக்கு ஏற்கெனவே தொழில் இடம் உள்ளது|मेरे पास कार्यस्थल है
start_date|Planned loan disbursement date|கடன் பெறத் திட்டமிட்ட தேதி|प्रस्तावित ऋण वितरण तारीख
example|Try a dairy example|பால் பண்ணை உதாரணம்|डेयरी का उदाहरण देखें
example_location|Alanganallur, Madurai|அலங்காநல்லூர், மதுரை|अलंगानल्लूर, मदुरै
example_business|Fresh milk and curd delivery|பால் மற்றும் தயிர் விநியோகம்|ताजा दूध और दही वितरण
what_you_get|A practical plan, in one place.|பயனுள்ள திட்டம், ஒரே இடத்தில்.|उपयोगी योजना, एक ही जगह।
benefit_market|Know your market|உங்கள் சந்தையை அறியுங்கள்|अपना बाजार समझें
benefit_market_desc|Customer reach, competition, pricing and local opportunities.|வாடிக்கையாளர் எல்லை, போட்டி, விலை மற்றும் உள்ளூர் வாய்ப்புகள்.|ग्राहक पहुंच, प्रतिस्पर्धा, कीमत और स्थानीय अवसर।
benefit_finance|Make the numbers clear|நிதிக் கணக்கைத் தெளிவாக்குங்கள்|वित्तीय आंकड़े स्पष्ट करें
benefit_finance_desc|Project cost, loan limits, working capital and every quarterly payment.|திட்டச் செலவு, கடன் வரம்பு, நடைமுறை மூலதனம் மற்றும் காலாண்டுத் தவணை.|परियोजना लागत, ऋण सीमा, कार्यशील पूंजी और हर तिमाही की किस्त।
benefit_action|Take a sensible next step|சரியான அடுத்த படியை எடுங்கள்|सोच-समझकर अगला कदम लें
benefit_action_desc|A small pilot and a lender conversation before a large commitment.|பெரிய முதலீட்டுக்கு முன் சிறிய சோதனை விற்பனையும் வங்கி ஆலோசனையும்.|बड़े निवेश से पहले छोटा परीक्षण और ऋणदाता से बातचीत।
data_note|Planning estimates, with sources shown. Local field checks still matter.|ஆதாரங்களுடன் திட்டமிடல் மதிப்பீடுகள். நேரடி உள்ளூர் ஆய்வு அவசியம்.|स्रोतों सहित योजना अनुमान। स्थानीय जांच अभी भी जरूरी है।
existing|Already running a business?|ஏற்கெனவே தொழில் செய்கிறீர்களா?|क्या आपका व्यवसाय पहले से चल रहा है?
existing_desc|Use Daily accounts to record income and expenses. Save a repayment plan to review upcoming instalments.|வரவு செலவைப் பதிவு செய்ய தினசரி கணக்கைப் பயன்படுத்தவும். வரவிருக்கும் தவணைகளுக்குத் திட்டத்தைச் சேமிக்கவும்.|आमदनी और खर्च के लिए दैनिक खाते उपयोग करें। आगामी किस्तें देखने के लिए भुगतान योजना सहेजें।
report|Your business plan|உங்கள் தொழில் திட்டம்|आपकी व्यवसाय योजना
report_subtitle|A first assessment. Validate locally before investing.|முதல் கட்ட மதிப்பீடு. முதலீட்டுக்கு முன் உள்ளூரில் சரிபார்க்கவும்.|शुरुआती आकलन। निवेश से पहले स्थानीय जांच करें।
edit|Edit details|விவரங்களைத் திருத்து|विवरण बदलें
print|Print / save PDF|அச்சிடு / PDF சேமி|प्रिंट / PDF सहेजें
csv|Download repayment table|தவணை அட்டவணையைப் பதிவிறக்கு|चुकौती तालिका डाउनलोड करें
reset|New plan|புதிய திட்டம்|नई योजना
saved|Saved on this device|இந்தச் சாதனத்தில் சேமிக்கப்பட்டது|इस उपकरण पर सहेजा गया
cached|Showing your saved plan. Reconnect to the local server to calculate changed inputs.|சேமித்த திட்டம் காட்டப்படுகிறது. மாற்றிய விவரங்களைக் கணக்கிட உள்ளூர் சேவையகத்துடன் இணையவும்.|सहेजी हुई योजना दिख रही है। बदली जानकारी की गणना के लिए स्थानीय सर्वर से जुड़ें।
server_error|Local server is unavailable. Start the backend and try again. Your last saved plan is kept.|உள்ளூர் சேவையகம் கிடைக்கவில்லை. அதைத் தொடங்கி மீண்டும் முயற்சிக்கவும். முந்தைய திட்டம் பாதுகாக்கப்பட்டுள்ளது.|स्थानीय सर्वर उपलब्ध नहीं है। बैकएंड शुरू करके फिर प्रयास करें। पिछली योजना सुरक्षित है।
invalid_input|Enter a location, a business description and a positive amount (up to ₹10 crore).|இடம், தொழில் விளக்கம் மற்றும் பூஜ்ஜியத்தை விட அதிகமான தொகையை (₹10 கோடி வரை) உள்ளிடவும்.|स्थान, व्यवसाय विवरण और शून्य से अधिक राशि (₹10 करोड़ तक) दर्ज करें।
clarify|Add the district to identify this village safely.|இந்த ஊரைச் சரியாகக் கண்டறிய மாவட்டத்தையும் சேர்க்கவும்.|गांव की सही पहचान के लिए जिला जोड़ें।
ambiguous|This name matches several places. Choose the district and add the block.|இந்தப் பெயரில் பல ஊர்கள் உள்ளன. மாவட்டத்தைத் தேர்ந்து வட்டாரத்தையும் சேர்க்கவும்.|इस नाम के कई स्थान हैं। जिला चुनें और ब्लॉक जोड़ें।
outside_state|This prototype covers Tamil Nadu. Enter a Tamil Nadu location.|இந்த முன்மாதிரி தமிழ்நாட்டை உள்ளடக்குகிறது. தமிழ்நாட்டு இடத்தை உள்ளிடவும்.|यह नमूना तमिलनाडु के लिए है। तमिलनाडु का स्थान दर्ज करें।
district_proxy|Village not verified. This report uses a district-level scenario.|கிராமம் உறுதிப்படுத்தப்படவில்லை. மாவட்ட அளவிலான மதிப்பீடு பயன்படுத்தப்படுகிறது.|गांव की पुष्टि नहीं हुई। यह रिपोर्ट जिले के स्तर का अनुमान है।
historical|Place matched in the historical directory. Boundaries may have changed.|பழைய பட்டியலில் இடம் பொருந்தியது. எல்லைகள் மாறியிருக்கலாம்.|पुरानी निर्देशिका में स्थान मिला। सीमाएं बदल चुकी हो सकती हैं।
uncertain|Business is unfamiliar. Generic estimates are shown; choose a category or add detail.|தொழில் தெளிவாகப் புரியவில்லை. பொதுவான மதிப்பீடுகள் காட்டப்படுகின்றன; வகையைத் தேர்ந்தெடுக்கவும் அல்லது மேலும் விவரம் தரவும்.|व्यवसाय स्पष्ट नहीं है। सामान्य अनुमान दिखाए गए हैं; श्रेणी चुनें या अधिक विवरण दें।
estimated|Estimate|மதிப்பீடு|अनुमान
calculated|Calculated|கணக்கிடப்பட்டது|गणना की गई
pilot|Test with a small pilot|சிறிய அளவில் சோதித்து தொடங்குங்கள்|छोटे परीक्षण से शुरुआत करें
caution|Adjust the plan before borrowing|கடன் பெறும் முன் திட்டத்தை மாற்றுங்கள்|ऋण लेने से पहले योजना सुधारें
verdict_pilot|The base scenario supports a pilot. Demand and actual costs still need checking.|அடிப்படை மதிப்பீடு சிறிய சோதனைக்கு ஏற்றது. உண்மையான தேவை மற்றும் செலவைச் சரிபார்க்க வேண்டும்.|मूल अनुमान छोटे परीक्षण का समर्थन करता है। वास्तविक मांग और लागत जांचना जरूरी है।
verdict_caution|Estimated cash or working capital is tight. Reduce fixed costs or validate more demand before taking a loan.|மதிப்பீட்டில் பணப்புழக்கம் அல்லது நடைமுறை மூலதனம் போதவில்லை. கடன் பெறும் முன் நிலையான செலவைக் குறைக்கவும் அல்லது தேவையை உறுதி செய்யவும்.|अनुमानित नकदी या कार्यशील पूंजी कम है। ऋण से पहले स्थायी खर्च घटाएं या अधिक मांग की पुष्टि करें।
market|Market reach|சந்தை வாய்ப்பு எல்லை|बाजार पहुंच
opportunity|Local opportunities|உள்ளூர் வாய்ப்புகள்|स्थानीय अवसर
swot|Strengths, gaps & risks|பலங்கள், குறைகள் மற்றும் அபாயங்கள்|ताकत, कमियां और जोखिम
strengths|Strengths|பலங்கள்|ताकत
weaknesses|Weaknesses|குறைகள்|कमियां
threats|Threats to plan for|கவனிக்க வேண்டிய அபாயங்கள்|जिन जोखिमों की तैयारी करें
competition|Competition estimate|போட்டி மதிப்பீடு|प्रतिस्पर्धा का अनुमान
pricing|Price & local value|விலை மற்றும் உள்ளூர் மதிப்பு|कीमत और स्थानीय मूल्य
steps|Your next steps|உங்கள் அடுத்த படிகள்|आपके अगले कदम
population|Potential catchment residents|எல்லைக்குள் உள்ள மக்கள் மதிப்பீடு|संभावित क्षेत्रीय आबादी
households|Households in reach|அணுகக்கூடிய குடும்பங்கள்|पहुंच में परिवार
competitors|Similar businesses in catchment|எல்லைக்குள் ஒத்த தொழில்கள்|क्षेत्र में समान व्यवसाय
block_competitors|Similar businesses in block proxy|வட்டார மதிப்பீட்டில் ஒத்த தொழில்கள்|ब्लॉक अनुमान में समान व्यवसाय
no_map|Density scenario only; businesses have not been counted or mapped.|அடர்த்தி மதிப்பீடு மட்டும்; தொழில்கள் நேரடியாக எண்ணப்படவோ வரைபடமிடப்படவோ இல்லை.|यह केवल घनत्व का अनुमान है; व्यवसाय गिने या मानचित्रित नहीं किए गए हैं।
price|Indicative selling price|உத்தேச விற்பனை விலை|सांकेतिक बिक्री मूल्य
price_range|Price-testing range|விலையைச் சோதிக்கும் வரம்பு|कीमत परीक्षण की सीमा
units|Estimated monthly sales units|மாத விற்பனை அலகுகள் மதிப்பீடு|अनुमानित मासिक बिक्री इकाइयां
capacity|Monthly capacity limit|மாத உற்பத்தித் திறன் வரம்பு|मासिक क्षमता सीमा
unit_litre|per litre|லிட்டருக்கு|प्रति लीटर
unit_basket|per basket|பொருட்கள் தொகுப்புக்கு|प्रति टोकरी
unit_serving|per serving|ஒரு பரிமாறலுக்கு|प्रति परोस
unit_job|per job|ஒரு வேலைக்கு|प्रति कार्य
unit_kg|per kg|கிலோவுக்கு|प्रति किलो
unit_egg|per egg|முட்டைக்கு|प्रति अंडा
unit_item|per item|பொருளுக்கு|प्रति वस्तु
unit_trip|per trip|பயணத்திற்கு|प्रति यात्रा
unit_unit|per unit|அலகுக்கு|प्रति इकाई
project_cost|Total project cost|மொத்தத் திட்டச் செலவு|कुल परियोजना लागत
loan|Indicative loan amount|உத்தேசக் கடன் தொகை|सांकेतिक ऋण राशि
maximum_loan|90% financing before cap|வரம்புக்கு முன் 90% நிதி|सीमा से पहले 90% वित्त
funding_gap|Additional own funds needed|மேலும் தேவைப்படும் சொந்த நிதி|अतिरिक्त स्वयं की पूंजी जरूरी
quarterly_payment|Quarterly instalment|காலாண்டுத் தவணை|तिमाही किस्त
quarterly|Quarterly|காலாண்டு|तिमाही
monthly|Monthly|மாதம்|मासिक
micro|Micro Finance Scheme|நுண்நிதித் திட்டம்|सूक्ष्म वित्त योजना
term|Term Loan Scheme|காலக் கடன் திட்டம்|सावधि ऋण योजना
outside|Outside these scheme limits|இந்தத் திட்ட வரம்பிற்கு வெளியே|इन योजनाओं की सीमा से बाहर
outside_note|Project cost exceeds ₹50 lakh. No loan is routed under these two schemes. Discuss a smaller project or another financing route.|திட்டச் செலவு ₹50 லட்சத்தை மீறுகிறது. இந்த இரு திட்டங்களில் கடன் பரிந்துரை இல்லை. சிறிய திட்டம் அல்லது வேறு நிதி வழியை ஆலோசிக்கவும்.|परियोजना लागत ₹50 लाख से अधिक है। इन दो योजनाओं में ऋण का मार्ग नहीं है। छोटी परियोजना या अन्य वित्त विकल्प पर चर्चा करें।
cap_note|The loan cap applies. The remaining gap needs additional own funds.|கடன் உச்சவரம்பு பொருந்துகிறது. மீதித் தொகைக்கு கூடுதல் சொந்த நிதி தேவை.|ऋण सीमा लागू है। बची राशि के लिए अतिरिक्त स्वयं की पूंजी चाहिए।
finance_intro|Your capital builds the project. Repayment must fit the business.|உங்கள் முதலீடு திட்டத்தை உருவாக்குகிறது. தவணை தொழிலின் வருமானத்திற்கு ஏற்றதாக இருக்க வேண்டும்.|आपकी पूंजी से परियोजना बनती है। किस्त व्यवसाय की आय के अनुरूप होनी चाहिए।
formula|Project cost = your margin ÷ 10%. Loan = 90% of project cost, subject to the scheme cap.|திட்டச் செலவு = சொந்த முதலீடு ÷ 10%. கடன் = திட்டச் செலவில் 90%, திட்ட உச்சவரம்பிற்கு உட்பட்டது.|परियोजना लागत = आपकी पूंजी ÷ 10%। ऋण = परियोजना लागत का 90%, योजना सीमा के अधीन।
rate|Annual interest|ஆண்டு வட்டி|वार्षिक ब्याज
tenure|Total tenure, including grace period|சலுகைக் காலம் உட்பட மொத்தக் காலம்|छूट अवधि सहित कुल अवधि
moratorium|No-payment grace period|தவணை இல்லாத சலுகைக் காலம்|बिना भुगतान की छूट अवधि
months|months|மாதங்கள்|महीने
interest|Interest|வட்டி|ब्याज
total_interest|Total interest, including grace period|சலுகைக் காலம் உட்பட மொத்த வட்டி|छूट अवधि सहित कुल ब्याज
total_repayment|Total repayment|மொத்தத் திருப்பிச் செலுத்தல்|कुल चुकौती
moratorium_note|No payment in the first {{grace}} months. First payment at month {{first}}; last at month {{last}}. Interest accrues during the grace period.|முதல் {{grace}} மாதங்களில் தவணை இல்லை. முதல் தவணை {{first}}-ஆம் மாதம்; கடைசித் தவணை {{last}}-ஆம் மாதம். சலுகைக் காலத்தில் வட்டி சேரும்.|पहले {{grace}} महीनों में भुगतान नहीं। पहली किस्त {{first}}वें महीने और आखिरी {{last}}वें महीने में। छूट अवधि में ब्याज जुड़ता है।
interest_assumption|Assumption: simple moratorium interest is added once to principal; quarterly reducing-balance payments follow. Confirm the lender’s policy.|அனுமானம்: சலுகைக் காலத் தனிவட்டி அசலுடன் ஒருமுறை சேர்க்கப்படுகிறது; பின்னர் குறையும் நிலுவையில் காலாண்டுத் தவணை. வங்கிக் கொள்கையை உறுதி செய்யவும்.|मान्यता: छूट अवधि का साधारण ब्याज एक बार मूलधन में जुड़ता है; फिर घटते शेष पर तिमाही किस्तें। ऋणदाता की नीति की पुष्टि करें।
eligibility|Scheme route, not loan approval|திட்ட வழிகாட்டல்; கடன் ஒப்புதல் அல்ல|योजना मार्गदर्शन, ऋण मंजूरी नहीं
eligibility_desc|Community, income, documents and lending-agency checks apply. Capital alone does not establish eligibility.|சமூகம், வருமானம், ஆவணங்கள் மற்றும் கடன் நிறுவனச் சரிபார்ப்பு தேவை. முதலீடு மட்டும் தகுதியை நிரூபிக்காது.|समुदाय, आय, दस्तावेज और ऋण संस्था की जांच जरूरी है। केवल पूंजी से पात्रता तय नहीं होती।
agency_sc|Ask the district TAHDCO office about access and current eligibility.|திட்ட அணுகல் மற்றும் தற்போதைய தகுதி குறித்து மாவட்ட தாட்கோ அலுவலகத்தில் கேளுங்கள்.|पहुंच और वर्तमान पात्रता के लिए जिला ताडको कार्यालय से पूछें।
agency_other|For other communities, ask the district welfare office; BC/OBC applicants can explore TABCEDCO/NBCFDC. Terms differ.|மற்ற சமூகப் பிரிவினர் மாவட்ட நல அலுவலகத்தை அணுகவும்; பிற்படுத்தப்பட்ட வகுப்பினர் டாப்செட்கோ/NBCFDC வழிகளை விசாரிக்கலாம். நிபந்தனைகள் மாறுபடும்.|अन्य वर्ग जिला कल्याण कार्यालय से पूछें; पिछड़ा वर्ग TABCEDCO/NBCFDC विकल्प देख सकता है। शर्तें अलग हैं।
official_details|Official scheme details|அதிகாரப்பூர்வத் திட்ட விவரங்கள்|आधिकारिक योजना विवरण
local_access|District support / application guidance|மாவட்ட உதவி / விண்ணப்ப வழிகாட்டல்|जिला सहायता / आवेदन मार्गदर्शन
operating|Can the business cover its costs?|தொழிலால் செலவுகளை ஈடுசெய்ய முடியுமா?|क्या व्यवसाय अपने खर्च उठा सकता है?
revenue|Monthly sales revenue|மாத விற்பனை வருமானம்|मासिक बिक्री आय
fixed_cost|Fixed operating costs|நிலையான இயக்கச் செலவுகள்|स्थायी परिचालन खर्च
variable_cost|Stock / variable costs|சரக்கு / மாறும் செலவுகள்|माल / परिवर्ती खर्च
monthly_cost|Total monthly operating cost|மொத்த மாத இயக்கச் செலவு|कुल मासिक परिचालन खर्च
operating_profit|Operating surplus before repayment|தவணைக்கு முன் இயக்க உபரி|किस्त से पहले परिचालन बचत
net_after_debt|After monthly repayment reserve|மாதத் தவணை ஒதுக்கீட்டுக்குப் பின்|मासिक किस्त प्रावधान के बाद
working_capital|Working capital required|தேவைப்படும் நடைமுறை மூலதனம்|आवश्यक कार्यशील पूंजी
working_allocated|Working capital in project budget|திட்டத்தில் ஒதுக்கிய நடைமுறை மூலதனம்|योजना में कार्यशील पूंजी
working_gap|Working capital shortfall|நடைமுறை மூலதனப் பற்றாக்குறை|कार्यशील पूंजी की कमी
starter_cost|Starter setup benchmark|சிறிய தொடக்கச் செலவு மதிப்பீடு|छोटे प्रारंभ की लागत का अनुमान
established_cost|Established setup benchmark|முழுமையான அமைப்புச் செலவு மதிப்பீடு|पूर्ण व्यवस्था की लागत का अनुमान
break_even_units|Monthly units to cover costs & debt|செலவு மற்றும் கடனை ஈடுசெய்ய மாத அலகுகள்|खर्च और ऋण के लिए मासिक इकाइयां
no_break_even|Not achievable at this unit margin|இந்த அலகு லாபத்தில் சாத்தியமில்லை|इस इकाई लाभ पर संभव नहीं
downside|If sales fall by 25%|விற்பனை 25% குறைந்தால்|बिक्री 25% घटे तो
allocation|Project budget allocation|திட்ட நிதி ஒதுக்கீடு|परियोजना बजट आवंटन
equipment|Setup & equipment (60%)|அமைப்பு மற்றும் கருவிகள் (60%)|व्यवस्था और उपकरण (60%)
working|Working capital (30%)|நடைமுறை மூலதனம் (30%)|कार्यशील पूंजी (30%)
reserve|Contingency (10%)|எதிர்பாராத செலவு (10%)|आकस्मिक खर्च (10%)
projection|12-month cash scenario|12 மாதப் பணப்புழக்க மதிப்பீடு|12 महीने का नकदी अनुमान
projection_note|Sales ramp up over six months. Actual quarterly repayments are deducted when due. These are scenarios, not historical trends.|ஆறு மாதங்களில் விற்பனை படிப்படியாக உயரும் எனக் கருதப்படுகிறது. உரிய மாதத்தில் காலாண்டுத் தவணை கழிக்கப்படும். இவை மதிப்பீடுகள்; வரலாற்றுத் தரவுகள் அல்ல.|छह महीने में बिक्री बढ़ने की मान्यता है। देय महीने में वास्तविक तिमाही किस्त घटती है। ये अनुमान हैं, पुराने रुझान नहीं।
schedule|Every quarterly payment|ஒவ்வொரு காலாண்டுத் தவணையும்|हर तिमाही का भुगतान
month|Month|மாதம்|महीना
due_date|Due date|செலுத்தும் தேதி|देय तारीख
opening|Opening balance|தொடக்க நிலுவை|शुरुआती शेष
principal|Principal repaid|செலுத்திய அசல்|चुकाया मूलधन
payment|Payment|தவணை|भुगतान
balance|Closing balance|இறுதி நிலுவை|अंतिम शेष
grace|Grace period|சலுகைக் காலம்|छूट अवधि
cash|Net cash movement|நிகரப் பண மாற்றம்|शुद्ध नकदी बदलाव
costs|Operating costs|இயக்கச் செலவுகள்|परिचालन खर्च
repayment|Loan repayment|கடன் தவணை|ऋण चुकौती
sources_title|Know what is measured. Know what is assumed.|எது தரவு, எது அனுமானம் என்பதை அறியுங்கள்.|जानें क्या स्रोत से है और क्या अनुमान है।
sources_intro|Official directories identify places. Curated assumptions estimate local demand and costs. Every report keeps that distinction.|அதிகாரப்பூர்வப் பட்டியல்கள் இடங்களைக் கண்டறிகின்றன. தொகுக்கப்பட்ட அனுமானங்கள் உள்ளூர் தேவை மற்றும் செலவை மதிப்பிடுகின்றன.|आधिकारिक निर्देशिकाएं स्थान पहचानती हैं। तैयार मान्यताएं स्थानीय मांग और लागत का अनुमान देती हैं।
coverage|Coverage|தரவுப் பரப்பு|कवरेज
coverage_detail|{{districts}} districts, {{blocks}} historical blocks and {{villages}} historical panchayat records. Current LGD boundaries are not verified.|{{districts}} மாவட்டங்கள், {{blocks}} பழைய வட்டாரங்கள், {{villages}} பழைய ஊராட்சிப் பதிவுகள். தற்போதைய LGD எல்லைகள் உறுதிப்படுத்தப்படவில்லை.|{{districts}} जिले, {{blocks}} पुराने ब्लॉक और {{villages}} पुराने पंचायत अभिलेख। वर्तमान LGD सीमाएं सत्यापित नहीं हैं।
source_directory|Tamil Nadu Rural Development directories|தமிழ்நாடு ஊரக வளர்ச்சிப் பட்டியல்கள்|तमिलनाडु ग्रामीण विकास निर्देशिकाएं
source_districts|Tamil Nadu district directory|தமிழ்நாடு மாவட்டப் பட்டியல்|तमिलनाडु जिला निर्देशिका
source_nabard|NABARD Tamil Nadu State Focus Paper, 2025–26|நபார்டு தமிழ்நாடு மாநிலத் திட்ட அறிக்கை, 2025–26|नाबार्ड तमिलनाडु राज्य फोकस पत्र, 2025–26
source_scheme|NSFDC scheme FAQ|NSFDC திட்டக் கேள்வி பதில்கள்|NSFDC योजना प्रश्नोत्तर
source_priors|Project-authored planning assumptions, September 2026|திட்டத்திற்காக உருவாக்கிய அனுமானங்கள், செப்டம்பர் 2026|परियोजना के लिए तैयार मान्यताएं, सितंबर 2026
source_date|Cached / accessed: 24 September 2026|சேமித்த / அணுகிய நாள்: 24 செப்டம்பர் 2026|सहेजने / देखने की तारीख: 24 सितंबर 2026
retrieved|Evidence retrieved for this plan|இந்தத் திட்டத்திற்குத் தேடிப் பெற்ற ஆதாரம்|इस योजना के लिए खोजे गए साक्ष्य
page|Page|பக்கம்|पृष्ठ
assumptions|Assumptions behind the numbers|கணக்குகளின் அடிப்படை அனுமானங்கள்|आंकड़ों के पीछे की मान्यताएं
assumptions_population|Customer reach uses an assumed population density and reachable share around your selected area. Household counts and the range are estimates, not a village survey or road-distance analysis.|தேர்ந்தெடுத்த பகுதியைச் சுற்றிய மக்கள் அடர்த்தி மற்றும் சென்றடையக்கூடிய பங்கு கருதப்படுகிறது. குடும்ப எண்ணிக்கையும் வரம்பும் மதிப்பீடுகள்; கிராமக் கணக்கெடுப்பு அல்லது சாலைத் தொலைவு ஆய்வு அல்ல.|ग्राहक पहुंच चुने क्षेत्र की अनुमानित आबादी घनत्व और पहुंच पर आधारित है। परिवार संख्या और दायरा अनुमान हैं, गांव का सर्वेक्षण या सड़क दूरी विश्लेषण नहीं।
assumptions_market|Competition uses sector density priors; the block proxy assumes 1 lakh residents. Prices and purchasing-power multipliers are synthetic planning benchmarks, not live mandi prices.|போட்டி தொழில் அடர்த்தி அனுமானத்தைப் பயன்படுத்துகிறது; வட்டாரத்திற்கு 1 லட்சம் மக்கள் எனக் கருதப்படுகிறது. விலையும் வாங்கும் திறனும் திட்ட மதிப்பீடுகள்; நேரடி சந்தை விலைகள் அல்ல.|प्रतिस्पर्धा श्रेणी के घनत्व अनुमान से है; ब्लॉक में 1 लाख निवासी माने गए हैं। कीमत और क्रयशक्ति गुणक योजना मान्यताएं हैं, ताजा मंडी भाव नहीं।
assumptions_cost|Working capital covers 45 days of costs, 7.5 days of receivables and 6 days of supplier credit. Price, capacity and demand estimates limit sales.|நடைமுறை மூலதனம் 45 நாள் செலவு, 7.5 நாள் வரவேண்டிய பணம், 6 நாள் வழங்குநர் கடன் அடிப்படையில் உள்ளது. விலை, திறன் மற்றும் தேவை விற்பனையை வரையறுக்கின்றன.|कार्यशील पूंजी में 45 दिन का खर्च, 7.5 दिन की उधारी बिक्री और 6 दिन का आपूर्तिकर्ता ऋण है। कीमत, क्षमता और मांग बिक्री सीमित करते हैं।
model_title|How the intelligence works|நுண்ணறிவு எவ்வாறு செயல்படுகிறது|बुद्धिमत्ता कैसे काम करती है
model_desc|A trained small text classifier understands the business. Local document retrieval supplies evidence. An API or local open language model adds advice. Code calculates every financial amount.|பயிற்சியளிக்கப்பட்ட சிறிய உரை மாதிரி தொழிலைப் புரிந்துகொள்கிறது. உள்ளூர் ஆவணத் தேடல் ஆதாரம் தருகிறது. இணைய அல்லது உள்ளூர் திறந்த மொழி மாதிரி ஆலோசனை வழங்குகிறது. நிதித் தொகைகள் நிரலால் கணக்கிடப்படுகின்றன.|प्रशिक्षित छोटा पाठ मॉडल व्यवसाय पहचानता है। स्थानीय दस्तावेज खोज साक्ष्य देती है। एपीआई या स्थानीय खुला भाषा मॉडल सलाह जोड़ता है। सभी वित्तीय राशियां कोड से निकलती हैं।
model_metric|Curated holdout: {{count}} examples; accuracy {{accuracy}}. Small authored dataset, not real-world accuracy or business success probability.|தொகுக்கப்பட்ட சோதனை: {{count}} எடுத்துக்காட்டுகள்; துல்லியம் {{accuracy}}. சிறிய செயற்கைத் தரவு; நடைமுறைத் துல்லியம் அல்லது தொழில் வெற்றி நிகழ்தகவு அல்ல.|तैयार परीक्षण: {{count}} उदाहरण; सटीकता {{accuracy}}। छोटा तैयार डेटासेट; वास्तविक सटीकता या व्यवसाय सफलता की संभावना नहीं।
ai_curated|Local evidence + curated guidance|உள்ளூர் ஆதாரம் + தொகுக்கப்பட்ட வழிகாட்டல்|स्थानीय साक्ष्य + तैयार मार्गदर्शन
ai_pending|Language model is adding advice; your plan is ready.|மொழி மாதிரி ஆலோசனையைச் சேர்க்கிறது; உங்கள் திட்டம் தயார்.|भाषा मॉडल सलाह जोड़ रहा है; आपकी योजना तैयार है।
ai_api|API language-model advice|இணைய மொழி மாதிரி ஆலோசனை|एपीआई भाषा मॉडल की सलाह
ai_local|Local open-model advice|உள்ளூர் திறந்த மாதிரி ஆலோசனை|स्थानीय खुले मॉडल की सलाह
ai_fallback|Language model unavailable or response rejected. Curated guidance remains available.|மொழி மாதிரி கிடைக்கவில்லை அல்லது பதில் ஏற்கப்படவில்லை. தொகுக்கப்பட்ட வழிகாட்டல் உள்ளது.|भाषा मॉडल उपलब्ध नहीं या उत्तर अस्वीकार हुआ। तैयार मार्गदर्शन उपलब्ध है।
ai_disclaimer|Generated advice can be wrong. Use it alongside the estimates and a local field check.|உருவாக்கிய ஆலோசனை தவறாக இருக்கலாம். மதிப்பீடுகள் மற்றும் நேரடி ஆய்வுடன் பயன்படுத்தவும்.|बनाई गई सलाह गलत हो सकती है। अनुमान और स्थानीय जांच के साथ इसका उपयोग करें।
voice|Speak your business idea|தொழில் யோசனையைப் பேசுங்கள்|अपना व्यवसाय विचार बोलें
voice_error|Voice input is unavailable. Please type your idea.|குரல் உள்ளீடு கிடைக்கவில்லை. யோசனையைத் தட்டச்சு செய்யவும்.|आवाज से जानकारी उपलब्ध नहीं। कृपया विचार लिखें।
listening|Listening…|கேட்கிறது…|सुन रहे हैं…
empty|Create a plan to see your results here.|முடிவுகளைப் பார்க்க ஒரு திட்டத்தை உருவாக்கவும்.|परिणाम देखने के लिए योजना बनाएं।
print_tip|Choose “Save as PDF” in your browser’s print window.|உலாவியின் அச்சு சாளரத்தில் “PDF ஆக சேமி” தேர்ந்தெடுக்கவும்.|ब्राउज़र की प्रिंट विंडो में “PDF के रूप में सहेजें” चुनें।
advice.market|Start with households and small shops within the selected radius. Test doorstep delivery and the weekly market; road access may reduce the reachable base.|தேர்ந்தெடுத்த எல்லைக்குள் உள்ள குடும்பங்கள் மற்றும் சிறிய கடைகளில் தொடங்குங்கள். வீட்டு விநியோகம், வாரச் சந்தையைச் சோதிக்கவும்; சாலை வசதியால் அணுகல் குறையலாம்.|चुने हुए दायरे के परिवारों और छोटी दुकानों से शुरू करें। घर पहुंच सेवा और साप्ताहिक बाजार जांचें; सड़क पहुंच ग्राहक आधार घटा सकती है।
advice.opportunity|Test a convenient delivery time, smaller affordable packs or reliable after-sales service. An underserved niche is a hypothesis until customers confirm it.|வசதியான விநியோக நேரம், குறைந்த விலைச் சிறிய பொட்டலங்கள் அல்லது நம்பகமான விற்பனைக்குப் பிந்தைய சேவையைச் சோதிக்கவும். வாடிக்கையாளர் உறுதிப்படுத்தும் வரை சந்தை இடைவெளி ஓர் அனுமானமே.|सुविधाजनक वितरण समय, सस्ते छोटे पैक या भरोसेमंद बिक्री बाद सेवा जांचें। ग्राहक पुष्टि तक अधूरी बाजार जरूरत केवल अनुमान है।
advice.strengths|A local customer base can support repeat purchases. Your own contribution gives a clear starting budget; begin within the working-capital allocation.|உள்ளூர் வாடிக்கையாளர்கள் மீண்டும் வாங்க உதவலாம். உங்கள் சொந்த முதலீடு தொடக்க நிதியைத் தெளிவாக்குகிறது; ஒதுக்கிய நடைமுறை மூலதனத்திற்குள் தொடங்குங்கள்.|स्थानीय ग्राहक बार-बार खरीद सकते हैं। अपना अंशदान शुरुआती बजट स्पष्ट करता है; आवंटित कार्यशील पूंजी के भीतर शुरू करें।
advice.weaknesses|Demand is unverified and the estimates may miss rent, wastage or family labour. Obtain supplier quotations and compare the working-capital gap before committing.|தேவை உறுதி செய்யப்படவில்லை; வாடகை, வீணாகும் பொருட்கள் அல்லது குடும்ப உழைப்பு மதிப்பீட்டில் விடுபடலாம். வழங்குநர் விலைப்புள்ளிகளைப் பெற்று நடைமுறை மூலதனக் குறையை ஒப்பிடுங்கள்.|मांग सत्यापित नहीं है; किराया, खराब माल या पारिवारिक श्रम छूट सकते हैं। आपूर्तिकर्ता भाव लें और कार्यशील पूंजी की कमी जांचें।
advice.threats|Keep a second supplier for transport or stock disruptions. Plan for monsoon and harvest-season demand changes. Avoid depending on one buyer; build several repeat customers.|போக்குவரத்து அல்லது சரக்குத் தடைக்கு மாற்று வழங்குநரை வைத்திருங்கள். மழை மற்றும் அறுவடைக் காலத் தேவை மாற்றத்தைத் திட்டமிடுங்கள். ஒரே வாங்குபவரைச் சாராமல் பல தொடர் வாடிக்கையாளர்களை உருவாக்குங்கள்.|परिवहन या माल रुकने पर दूसरा आपूर्तिकर्ता रखें। मानसून और फसल मौसम की मांग के बदलाव की तैयारी करें। एक खरीदार पर निर्भर न रहें; कई नियमित ग्राहक बनाएं।
advice.competition|The displayed density is a scenario, not a field count. Walk the market, record comparable sellers and compare opening hours, quality and customer credit before choosing a location.|காட்டப்படும் அடர்த்தி ஒரு மதிப்பீடு; நேரடி எண்ணிக்கை அல்ல. சந்தையில் ஒத்த விற்பனையாளர்களைக் கணக்கிட்டு, நேரம், தரம் மற்றும் வாடிக்கையாளர் கடனை ஒப்பிட்டபின் இடத்தைத் தேர்ந்தெடுக்கவும்.|दिखाया घनत्व अनुमान है, मैदानी गिनती नहीं। बाजार में समान विक्रेताओं, समय, गुणवत्ता और ग्राहक उधारी की तुलना करके स्थान चुनें।
advice.pricing|Treat the price range as a local trial range. Confirm input costs and customer willingness to pay; smaller packs can improve affordability without selling below cost.|விலை வரம்பை உள்ளூர் சோதனைக்கானதாகக் கருதுங்கள். மூலப்பொருள் செலவு மற்றும் வாடிக்கையாளர் செலுத்த விரும்பும் விலையை உறுதி செய்யவும்; சிறிய பொட்டலங்கள் செலவுக்குக் கீழ் விற்காமல் வாங்க உதவலாம்.|कीमत सीमा को स्थानीय परीक्षण मानें। लागत और ग्राहक की भुगतान इच्छा जांचें; छोटे पैक लागत से नीचे बेचे बिना किफायती हो सकते हैं।
advice.steps|Speak to potential customers, collect supplier quotations and run a small trial. Take this report to the district support office and confirm scheme eligibility and repayment terms before borrowing.|வாடிக்கையாளர்களிடம் பேசி, வழங்குநர் விலைப்புள்ளிகளைப் பெற்று, சிறிய சோதனை நடத்துங்கள். அறிக்கையுடன் மாவட்ட உதவி அலுவலகத்தை அணுகி, கடனுக்கு முன் திட்டத் தகுதி மற்றும் தவணை விதிகளை உறுதி செய்யுங்கள்.|ग्राहकों से बात करें, आपूर्तिकर्ता भाव लें और छोटा परीक्षण करें। रिपोर्ट जिला सहायता कार्यालय ले जाकर ऋण से पहले पात्रता और चुकौती की शर्तें पक्की करें।
sector.dairy|Dairy|பால் பண்ணை|डेयरी
sector.retail|Retail & groceries|சில்லறை மற்றும் மளிகை|खुदरा और किराना
sector.food|Food & beverages|உணவு மற்றும் பானங்கள்|खाद्य और पेय
sector.tailoring|Tailoring & textiles|தையல் மற்றும் துணி|सिलाई और वस्त्र
sector.agriculture|Agriculture & processing|வேளாண்மை மற்றும் பதப்படுத்தல்|कृषि और प्रसंस्करण
sector.poultry|Poultry & eggs|கோழி மற்றும் முட்டை|मुर्गी और अंडे
sector.fish|Fish & seafood|மீன் மற்றும் கடல் உணவு|मछली और समुद्री खाद्य
sector.repair|Repair & maintenance|பழுது மற்றும் பராமரிப்பு|मरम्मत और रखरखाव
sector.craft|Handicrafts|கைவினை|हस्तशिल्प
sector.manufacturing|Small manufacturing|சிறு உற்பத்தி|छोटा विनिर्माण
sector.transport|Transport & delivery|போக்குவரத்து மற்றும் விநியோகம்|परिवहन और वितरण
sector.services|Local services|உள்ளூர் சேவைகள்|स्थानीय सेवाएं
sector.other|Other / needs validation|மற்றவை / சரிபார்ப்பு தேவை|अन्य / जांच जरूरी
region.delta|Delta agriculture and food processing|டெல்டா வேளாண்மை மற்றும் உணவுப் பதப்படுத்தல்|डेल्टा कृषि और खाद्य प्रसंस्करण
region.industrial|Manufacturing, textiles and local services|உற்பத்தி, துணி மற்றும் உள்ளூர் சேவைகள்|विनिर्माण, वस्त्र और स्थानीय सेवाएं
region.coastal|Coastal trade, fisheries and local services|கடலோர வணிகம், மீன்வளம் மற்றும் சேவைகள்|तटीय व्यापार, मत्स्य और स्थानीय सेवाएं
region.hills|Horticulture, tourism and local trade|தோட்டக்கலை, சுற்றுலா மற்றும் வணிகம்|बागवानी, पर्यटन और स्थानीय व्यापार
region.urban|Peri-urban trade and service demand|நகர்ப்புறச் சுற்றுவட்ட வணிகம் மற்றும் சேவைத் தேவை|शहरी किनारे का व्यापार और सेवा मांग
region.interior|Mixed farming, retail and local services|கலப்பு வேளாண்மை, சில்லறை மற்றும் சேவைகள்|मिश्रित खेती, खुदरा और स्थानीय सेवाएं
local_economy|Regional economy context|வட்டாரப் பொருளாதாரப் பின்னணி|क्षेत्रीय अर्थव्यवस्था का संदर्भ
confidence|Model confidence (not success probability)|மாதிரி நம்பிக்கை (வெற்றி நிகழ்தகவு அல்ல)|मॉडल भरोसा (सफलता की संभावना नहीं)
input_preserved|Your original description|உங்கள் அசல் விளக்கம்|आपका मूल विवरण
privacy|Saved only in this browser and the local server. Configured AI providers receive the business description and district.|இந்த உலாவி மற்றும் உள்ளூர் சேவையகத்தில் மட்டும் சேமிக்கப்படும். அமைக்கப்பட்ட நுண்ணறிவுச் சேவைக்கு தொழில் விளக்கமும் மாவட்டமும் அனுப்பப்படும்.|केवल इस ब्राउज़र और स्थानीय सर्वर में सहेजा जाता है। चुने हुए एआई प्रदाता को व्यवसाय विवरण और जिला भेजा जाता है।
footer|Plan carefully. Start small. Grow with evidence.|கவனமாகத் திட்டமிடுங்கள். சிறிதாகத் தொடங்குங்கள். ஆதாரத்துடன் வளருங்கள்.|सावधानी से योजना बनाएं। छोटे से शुरू करें। साक्ष्य के साथ बढ़ें।
fatal|Something went wrong. Reload to restore your saved plan.|பிழை ஏற்பட்டது. சேமித்த திட்டத்தை மீட்க மீண்டும் ஏற்றவும்.|कुछ गलत हुआ। सहेजी योजना पाने के लिए फिर लोड करें।
reload|Reload|மீண்டும் ஏற்று|फिर लोड करें
online|Local server ready|உள்ளூர் சேவையகம் தயார்|स्थानीय सर्वर तैयार
offline|Saved / offline view|சேமித்த / இணையமற்ற காட்சி|सहेजा / ऑफलाइन दृश्य
range|Scenario range|மதிப்பீட்டு வரம்பு|अनुमान की सीमा
report_missing|Saved report is unavailable. Prepare the plan again.|சேமித்த அறிக்கை கிடைக்கவில்லை. திட்டத்தை மீண்டும் உருவாக்கவும்.|सहेजी रिपोर्ट उपलब्ध नहीं है। योजना फिर बनाएं।
storage_error|This browser cannot save data. Keep this page open or print your plan.|இந்த உலாவியில் சேமிக்க முடியவில்லை. பக்கத்தைத் திறந்து வைக்கவும் அல்லது திட்டத்தை அச்சிடவும்.|यह ब्राउज़र डेटा नहीं सहेज सकता। पृष्ठ खुला रखें या योजना प्रिंट करें।
edit_hint|Recalculate after changing any details; the existing report keeps its original inputs.|விவரங்களை மாற்றிய பின் மீண்டும் கணக்கிடுங்கள்; பழைய அறிக்கை அதன் அசல் விவரங்களைக் கொண்டிருக்கும்.|विवरण बदलने के बाद फिर गणना करें; पुरानी रिपोर्ट अपने मूल इनपुट रखती है।
low_budget|A modelled financing envelope, not a requirement to borrow the maximum.|இது நிதித் திட்ட வரம்பு; அதிகபட்சக் கடன் பெற வேண்டிய கட்டாயம் இல்லை.|यह अनुमानित वित्त सीमा है; अधिकतम ऋण लेना जरूरी नहीं।
data_unavailable|Detailed source coverage is unavailable; cached report sources remain below.|விரிவான தரவுப் பரப்பு கிடைக்கவில்லை; சேமித்த அறிக்கையின் ஆதாரங்கள் கீழே உள்ளன.|विस्तृत कवरेज उपलब्ध नहीं; सहेजी रिपोर्ट के स्रोत नीचे हैं।
named_places|Official names retain the source directory spelling.|அதிகாரப்பூர்வ இடப்பெயர்கள் மூலப் பட்டியலின் எழுத்தில் உள்ளன.|आधिकारिक स्थान नाम स्रोत की वर्तनी में रखे गए हैं।
no_loan|No scheme loan assumed|திட்டக் கடன் கருதப்படவில்லை|योजना ऋण नहीं माना गया
application_note|The link opens guidance. This prototype does not submit a loan application.|இணைப்பு வழிகாட்டலைத் திறக்கும். இந்த முன்மாதிரி கடன் விண்ணப்பத்தை அனுப்பாது.|लिंक मार्गदर्शन खोलता है। यह नमूना ऋण आवेदन जमा नहीं करता।
price_disclaimer|No live price feed. Confirm today’s local prices before purchasing stock.|நேரடி விலைத் தரவு இல்லை. சரக்கு வாங்கும் முன் இன்றைய உள்ளூர் விலையை உறுதி செய்யவும்.|ताजा कीमत की फीड नहीं है। माल खरीदने से पहले आज का स्थानीय भाव जांचें।
equity|Your own capital|உங்கள் சொந்த முதலீடு|आपकी अपनी पूंजी
period|Period|காலம்|अवधि
year|Year|ஆண்டு|वर्ष
back|Back to plan|திட்டத்திற்குத் திரும்பு|योजना पर वापस जाएं
zoom_in|Zoom in|பெரிதாக்கு|बड़ा करें
zoom_out|Zoom out|சிறிதாக்கு|छोटा करें
map_label|Choose a point on the map|வரைபடத்தில் இடத்தைத் தேர்ந்தெடு|मानचित्र पर स्थान चुनें
map_hint|Optional online map. Click to place a pin; typing a location works offline.|விருப்ப இணைய வரைபடம். இடத்தைத் தொடவும்; இணையமின்றி இடத்தைத் தட்டச்சு செய்யலாம்.|वैकल्पिक ऑनलाइन मानचित्र। पिन रखने के लिए क्लिक करें; बिना इंटरनेट स्थान लिख सकते हैं।
map_loading|Finding the place…|இடத்தைக் கண்டறிகிறது…|स्थान खोज रहे हैं…
map_selected|Point selected. Check the location and district.|இடம் தேர்ந்தெடுக்கப்பட்டது. ஊர் மற்றும் மாவட்டத்தைச் சரிபார்க்கவும்.|स्थान चुना गया। स्थान और जिला जांचें।
map_failed|Map lookup unavailable. Keep the pin and choose a district under more options.|வரைபடத் தேடல் கிடைக்கவில்லை. குறியீட்டை வைத்துக்கொண்டு மேலும் விருப்பங்களில் மாவட்டத்தைத் தேர்ந்தெடுக்கவும்.|मानचित्र खोज उपलब्ध नहीं। पिन रखें और अन्य विकल्प में जिला चुनें।
map_attribution|Contributors · Map tiles need internet|பங்களிப்பாளர்கள் · வரைபடத்திற்கு இணையம் தேவை|योगदानकर्ता · मानचित्र के लिए इंटरनेट जरूरी

nav_profile|My profile|எனது விவரங்கள்|मेरी जानकारी
choose_business|Choose a business|தொழிலைத் தேர்ந்தெடுக்கவும்|व्यवसाय चुनें
business_select_hint|Choose the main activity. Your plan uses this selection; no description needed.|முக்கிய தொழிலைத் தேர்ந்தெடுக்கவும். விளக்கம் எழுத வேண்டியதில்லை.|मुख्य काम चुनें। विवरण लिखने की जरूरत नहीं।
profile_intro|Your circumstances shape your plan. These details stay on this device and the local server.|உங்கள் சூழலுக்கு ஏற்ப திட்டம் அமையும். விவரங்கள் இந்தச் சாதனத்திலும் உள்ளூர் சேவையகத்திலும் இருக்கும்.|आपकी परिस्थिति से योजना बनती है। जानकारी इस उपकरण और स्थानीय सर्वर पर रहती है।
profile_saved|Changes saved on this device. Recalculate your plan to use them.|மாற்றங்கள் இந்தச் சாதனத்தில் சேமிக்கப்பட்டன. திட்டத்தில் பயன்படுத்த மீண்டும் கணக்கிடவும்.|बदलाव इस उपकरण पर सहेजे गए। योजना में उपयोग के लिए फिर गणना करें।
gender|Gender|பாலினம்|लिंग
female|Woman|பெண்|महिला
male|Man|ஆண்|पुरुष
other_gender|Another gender|மற்ற பாலினம்|अन्य लिंग
age|Age (years)|வயது (ஆண்டுகள்)|उम्र (वर्ष)
household_income|Annual household income (₹)|குடும்ப ஆண்டு வருமானம் (₹)|परिवार की वार्षिक आय (₹)
optional_profile|Optional. Complete these for more precise scheme screening.|விருப்பம். திட்டத் தகுதியைச் சரிபார்க்க இவற்றை நிரப்பவும்.|वैकल्पिक। योजना पात्रता की बेहतर जांच के लिए भरें।
facilities_title|What do you already have?|உங்களிடம் ஏற்கெனவே உள்ள வசதிகள்?|आपके पास पहले से क्या है?
facilities_hint|Select only facilities you can reliably use. Missing facilities need a setup plan.|நம்பகமாகப் பயன்படுத்தக்கூடிய வசதிகளை மட்டும் தேர்ந்தெடுக்கவும். மற்றவற்றுக்கு ஏற்பாடு தேவை.|केवल भरोसे से उपलब्ध सुविधाएं चुनें। बाकी की व्यवस्था करनी होगी।
facility.space|Workspace|தொழில் இடம்|काम की जगह
facility.power|Reliable electricity|நம்பகமான மின்சாரம்|भरोसेमंद बिजली
facility.three_phase|Three-phase electricity|மும்முனை மின்சாரம்|तीन फेज बिजली
facility.water|Clean running water|சுத்தமான குழாய் நீர்|साफ बहता पानी
facility.storage|Secure storage|பாதுகாப்பான சேமிப்பிடம்|सुरक्षित भंडारण
facility.cold|Refrigeration|குளிர்பதன வசதி|शीत भंडारण
facility.transport|Transport access|போக்குவரத்து வசதி|परिवहन सुविधा
facility.equipment|Basic business equipment|அடிப்படை தொழில் கருவிகள்|बुनियादी उपकरण
readiness|Before you begin|தொடங்கும் முன்|शुरू करने से पहले
readiness_missing|Arrange or confirm these facilities before investing.|முதலீட்டுக்கு முன் இந்த வசதிகளை ஏற்பாடு செய்யவும் அல்லது உறுதி செய்யவும்.|निवेश से पहले इन सुविधाओं की व्यवस्था या पुष्टि करें।
readiness_ready|Your declared facilities cover the basic checklist. Confirm capacity and safety locally.|நீங்கள் தெரிவித்த வசதிகள் அடிப்படைப் பட்டியலை நிறைவு செய்கின்றன. கொள்ளளவும் பாதுகாப்பும் உறுதி செய்யவும்.|बताई सुविधाएं बुनियादी सूची पूरी करती हैं। क्षमता और सुरक्षा की स्थानीय पुष्टि करें।
readiness_note|Indicative business checklist; equipment-specific needs may differ.|தொழிலுக்கான பொதுப் பட்டியல்; கருவிகளின் தேவைகள் மாறலாம்.|व्यवसाय की संकेतात्मक सूची; उपकरण के अनुसार जरूरत बदल सकती है।
finance_plain|See what you can invest, what you may borrow and whether repayments fit your business.|முதலீடு, கிடைக்கக்கூடிய கடன் மற்றும் தொழிலுக்கு ஏற்ற தவணைகளை அறியுங்கள்.|देखें कितना निवेश और ऋण संभव है तथा किस्तें व्यवसाय के अनुकूल हैं या नहीं।
nav_help|Website helper|இணையதள உதவி|वेबसाइट सहायक
help_intro|I help you find pages and understand the next step. I do not approve loans or give financial advice.|பக்கங்களையும் அடுத்த படியையும் கண்டுபிடிக்க உதவுவேன். கடன் ஒப்புதல் அல்லது நிதி ஆலோசனை வழங்க மாட்டேன்.|मैं पृष्ठ और अगला कदम खोजने में मदद करता हूं। ऋण स्वीकृति या वित्तीय सलाह नहीं देता।
help_placeholder|Ask where to find something…|எதை எங்கே காணலாம் என்று கேளுங்கள்…|पूछें कोई सुविधा कहां मिलेगी…
help_send|Ask|கேள்|पूछें
help_close|Close helper|உதவியை மூடு|सहायक बंद करें
help_open_page|Open this page|இந்தப் பக்கத்தைத் திற|यह पृष्ठ खोलें
help_plan|Open Business plan. Choose a location, business and your own capital, then prepare your plan.|தொழில் திட்டத்தைத் திறக்கவும். இடம், தொழில், சொந்த முதலீட்டைத் தேர்ந்தெடுத்து திட்டம் தயாரிக்கவும்.|व्यवसाय योजना खोलें। स्थान, व्यवसाय और अपनी पूंजी चुनकर योजना बनाएं।
help_finance|Open Financial plan to review costs and borrowing. Open Repayments for the full schedule. Prepare a business plan first.|செலவு மற்றும் கடனுக்கு நிதித் திட்டத்தைத் திறக்கவும். முழு அட்டவணைக்கு திருப்பிச் செலுத்துதல் பக்கத்தைத் திறக்கவும். முதலில் தொழில் திட்டம் தயாரிக்கவும்.|खर्च और ऋण के लिए वित्तीय योजना खोलें। पूरी समयसारणी के लिए ऋण भुगतान खोलें। पहले व्यवसाय योजना बनाएं।
help_profile|Open My profile to add community, income and facilities you already have.|சமூகம், வருமானம், வசதிகளைச் சேர்க்க எனது விவரங்களைத் திறக்கவும்.|समुदाय, आय और उपलब्ध सुविधाएं जोड़ने के लिए मेरी जानकारी खोलें।
help_sources|Open Data & assumptions to check where figures come from and which values are estimates.|எண்களின் ஆதாரங்களையும் மதிப்பீடுகளையும் அறிய தரவு மற்றும் கணிப்புகளைத் திறக்கவும்.|आंकड़ों के स्रोत और अनुमान जानने के लिए डेटा और मान्यताएं खोलें।
help_unknown|I can help with website navigation. Choose a topic below or ask about a page.|இணையதள வழிசெலுத்த உதவுவேன். கீழே தலைப்பைத் தேர்ந்தெடுக்கவும் அல்லது பக்கம் பற்றிக் கேளுங்கள்.|मैं वेबसाइट चलाने में मदद कर सकता हूं। नीचे विषय चुनें या किसी पृष्ठ के बारे में पूछें।
more_languages|More languages planned|மேலும் மொழிகள் திட்டமிடப்பட்டுள்ளன|अन्य भाषाएं नियोजित हैं
language_roadmap|Telugu, Kannada, Malayalam, Marathi and Bengali are planned. These are not available yet.|தெலுங்கு, கன்னடம், மலையாளம், மராத்தி, வங்காளம் திட்டமிடப்பட்டுள்ளன. தற்போது கிடைக்கவில்லை.|तेलुगु, कन्नड़, मलयालम, मराठी और बंगाली नियोजित हैं। अभी उपलब्ध नहीं हैं।

nav_schemes|Find a scheme|கடன் திட்டங்கள்|योजना खोजें
nav_allocation|Use of funds|நிதிப் பயன்பாடு|धन का उपयोग
nav_repayment|Repayments|திருப்பிச் செலுத்துதல்|ऋण भुगतान
nav_tracker|Daily accounts|தினசரி கணக்கு|दैनिक खाते
nbcfdc|NBCFDC Individual Loan|என்.பி.சி.எஃப்.டி.சி தனிநபர் கடன்|एनबीसीएफडीसी व्यक्तिगत ऋण
scheme_intro|Explore schemes against your profile and budget. These checks indicate a possible match; the lending agency decides eligibility.|உங்கள் விவரங்கள் மற்றும் முதலீட்டுக்கு ஏற்ற திட்டங்களைப் பாருங்கள். இறுதித் தகுதியை கடன் நிறுவனம் முடிவு செய்யும்.|अपनी जानकारी और बजट के अनुसार योजनाएं देखें। अंतिम पात्रता ऋण संस्था तय करती है।
potential|Potential match|பொருந்தக்கூடும்|संभावित पात्रता
need_details|More details needed|மேலும் விவரங்கள் தேவை|अधिक जानकारी चाहिए
not_eligible|Does not match entered details|உள்ளிட்ட விவரங்களுடன் பொருந்தவில்லை|भरी जानकारी से मेल नहीं
filter_status|Show schemes|திட்டங்களைக் காட்டு|योजनाएं दिखाएं
all_schemes|All available schemes|கிடைக்கும் அனைத்துத் திட்டங்கள்|सभी उपलब्ध योजनाएं
filter_community|Community filter|சமூக வடிகட்டி|समुदाय फ़िल्टर
all_communities|All communities|அனைத்துச் சமூகங்கள்|सभी समुदाय
community_mismatch|Community requirement does not match.|சமூகத் தகுதி பொருந்தவில்லை.|समुदाय की शर्त मेल नहीं खाती।
income_above|Household income exceeds this scheme’s limit.|குடும்ப வருமானம் இந்தத் திட்ட வரம்பை மீறுகிறது.|परिवार की आय योजना सीमा से अधिक है।
project_mismatch|This budget falls outside the scheme’s project range.|இந்த முதலீடு திட்ட வரம்பிற்கு வெளியே உள்ளது.|यह बजट योजना की परियोजना सीमा से बाहर है।
scheme_project_limit|Choose a scheme that fits your project budget.|உங்கள் திட்ட முதலீட்டுக்கு ஏற்ற திட்டத்தைத் தேர்ந்தெடுக்கவும்.|परियोजना बजट के अनुकूल योजना चुनें।
use_scheme|Use this scheme in my plan|இந்தத் திட்டத்தைப் பயன்படுத்து|मेरी योजना में उपयोग करें
selected_scheme|Selected scheme|தேர்ந்தெடுத்த திட்டம்|चुनी गई योजना
scheme_auto|Problem-statement calculator|பிரச்சினை அறிக்கையின் கணிப்பான்|समस्या विवरण का कैलकुलेटर
apply_official|Official application guidance|அதிகாரப்பூர்வ விண்ணப்ப வழிகாட்டல்|आधिकारिक आवेदन मार्गदर्शन
income_limit|Annual family income limit|குடும்ப ஆண்டு வருமான வரம்பு|परिवार की वार्षिक आय सीमा
loan_cap|Maximum scheme loan|திட்டத்தின் அதிகபட்சக் கடன்|योजना में अधिकतम ऋण
scheme_catalog_note|Verified catalogue currently covers NSFDC Micro/Term and NBCFDC Individual loans. Other schemes need verified documents before inclusion. Gender alone does not exclude anyone from these three schemes.|தற்போது என்.எஸ்.எஃப்.டி.சி சிறு/காலக் கடன் மற்றும் என்.பி.சி.எஃப்.டி.சி தனிநபர் கடன் உள்ளன. மற்ற திட்டங்களுக்கு சரிபார்க்கப்பட்ட ஆவணங்கள் தேவை. இம்மூன்றிலும் பாலினத்தால் விலக்கு இல்லை.|अभी एनएसएफडीसी सूक्ष्म/सावधि और एनबीसीएफडीसी व्यक्तिगत ऋण शामिल हैं। अन्य योजनाओं के लिए सत्यापित दस्तावेज चाहिए। इन तीनों में लिंग के आधार पर रोक नहीं है।
nbcfdc_note|The remaining contribution may be shared with the channel partner. This estimate conservatively treats it as your own funds. Confirm the sanctioned share and grace-period interest.|மீதிப் பங்கை இடைநிலை நிறுவனம் பகிரலாம். இங்கு முழுவதும் உங்கள் சொந்த நிதியாகக் கருதப்படுகிறது. ஒப்புதல் பங்கு மற்றும் சலுகைக் கால வட்டியை உறுதி செய்யவும்.|शेष योगदान में चैनल पार्टनर हिस्सा दे सकता है। इस अनुमान में पूरा हिस्सा आपका माना गया है। स्वीकृत हिस्सा और छूट अवधि का ब्याज जांचें।
no_scheme_results|No schemes match these filters. Change filters or review your profile.|இந்த வடிகட்டிகளுக்கு திட்டங்கள் இல்லை. வடிகட்டிகள் அல்லது விவரங்களை மாற்றவும்.|इन फ़िल्टरों से कोई योजना नहीं मिली। फ़िल्टर या जानकारी बदलें।
check_profile|Update my profile|எனது விவரங்களை மாற்று|मेरी जानकारी बदलें
budget_health|Can this plan carry its repayments?|இந்தத் திட்டத்தால் தவணைகளைச் செலுத்த முடியுமா?|क्या यह योजना किस्तें चुका सकती है?
cash_positive|Estimated cash remains after costs and debt provision.|செலவு மற்றும் தவணைக்குப் பின் மதிப்பிட்ட பணம் மீதமுள்ளது.|खर्च और ऋण प्रावधान के बाद अनुमानित पैसा बचता है।
cash_negative|Estimated earnings do not cover costs and debt provision. Reduce costs or test a smaller setup.|மதிப்பிட்ட வருவாய் செலவு மற்றும் தவணைக்குப் போதாது. செலவைக் குறைக்கவும் அல்லது சிறிய அளவில் முயலவும்.|अनुमानित कमाई खर्च और ऋण प्रावधान नहीं चुकाती। खर्च घटाएं या छोटा काम आजमाएं।
allocation_note|Initial planning split. Equipment and inventory quantities need supplier quotes; this is not a shopping list yet.|ஆரம்ப நிதிப் பிரிவு. கருவி, சரக்கு அளவுகளுக்கு விற்பனையாளர் விலைப்புள்ளி தேவை; இது இன்னும் கொள்முதல் பட்டியல் அல்ல.|शुरुआती बजट विभाजन। उपकरण और माल की मात्रा के लिए विक्रेता भाव चाहिए; यह अभी खरीद सूची नहीं है।
tracker_intro|Record actual cash received and spent. Your forecast stays separate. Stored on this device.|உண்மையான வரவு செலவைப் பதிவு செய்யவும். கணிப்பு தனியாக இருக்கும். இந்தச் சாதனத்தில் சேமிக்கப்படும்.|वास्तविक प्राप्ति और खर्च दर्ज करें। अनुमान अलग रहता है। इस उपकरण पर सहेजा जाता है।
entry_type|Entry type|பதிவு வகை|प्रविष्टि प्रकार
income|Income|வரவு|आमदनी
expense|Expense|செலவு|खर्च
amount|Amount (₹)|தொகை (₹)|राशि (₹)
entry_date|Date|தேதி|तारीख
entry_note|Note (optional)|குறிப்பு (விருப்பம்)|विवरण (वैकल्पिक)
add_entry|Save entry|பதிவைச் சேமி|प्रविष्टि सहेजें
remove_entry|Remove entry|பதிவை நீக்கு|प्रविष्टि हटाएं
cash_balance|Recorded net cash|பதிவுசெய்த நிகரப் பணம்|दर्ज शुद्ध नकदी
no_entries|No entries yet. Add your first income or expense.|பதிவுகள் இல்லை. முதல் வரவு அல்லது செலவைச் சேர்க்கவும்.|अभी कोई प्रविष्टि नहीं। पहली आमदनी या खर्च जोड़ें।
invalid_entry|Enter a valid date and a positive amount with up to two decimal places.|சரியான தேதி மற்றும் இரண்டு தசம இடங்கள் வரை நேர்மத் தொகையை உள்ளிடவும்.|सही तारीख और अधिकतम दो दशमलव वाली धनात्मक राशि भरें।
track_plan|Track these planned repayments|இந்தத் திட்டத் தவணைகளைக் கண்காணி|इन नियोजित किस्तों को ट्रैक करें
tracked_plans|Saved repayment plans|சேமித்த தவணைத் திட்டங்கள்|सहेजी भुगतान योजनाएं
planned_not_sanctioned|Planning schedule only. Replace with the lender’s sanctioned terms before recording actual loan payments.|இது திட்டமிடும் அட்டவணை மட்டுமே. உண்மைக் கடன் செலுத்துதலுக்கு முன் கடன் நிறுவனத்தின் ஒப்புதல் விதிகளைப் பயன்படுத்தவும்.|यह केवल नियोजित समयसारणी है। वास्तविक भुगतान से पहले ऋणदाता की स्वीकृत शर्तें लें।
plan_saved|Repayment plan saved in Daily accounts.|தவணைத் திட்டம் தினசரி கணக்கில் சேமிக்கப்பட்டது.|भुगतान योजना दैनिक खाते में सहेजी गई।
no_tracked_plans|Save a repayment plan from the Repayments page.|தவணைப் பக்கத்திலிருந்து திட்டத்தைச் சேமிக்கவும்.|ऋण भुगतान पृष्ठ से योजना सहेजें।
help_schemes|Open Find a scheme. Complete your community and income in My profile, then check matching schemes and official application links.|கடன் திட்டங்களைத் திறக்கவும். எனது விவரங்களில் சமூகம், வருமானம் நிரப்பி பொருத்தமான திட்டங்களையும் விண்ணப்ப இணைப்புகளையும் பாருங்கள்.|योजना खोजें खोलें। मेरी जानकारी में समुदाय और आय भरकर मेल खाती योजनाएं और आवेदन लिंक देखें।
help_tracker|Open Daily accounts to record actual income and expenses and view saved repayment plans.|உண்மையான வரவு செலவு மற்றும் சேமித்த தவணைத் திட்டங்களுக்கு தினசரி கணக்கைத் திறக்கவும்.|वास्तविक आमदनी, खर्च और सहेजी किस्तें देखने के लिए दैनिक खाते खोलें।

nav_account|My account|எனது கணக்கு|मेरा खाता
account_intro|Create a local account to save your workspace on this computer’s server. This is not a cloud account.|இந்தக் கணினியின் சேவையகத்தில் பணியைச் சேமிக்க உள்ளூர் கணக்கை உருவாக்கவும். இது மேகக் கணக்கு அல்ல.|इस कंप्यूटर के सर्वर पर काम सहेजने के लिए स्थानीय खाता बनाएं। यह क्लाउड खाता नहीं है।
account_login|Sign in|உள்நுழை|साइन इन
account_register|Create account|கணக்கை உருவாக்கு|खाता बनाएं
account_reset|Recover account|கணக்கை மீட்டெடு|खाता पुनः प्राप्त करें
account_email|Email address|மின்னஞ்சல் முகவரி|ईमेल पता
account_password|Password (at least 10 characters)|கடவுச்சொல் (குறைந்தது 10 எழுத்துகள்)|पासवर्ड (कम से कम 10 अक्षर)
account_recovery|Recovery code|மீட்புக் குறியீடு|पुनर्प्राप्ति कोड
account_recovery_notice|Keep this recovery code privately. It is shown only now; it can reset your password. Email delivery is not configured.|இந்த மீட்புக் குறியீட்டை ரகசியமாகப் பாதுகாக்கவும். இப்போது மட்டுமே காட்டப்படும்; கடவுச்சொல்லை மாற்ற உதவும். மின்னஞ்சல் அனுப்புதல் அமைக்கப்படவில்லை.|यह कोड निजी रखें। अभी ही दिखता है और पासवर्ड बदल सकता है। ईमेल भेजना अभी उपलब्ध नहीं है।
account_recovery_saved|I saved my recovery code|மீட்புக் குறியீட்டைச் சேமித்தேன்|मैंने पुनर्प्राप्ति कोड सहेज लिया
account_save|Save workspace to my account|எனது கணக்கில் பணியைச் சேமி|काम मेरे खाते में सहेजें
account_load|Load saved workspace|சேமித்த பணியைத் திற|सहेजा काम खोलें
account_logout|Save and sign out|சேமித்து வெளியேறு|सहेजकर साइन आउट करें
account_saved|Workspace saved to your local account.|பணி உங்கள் உள்ளூர் கணக்கில் சேமிக்கப்பட்டது.|काम आपके स्थानीय खाते में सहेजा गया।
account_loaded|Saved workspace loaded.|சேமித்த பணி திறக்கப்பட்டது.|सहेजा काम खुल गया।
account_invalid|Email, password or recovery code is incorrect.|மின்னஞ்சல், கடவுச்சொல் அல்லது மீட்புக் குறியீடு தவறு.|ईमेल, पासवर्ड या पुनर्प्राप्ति कोड गलत है।
account_exists|This email already has a local account. Sign in or recover it.|இந்த மின்னஞ்சலுக்கு ஏற்கெனவே உள்ளூர் கணக்கு உள்ளது. உள்நுழையவும் அல்லது மீட்டெடுக்கவும்.|इस ईमेल का स्थानीय खाता मौजूद है। साइन इन करें या पुनः प्राप्त करें।
account_wait|Too many attempts. Wait a minute and try again.|பல முயற்சிகள். ஒரு நிமிடம் காத்திருந்து மீண்டும் முயலவும்.|बहुत प्रयास हुए। एक मिनट बाद फिर कोशिश करें।
account_login_needed|Sign in to access your saved workspace.|சேமித்த பணியை அணுக உள்நுழையவும்.|सहेजा काम खोलने के लिए साइन इन करें।
account_denied|This request is not allowed.|இந்தக் கோரிக்கை அனுமதிக்கப்படவில்லை.|इस अनुरोध की अनुमति नहीं है।
account_too_large|This workspace is too large to save. Export or reduce old records first.|இந்தப் பணி சேமிக்க மிகப் பெரியது. பழைய பதிவுகளை முதலில் குறைக்கவும்.|काम सहेजने के लिए बहुत बड़ा है। पहले पुराने रिकॉर्ड कम करें।
account_social|Google / Facebook sign-in|கூகுள் / பேஸ்புக் உள்நுழைவு|गूगल / फेसबुक साइन इन
account_social_pending|Requires provider setup. Use a local account for now.|வழங்குநர் அமைப்பு தேவை. இப்போது உள்ளூர் கணக்கைப் பயன்படுத்தவும்.|प्रदाता की व्यवस्था चाहिए। अभी स्थानीय खाता उपयोग करें।
account_switch_note|Signing in opens that account’s saved workspace. Guest work is kept separately and restored when you sign out.|உள்நுழைந்தால் அந்தக் கணக்கின் பணி திறக்கும். விருந்தினர் பணி தனியாக இருந்து வெளியேறும்போது மீண்டும் திறக்கும்.|साइन इन पर उस खाते का काम खुलेगा। अतिथि का काम अलग रहेगा और साइन आउट पर लौटेगा।
account_unsaved_note|Use Save after changes. Sign out saves your current workspace before leaving.|மாற்றங்களுக்குப் பின் சேமிக்கவும். வெளியேறும்போது தற்போதைய பணி சேமிக்கப்படும்.|बदलाव के बाद सहेजें। साइन आउट करते समय वर्तमान काम सहेजा जाता है।
account_confirm_load|Load the saved version and replace current device changes?|சேமித்த பதிப்பைத் திறந்து தற்போதைய மாற்றங்களை மாற்றவா?|सहेजा संस्करण खोलकर इस उपकरण के बदलाव बदलें?
help_account|Open My account to register, sign in or recover a local account. Save your recovery code safely.|பதிவு, உள்நுழைவு அல்லது மீட்புக்கு எனது கணக்கைத் திறக்கவும். மீட்புக் குறியீட்டை பாதுகாப்பாக வைக்கவும்.|स्थानीय पंजीकरण, साइन इन या पुनर्प्राप्ति के लिए मेरा खाता खोलें। पुनर्प्राप्ति कोड सुरक्षित रखें।
'''
root=Path(__file__).resolve().parents[1]/'frontend/src/locales';root.mkdir(parents=True,exist_ok=True)
data={l:{} for l in ['en','ta','hi']}
for line in ROWS.strip().splitlines():
 if not line.strip():continue
 key,*values=line.split('|');assert len(values)==3,(key,len(values))
 for lang,value in zip(data,values):
  assert key not in data[lang],key
  data[lang][key]=value
for lang,values in data.items():(root/f'{lang}.json').write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf8')
print('Translation keys per language:',len(data['en']))
