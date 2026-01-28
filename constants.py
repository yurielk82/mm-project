"""
================================================================================
📋 Constants & Configuration Module
================================================================================
모든 상수, 기본값, 설정을 중앙 집중 관리합니다.
하드코딩을 최소화하고 유지보수성을 높입니다.

Author: Senior Solution Architect
Version: 1.0.0
================================================================================
"""

from typing import Dict, Any
from dataclasses import dataclass, field


# ============================================================================
# 🏢 APPLICATION METADATA
# ============================================================================

APP_TITLE = "CSO 메일머지"
APP_SUBTITLE = "CSO 정산서 자동 발송 시스템"
VERSION = "3.1.0"
AUTHOR = "KUP Sales Management"
COPYRIGHT_YEAR = "2026"


# ============================================================================
# 📧 SMTP PROVIDERS
# ============================================================================

SMTP_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "Hiworks (하이웍스)": {"server": "smtps.hiworks.com", "port": 465, "use_ssl": True},
    "Gmail": {"server": "smtp.gmail.com", "port": 587, "use_ssl": False},
    "Naver": {"server": "smtp.naver.com", "port": 587, "use_ssl": False},
    "Daum/Kakao": {"server": "smtp.daum.net", "port": 465, "use_ssl": True},
    "Outlook": {"server": "smtp-mail.outlook.com", "port": 587, "use_ssl": False},
    "직접 입력": {"server": "", "port": 587, "use_ssl": False},
}


# ============================================================================
# 📬 EMAIL SENDING DEFAULTS
# ============================================================================

DEFAULT_SENDER_NAME = "한국유니온제약"
DEFAULT_BATCH_SIZE = 10
DEFAULT_EMAIL_DELAY_MIN = 5  # 초
DEFAULT_EMAIL_DELAY_MAX = 10  # 초
DEFAULT_BATCH_DELAY = 30  # 초
MAX_RETRY_COUNT = 3


# ============================================================================
# 🎯 WORKFLOW STEPS
# ============================================================================

STEPS = ["파일 업로드", "컬럼 설정", "데이터 검토", "템플릿 편집", "발송"]


# ============================================================================
# 📝 EMAIL TEMPLATE PRESETS
# ============================================================================

@dataclass
class TemplatePreset:
    """이메일 템플릿 프리셋 데이터 클래스"""
    name: str
    subject: str
    header: str
    body: str
    footer: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "subject": self.subject,
            "header": self.header,
            "body": self.body,
            "footer": self.footer
        }


TEMPLATE_PRESETS = {
    "기본 (정산서)": TemplatePreset(
        name="기본 (정산서)",
        subject="[한국유니온제약] {{ company_name }} {{ period }} 정산서",
        header="정산 내역 안내",
        body="""안녕하세요, {{ company_name }} 담당자님.

{{ period }} 정산 내역을 안내드립니다.
아래 표를 확인해 주시기 바랍니다.

문의사항이 있으시면 회신 부탁드립니다.
감사합니다.""",
        footer="본 메일은 발신 전용입니다.\n문의: 영업관리팀"
    ),
    "간단형": TemplatePreset(
        name="간단형",
        subject="{{ company_name }} {{ period }} 정산 안내",
        header="정산서",
        body="""{{ company_name }} 담당자님께,

{{ period }} 정산 내역 송부드립니다.
확인 부탁드립니다.""",
        footer=""
    ),
    "상세형": TemplatePreset(
        name="상세형",
        subject="[한국유니온제약] {{ company_name }} 귀하 - {{ period }} 월간 정산서",
        header="{{ period }} 월간 정산 내역서",
        body="""안녕하세요, {{ company_name }} 담당자님.

항상 저희 한국유니온제약과 협력해 주셔서 감사합니다.

{{ period }} 정산 내역을 아래와 같이 송부 드리오니 
내용 확인 후 이상이 있으시면 연락 부탁드립니다.

감사합니다.""",
        footer="본 메일은 자동 발송되었습니다.\n문의사항: 영업관리팀 (내선 XXX)"
    )
}


# ============================================================================
# 🎨 THEME & COLORS (Semantic Colors)
# ============================================================================
# 하드코딩 색상을 최소화하고, 의미론적 색상만 정의합니다.
# Streamlit 테마 변수를 최대한 활용합니다.

