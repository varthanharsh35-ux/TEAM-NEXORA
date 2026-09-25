from fastapi import APIRouter
from models import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["AI Navigation Guide"])

NAVIGATION_GUIDE = {
    "assessment": "To run a **Feasibility Assessment**:\n1. Click **'New Assessment'** in the sidebar or navbar.\n2. Complete the 5-step wizard (Business Idea, Location & Pin Drop, Capital, Demographic Profile).\n3. Click **'Analyze Feasibility'** to get real POIs, competitor density, SWOT, and a downloadable report.",
    
    "schemes": "To explore and apply for **Government Schemes**:\n1. Navigate to the **'Government Schemes'** page from the sidebar.\n2. Filter by loan amount, community category (SC/ST/OBC/Women/General), or scheme type.\n3. View official application links, explicit moratorium schedules, and nearby bank access points.",
    
    "emi": "To use the **Bidirectional EMI Calculator**:\n1. Open the **'Government Schemes'** page.\n2. Click the **'EMI Calculator'** button on any matched scheme or at the top.\n3. Switch between **'Calculate by Target Monthly EMI'** (to see required tenure & payoff date) or **'Calculate by Tenure'** (to see exact monthly installment).",
    
    "financial": "To plan your **Startup Capital & Runway**:\n1. Go to the **'Financial Plan'** page.\n2. Drag the **Startup Capital Slider** to dynamically recalculate setup costs, bare-minimum vs established setup requirements, monthly recurring expenses, and break-even timelines.",
    
    "cashflow": "To log daily business income and expenses:\n1. Go to the **'Cash Flow'** page.\n2. Click **'+ Add Transaction'** to record daily sales, inventory restocking, rent, or utility bills.\n3. View real-time net balances and monthly cash flow charts.",
    
    "credit": "To monitor **Credit Health & CIBIL**:\n1. Open the **'Credit Score'** page.\n2. View guidelines for loan eligibility, maintain credit utilization under 30%, and track registered facility repayment statuses.",
    
    "debt": "To manage **Active Loans & Liabilities**:\n1. Open the **'Debt Management'** page.\n2. Click **'+ Add Loan Record'** to log sanctioned schemes, principal balances, monthly EMIs, and upcoming due dates.",
    
    "export": "To export your **Feasibility Report**:\n1. After completing an assessment, open the **'Feasibility Report'** page.\n2. Click **'Export PDF'** or **'Export Word (.docx)'** at the top right to download a consulting-grade report.",
    
    "existing": "For running businesses looking to track inventory:\n1. Click **'Existing Business (Beta)'** on the landing page or navigation.\n2. Explore our upcoming stock register, debtor khata, and automated reconciliation features."
}

@router.post("/chat", response_model=ChatResponse)
async def guide_user_navigation(req: ChatRequest):
    msg = req.message.lower()
    reply = ""
    suggestions = []

    if any(w in msg for w in ["assess", "viability", "idea", "start", "evaluate", "feasibility"]):
        reply = NAVIGATION_GUIDE["assessment"]
        suggestions = ["How does the EMI calculator work?", "Where do I find matching schemes?", "How can I export my report?"]
    elif any(w in msg for w in ["scheme", "loan", "subsidy", "mudra", "svanidhi", "pmegp"]):
        reply = NAVIGATION_GUIDE["schemes"]
        suggestions = ["How do I calculate EMI?", "How do I run a business assessment?", "Where do I see nearby banks?"]
    elif any(w in msg for w in ["emi", "calculator", "interest", "tenure", "monthly payment"]):
        reply = NAVIGATION_GUIDE["emi"]
        suggestions = ["Where are matching government schemes?", "How to plan financial runway?", "How to export feasibility report?"]
    elif any(w in msg for w in ["finance", "financial", "setup cost", "capital", "breakeven", "runway"]):
        reply = NAVIGATION_GUIDE["financial"]
        suggestions = ["How do I track daily cash flow?", "Where do I find loans?", "How do I assess my business?"]
    elif any(w in msg for w in ["cash", "cashflow", "expense", "income", "transaction"]):
        reply = NAVIGATION_GUIDE["cashflow"]
        suggestions = ["How do I manage debts and EMIs?", "Where is the financial plan?", "How do I check my score?"]
    elif any(w in msg for w in ["credit", "cibil", "rating", "score"]):
        reply = NAVIGATION_GUIDE["credit"]
        suggestions = ["How do I manage loans on the site?", "Where are government subsidies?", "How to run an assessment?"]
    elif any(w in msg for w in ["debt", "liability", "due date", "outstanding"]):
        reply = NAVIGATION_GUIDE["debt"]
        suggestions = ["How does the EMI calculator work?", "How do I track daily cash flow?", "Where are matching schemes?"]
    elif any(w in msg for w in ["export", "pdf", "docx", "word", "download", "print"]):
        reply = NAVIGATION_GUIDE["export"]
        suggestions = ["How do I run a new assessment?", "Where is the financial plan?", "How to calculate loan EMI?"]
    elif any(w in msg for w in ["existing", "already", "inventory", "stock", "khata"]):
        reply = NAVIGATION_GUIDE["existing"]
        suggestions = ["How do I assess a new venture?", "Where is the cash flow tracker?", "Where are government schemes?"]
    elif any(w in msg for w in ["hello", "hi", "namaste", "help", "guide"]):
        reply = "Namaste! 🙏 I am your **GramSahayak Site Guide**. I help you navigate the platform and use its features.\n\nAsk me questions like:\n- *'How do I run a business assessment?'*\n- *'Where do I find government schemes?'*\n- *'How do I use the bidirectional EMI calculator?'*\n- *'How can I export my report to PDF or Word?'*"
        suggestions = ["How do I run a business assessment?", "Where do I find matching schemes?", "How does the EMI calculator work?", "How to export feasibility report?"]
    else:
        reply = "I am your **GramSahayak Site Navigation Assistant**. I can guide you to any feature or tool on this platform:\n- **Assessment Wizard**: Evaluate new venture viability\n- **Feasibility Dashboard**: View real competitor POIs, SWOT & export\n- **Schemes Catalog**: Government loans, moratoriums & nearby banks\n- **EMI Calculator**: Bidirectional installment & tenure calculation\n- **Financial Plan**: Capital breakdown & break-even simulation\n- **Cash Flow**: Daily income/expense tracking\n\nHow can I help you navigate today?"
        suggestions = ["How do I run a business assessment?", "Where are government schemes?", "How to calculate loan EMI?", "How to export report?"]

    return ChatResponse(
        reply=reply,
        source="GramSahayak-Site-Guide",
        suggestions=suggestions,
        language=req.language or "en"
    )
