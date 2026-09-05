

from typing import Optional
from pydantic import BaseModel

class ComponentsScores(BaseModel):
    formatting : float 
    keywords :float 
    content :float 
    skill_validation :float
    ats_compatibility :float


class JDComaparison(BaseModel):
    match_percentage:float
    semantic_similarity:float
    macthed_keywords:list[str]
    missing_keywords:list[str]
    skills_gap:list[str]

class SkillValidationDetails(BaseModel):
    validated:list[str]
    unvalidated:list[str]
    total : int =0
    validated_count: int =0
    validation_pct:float=0.0


class IssueDetails(BaseModel):
    issue_title:str
    severity_level:str
    ats_impact:str
    explanation:str
    where_it_appears:str
    how_to_fix:str
    action_items:list[str]=[]
    example_improvements:str

class AnalysisResponse:
    ATS_score:float
    components_scores:ComponentsScores
    issues_summary:list[str]
    detailed_feedback:list[IssueDetails]
    jd_match_Analysis:Optional[JDComaparison]=None
    skill_validation_details:Optional[SkillValidationDetails]=None

    ats_score:float
    keyword_match:float

    