class SemanticColors:
    """의미론적 색상 정의 - Light/Dark 모드 자동 대응"""
    
    # 상태 색상 (접근성 기준 충족)
    SUCCESS = "#22c55e"
    SUCCESS_SOFT = "rgba(34, 197, 94, 0.12)"
    
    WARNING = "#f59e0b"
    WARNING_SOFT = "rgba(245, 158, 11, 0.12)"
    
    ERROR = "#ef4444"
    ERROR_SOFT = "rgba(239, 68, 68, 0.12)"
    
    INFO = "#3b82f6"
    INFO_SOFT = "rgba(59, 130, 246, 0.12)"
    
    # 중립 색상 (테마 적응형)
    GLASS_OVERLAY = "rgba(128, 128, 128, 0.06)"
    GLASS_BORDER = "rgba(128, 128, 128, 0.12)"
    
    # 그라데이션 (브랜드 컬러)
    GRADIENT_PRIMARY = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    GRADIENT_SUCCESS = "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)"


# ============================================================================
# 📊 SESSION STATE DEFAULTS
# ============================================================================

SESSION_STATE_DEFAULTS: Dict[str, Any] = {
    # 워크플로우
    'current_step': 1,
    'current_page': '📧 메일 발송',
    
    # 데이터
    'df': None,
    'df_original': None,
    'df_email': None,
    'excel_file': None,
    'sheet_names': [],
    'selected_data_sheet': None,
    'selected_email_sheet': None,
    'use_separate_email_sheet': False,
    
    # 컬럼 설정
    'group_key_col': None,
    'email_col': None,
    'join_col_data': None,
    'join_col_email': None,
    'amount_cols': [],
    'percent_cols': [],
    'date_cols': [],
    'id_cols': [],
    'display_cols': [],
    'display_cols_order': [],
    'excluded_cols': [],
    
    # 그룹화 설정
    'use_wildcard_grouping': True,
    'wildcard_suffixes': [' 합계'],
    'calculate_totals_auto': False,
    'grouped_data': {},
    'email_conflicts': [],
    
    # 템플릿
    'subject_template': TEMPLATE_PRESETS["기본 (정산서)"].subject,
    'header_title': TEMPLATE_PRESETS["기본 (정산서)"].header,
    'greeting_template': TEMPLATE_PRESETS["기본 (정산서)"].body,
    'email_body_text': TEMPLATE_PRESETS["기본 (정산서)"].body,
    'info_template': '',
    'additional_template': '',
    'footer_template': TEMPLATE_PRESETS["기본 (정산서)"].footer,
    
    # 발송 설정
    'send_results': [],
    'sent_count': 0,
    'failed_count': 0,
    'smtp_config': None,
    'conflict_resolution': 'first',
    'batch_size': DEFAULT_BATCH_SIZE,
    'email_delay_min': DEFAULT_EMAIL_DELAY_MIN,
    'email_delay_max': DEFAULT_EMAIL_DELAY_MAX,
    'batch_delay': DEFAULT_BATCH_DELAY,
    
    # 캐시 및 상태
    'column_settings_cache': {},
    'activity_log': [],
    'emergency_stop': False,
    'sent_groups': set(),
    
    # UI 상태
    'show_smtp_settings': False,
    'zero_as_blank': True,
    'step2_config_loaded': False,
}


# ============================================================================
# 📁 FILE PATHS
# ============================================================================

CONFIG_COLUMNS_PATH = "config_columns.json"
MAIL_HISTORY_DB_PATH = "mail_history.db"


# ============================================================================
# 🔧 VALIDATION PATTERNS
# ============================================================================

import re

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_email(email: str) -> bool:
    """이메일 주소 유효성 검사"""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))


# ============================================================================
# 📋 UTILITY FUNCTIONS
# ============================================================================

def get_default_period() -> str:
    """현재 연월을 기본 정산 기간으로 반환"""
    from datetime import datetime
    return datetime.now().strftime('%Y년 %m월')


def get_template_variables() -> Dict[str, str]:
    """템플릿에서 사용 가능한 변수와 설명"""
    return {
        "{{ company_name }}": "업체명 (그룹 키)",
        "{{ company_code }}": "업체 코드 (그룹 키와 동일)",
        "{{ period }}": f"정산 기간 (예: {get_default_period()})",
        "{{ date }}": "오늘 날짜 (YYYY-MM-DD)",
        "{{ row_count }}": "데이터 행 수",
    }
