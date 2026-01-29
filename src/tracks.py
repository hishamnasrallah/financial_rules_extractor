"""
Track definitions and current rules for the Financial Rules Extraction system.
"""
from typing import Dict, List
from pydantic import BaseModel, Field


class TrackRule(BaseModel):
    """Represents a single rule within a track."""
    rule_id: str = Field(..., description="Unique identifier for the rule")
    description: str = Field(..., description="Description of the rule in Arabic")
    source: str = Field(default="System", description="Source of the rule")


class FinancialTrack(BaseModel):
    """Represents a financial track/workflow."""
    track_id: str = Field(..., description="Unique identifier for the track")
    name_ar: str = Field(..., description="Track name in Arabic")
    name_en: str = Field(..., description="Track name in English")
    definition_ar: str = Field(..., description="Track definition in Arabic")
    definition_en: str = Field(..., description="Track definition in English")
    current_rules: List[TrackRule] = Field(default_factory=list, description="Current rules")


class TracksRepository:
    """Repository for track definitions and current rules."""
    
    @staticmethod
    def get_all_tracks() -> Dict[str, FinancialTrack]:
        """Get all predefined financial tracks."""
        return {
            "contracts": FinancialTrack(
                track_id="contracts",
                name_ar="العقود",
                name_en="Contracts",
                definition_ar="يشمل أوامر دفع بناءً على نسبة إنجاز أو معلم محدد ضمن العقد، ويخضع للأنظمة مثل نظام المنافسات والمشتريات، تعليمات تنفيذ الميزانية، نظام استئجار العقار، وأوامر سامية",
                definition_en="Includes payment orders based on completion percentage or specific milestone within the contract, subject to regulations such as Competition and Procurement Law, Budget Execution Instructions, Real Estate Leasing Law, and Royal Orders",
                current_rules=[
                    TrackRule(
                        rule_id="CON-001",
                        description="وجود مستخلص يعكس مرحلته (أولي/جاري/ختامي) ومطابق لبيانات العقد وجدول الدفعات",
                    ),
                    TrackRule(
                        rule_id="CON-002",
                        description="في حالة المستخلص الختامي، يجب ألا تقل نسبته عن %10 من إجمالي قيمة العقد لعقود الإنشاءات العامة و %5 من العقود الأخرى",
                    ),
                    TrackRule(
                        rule_id="CON-003",
                        description="التحقق من سلامة إجراءات الترسية وأنها تمت وفقا لنظام المنافسات والمشتريات الحكومية والأنظمة والتعليمات ذات العلاقة وعدم وجود تحفظات في محضر لجنة فحص العروض",
                    ),
                    TrackRule(
                        rule_id="CON-004",
                        description="محضر تسليم الموقع أو بدء الأعمال",
                    ),
                ]
            ),
            "salaries": FinancialTrack(
                track_id="salaries",
                name_ar="الرواتب",
                name_en="Salaries",
                definition_ar="يشمل أوامر الدفع المتعلقة برواتب الموظفين، والبدلات، والمزايا الأخرى المرتبطة بالخدمة الحكومية",
                definition_en="Includes payment orders related to employee salaries, allowances, and other benefits associated with government service",
                current_rules=[
                    TrackRule(
                        rule_id="SAL-001",
                        description="التحقق من أن مجموع الحسميات لا يتجاوز ثلث الراتب الأساسي",
                    ),
                    TrackRule(
                        rule_id="SAL-002",
                        description="التحقق من عدم اختلاف صافي راتب الفرد بما لا يتجاوز 3%",
                    ),
                    TrackRule(
                        rule_id="SAL-003",
                        description="التحقق من أن الراتب الأساسي لكل موظف يتطابق مع الدرجة الوظيفية في السلم الرسمي",
                    ),
                    TrackRule(
                        rule_id="SAL-004",
                        description="التحقق من وجود خطاب تكليف للعمل الإضافي يتضمن جميع التفاصيل",
                    ),
                ]
            ),
            "invoices": FinancialTrack(
                track_id="invoices",
                name_ar="الفواتير",
                name_en="Invoices",
                definition_ar="يشمل المطالبات الناتجة عن فواتير الكهرباء، المياه، الجوال، وغيرها المقدمة مقابل خدمات استهلاكية فعلية",
                definition_en="Includes claims resulting from electricity, water, mobile bills, and others submitted in exchange for actual consumable services",
                current_rules=[
                    TrackRule(
                        rule_id="INV-001",
                        description="التحقق من عدم تكرار الصرف لنفس العملية",
                    ),
                    TrackRule(
                        rule_id="INV-002",
                        description="التحقق من مطابقة المبالغ المراد صرفها مع الفواتير",
                    ),
                    TrackRule(
                        rule_id="INV-003",
                        description="التحقق من أن الخدمة مرتبطة بجهة حكومية وليست بجهة خارجية",
                    ),
                    TrackRule(
                        rule_id="INV-004",
                        description="التحقق من مطابقتها لتسعيرة الشرائح الحكومية",
                    ),
                ]
            ),
        }
    
    @staticmethod
    def get_track(track_id: str) -> FinancialTrack:
        """Get a specific track by ID."""
        tracks = TracksRepository.get_all_tracks()
        if track_id not in tracks:
            raise ValueError(f"Track '{track_id}' not found")
        return tracks[track_id]
    
    @staticmethod
    def get_all_track_ids() -> List[str]:
        """Get all track IDs."""
        return list(TracksRepository.get_all_tracks().keys())
