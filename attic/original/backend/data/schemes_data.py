"""
Government Schemes Database for GramSahayak AI
Targeting rural and micro-entrepreneurs across India.

Each scheme includes `applicableSectors` to enable category-scoped filtering.
"""

GOVERNMENT_SCHEMES = [
    {
        "id": "pm-svanidhi",
        "name": "PM SVANidhi",
        "fullName": "Prime Minister Street Vendor's AtmaNirbhar Nidhi",
        "category": "microloan",
        "community": ["all", "general", "obc", "sc", "st"],
        "applicableSectors": ["retail", "food", "services", "handicraft", "textile", "other"],
        "maxAmount": 50000,
        "interestRate": 7.0,
        "tenure": 12,
        "moratorium": 3,
        "subsidyPercent": 7.0,
        "eligibility": "Street vendors and hawkers with a Certificate of Vending or Urban Local Body recommendation.",
        "eligibilityCriteria": [
            "Must possess a Certificate of Vending (CoV) or Letter of Recommendation (LoR) from ULB",
            "No minimum CIBIL score required",
            "Must have an active bank/mobile wallet account",
            "Age: 18 years and above"
        ],
        "benefits": "Collateral-free working capital loan starting at ₹10,000 up to ₹50,000 on prompt repayment with 7% interest subsidy.",
        "applyUrl": "https://pmsvanidhi.mohua.gov.in/",
        "documents": ["Aadhaar Card", "Vending ID Card / LoR", "Bank Account Details"]
    },
    {
        "id": "mudra-shishu",
        "name": "MUDRA - Shishu",
        "fullName": "Pradhan Mantri MUDRA Yojana (Shishu Category)",
        "category": "business_loan",
        "community": ["all", "women", "sc", "st", "obc"],
        "applicableSectors": ["retail", "food", "services", "handicraft", "textile", "agriculture", "dairy", "manufacturing", "transport", "other"],
        "maxAmount": 50000,
        "interestRate": 9.5,
        "tenure": 36,
        "moratorium": 0,
        "subsidyPercent": 0.0,
        "eligibility": "Small business starters, artisans, vegetable vendors, micro shop owners.",
        "eligibilityCriteria": [
            "No minimum CIBIL score; however, 650+ improves approval speed",
            "Must not have defaulted on any existing loan",
            "Business must be a non-farm, income-generating activity",
            "Age: 18 years and above"
        ],
        "benefits": "Up to ₹50,000 initial capital with zero collateral and minimal paperwork.",
        "applyUrl": "https://www.mudra.org.in/",
        "documents": ["Identity Proof", "Address Proof", "Quotation of Machinery / Stock"]
    },
    {
        "id": "mudra-kishore",
        "name": "MUDRA - Kishore",
        "fullName": "Pradhan Mantri MUDRA Yojana (Kishore Category)",
        "category": "business_loan",
        "community": ["all"],
        "applicableSectors": ["retail", "food", "services", "handicraft", "textile", "agriculture", "dairy", "manufacturing", "transport", "other"],
        "maxAmount": 500000,
        "interestRate": 10.5,
        "tenure": 60,
        "moratorium": 6,
        "subsidyPercent": 0.0,
        "eligibility": "Established micro-enterprises looking to expand operations or purchase equipment.",
        "eligibilityCriteria": [
            "Minimum CIBIL score required: 650+",
            "Business must be operational for at least 6 months",
            "Must have a business bank account with verifiable transaction history",
            "No existing loan defaults"
        ],
        "benefits": "Loans from ₹50,000 up to ₹5,00,000 without requiring third-party collateral.",
        "applyUrl": "https://www.mudra.org.in/",
        "documents": ["Last 6 Months Bank Statement", "Business Registration / Udyam", "Financial Projections"]
    },
    {
        "id": "pmegp",
        "name": "PMEGP",
        "fullName": "Prime Minister's Employment Generation Programme",
        "category": "subsidy_grant",
        "community": ["all", "rural", "women", "sc", "st", "minority"],
        "applicableSectors": ["retail", "food", "services", "handicraft", "textile", "agriculture", "dairy", "manufacturing", "transport", "other"],
        "maxAmount": 5000000,
        "interestRate": 11.0,
        "tenure": 84,
        "moratorium": 12,
        "subsidyPercent": 35.0,
        "eligibility": "Any individual above 18 years; 8th pass for projects above ₹10L in manufacturing or ₹5L in service.",
        "eligibilityCriteria": [
            "Minimum CIBIL score required: 700+ for amounts above ₹5 lakh",
            "Must be 8th standard pass for manufacturing projects above ₹10 lakh",
            "Must not have availed any previous government subsidy for self-employment",
            "Project must be new (not for expansion of existing unit under PMEGP)",
            "Age: 18 years and above"
        ],
        "benefits": "Subsidized credit-linked capital: 25% to 35% government subsidy for rural enterprises.",
        "applyUrl": "https://www.kviconline.gov.in/pmegpeportal/",
        "documents": ["Project Report", "Educational Qualification", "Caste/Special Category Certificate", "EDP Training Certificate"]
    },
    {
        "id": "standup-india",
        "name": "Stand-Up India",
        "fullName": "Stand-Up India Scheme for SC/ST and Women Entrepreneurs",
        "category": "business_loan",
        "community": ["women", "sc", "st"],
        "applicableSectors": ["retail", "food", "services", "handicraft", "textile", "agriculture", "dairy", "manufacturing", "transport", "other"],
        "maxAmount": 10000000,
        "interestRate": 8.5,
        "tenure": 84,
        "moratorium": 18,
        "subsidyPercent": 0.0,
        "eligibility": "Greenfield enterprise led by SC/ST or woman entrepreneur holding at least 51% shareholding.",
        "eligibilityCriteria": [
            "Minimum CIBIL score required: 700+",
            "Applicant must be SC, ST, or woman entrepreneur",
            "Must hold at least 51% shareholding in the enterprise",
            "Enterprise must be a greenfield project (new, not an expansion)",
            "Must not have more than 2 active existing loans"
        ],
        "benefits": "Bank loans between ₹10 Lakhs and ₹1 Crore for manufacturing, services, or trading sectors.",
        "applyUrl": "https://www.standupmitra.in/",
        "documents": ["Company / Firm Registration", "Proof of Category", "Detailed Project Report", "Margin Money Proof"]
    },
    {
        "id": "pmfme",
        "name": "PMFME Scheme",
        "fullName": "PM Formalisation of Micro Food Processing Enterprises",
        "category": "agro_business",
        "community": ["all", "rural", "farmer_groups"],
        "applicableSectors": ["food", "agriculture", "dairy"],
        "maxAmount": 1000000,
        "interestRate": 9.0,
        "tenure": 60,
        "moratorium": 6,
        "subsidyPercent": 35.0,
        "eligibility": "Existing individual micro food processing units, FPOs, SHGs, and Producer Cooperatives.",
        "eligibilityCriteria": [
            "No minimum CIBIL score for amounts under ₹5 lakh; 650+ for higher amounts",
            "Must be an existing micro food processing unit or have relevant FPO/SHG membership",
            "Must obtain or apply for FSSAI License",
            "Business must be operational for at least 1 year"
        ],
        "benefits": "Credit-linked capital subsidy @ 35% of eligible project cost with max ceiling of ₹10 lakh per unit.",
        "applyUrl": "https://pmfme.mofpi.gov.in/",
        "documents": ["Udyam Registration", "FSSAI License/Application", "Detailed Project Report"]
    },
    {
        "id": "lakhpati-didi",
        "name": "Lakhpati Didi",
        "fullName": "DAY-NRLM Lakhpati Didi Initiative",
        "category": "women_shg",
        "community": ["women", "shg", "rural"],
        "applicableSectors": ["retail", "food", "handicraft", "textile", "agriculture", "dairy", "services", "other"],
        "maxAmount": 200000,
        "interestRate": 4.0,
        "tenure": 36,
        "moratorium": 3,
        "subsidyPercent": 10.0,
        "eligibility": "Members of active Self Help Groups (SHGs) under Deendayal Antyodaya Yojana - NRLM.",
        "eligibilityCriteria": [
            "No minimum CIBIL score required",
            "Must be an active member of a DAY-NRLM Self Help Group",
            "SHG must comply with Panchasutra (5 principles)",
            "Applicant must be a woman"
        ],
        "benefits": "Interest subvention enabling effective interest as low as 4%, financial literacy training and market linkages.",
        "applyUrl": "https://nrlm.gov.in/",
        "documents": ["SHG Membership Resolution", "Panchasutra Adherence", "Aadhaar Card"]
    }
]
