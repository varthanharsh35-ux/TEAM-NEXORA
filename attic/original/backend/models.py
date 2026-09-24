from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class NearbyBusiness(BaseModel):
    id: str
    name: str
    category: str
    type: str  # competitor, amenity, financial
    distanceKm: float
    lat: float
    lon: float
    contact: Optional[str] = None
    address: Optional[str] = None
    gmapsUrl: str

class AssessmentInput(BaseModel):
    businessName: Optional[str] = "Proposed Enterprise"
    businessType: str = "retail"
    description: Optional[str] = ""
    location: str = "Wardha, Maharashtra"
    state: Optional[str] = "Maharashtra"
    district: Optional[str] = None
    pincode: Optional[str] = None
    lat: float = 20.7453
    lon: float = 78.6022
    radiusKm: float = Field(default=5.0, ge=1.0, le=25.0)
    initialCapital: float = Field(default=100000, ge=0)
    monthlyBudget: Optional[float] = None
    expectedMonthlyRevenue: Optional[float] = None
    priorExperienceYears: float = Field(default=0, ge=0)
    facilities: List[str] = []
    community: Optional[str] = "General"
    gender: Optional[str] = "All"
    education: Optional[str] = "Secondary"
    demographics: Optional[Dict[str, Any]] = None

class SWOTData(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

class StructuredVerdict(BaseModel):
    headline: str  # e.g. "Viable Opportunity", "Viable with Caveats", "Not Recommended"
    summary: str
    positiveFactors: List[str]
    negativeFactors: List[str]
    competitorComparison: str
    nextSteps: List[str]

class AssessmentResult(BaseModel):
    id: str
    businessName: str
    businessType: str
    location: str
    coordinates: Dict[str, float]
    radiusKm: float
    overallScore: int
    feasibilityGrade: str  # Excellent Viability, Viable Opportunity, Conditional Viability, High Risk
    riskLevel: str
    verdictReasoning: str
    structuredVerdict: Optional[StructuredVerdict] = None
    breakEvenMonths: int
    projectedMonthlyProfit: float
    dimensionScores: Dict[str, int]
    swot: SWOTData
    strengths: List[str]
    risks: List[str]
    recommendations: List[str]
    alternativeIdeas: List[Dict[str, Any]]
    nearbyCompetitors: List[NearbyBusiness]
    nearbyAmenities: List[NearbyBusiness]
    nearbyBanks: List[NearbyBusiness]
    competitorCount: int
    amenityCount: int
    bankCount: int
    matchedSchemes: List[Dict[str, Any]]

class FinancialPlanInput(BaseModel):
    investmentAmount: float = Field(default=200000, ge=5000)
    businessType: str = "retail"
    monthlyExpenses: Optional[float] = None
    expectedMarginPercent: float = 25.0
    contingencyReservePercent: float = 10.0

class FinancialPlanResult(BaseModel):
    capitalBreakdown: Dict[str, float]
    bareMinimumCapital: float
    establishedCapital: float
    averageSetupCost: float
    runwayMonths: int
    breakEvenMonths: int
    breakEvenUnitsMonthly: int
    operatingMargin: float
    returnOnInvestmentMonths: int
    financialHealthScore: int
    monthlyRecurring: Dict[str, float]
    monthlyProjection: List[Dict[str, Any]]
    recommendations: List[str]

class CashflowMonthDetail(BaseModel):
    month: int
    inflow: float
    outflow: float
    net: float
    endingBalance: float

class CashflowInput(BaseModel):
    initialBalance: float
    monthlyInflows: List[float]
    monthlyOutflows: List[float]
    months: int = 12

class CashflowResult(BaseModel):
    monthlyBreakdown: List[CashflowMonthDetail]
    lowestBalance: float
    peakCashMonth: int
    averageBurnRate: float
    isPositiveCashflow: bool
    suggestions: List[str]

class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    source: str = "GramSahayak-Site-Guide"
    suggestions: List[str]
    language: str = "en"
