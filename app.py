"""
================================================================================
지능형 그룹핑 메일머지 시스템 (Intelligent Grouped Mail Merge System)
================================================================================
엑셀 데이터를 특정 Key를 기준으로 자동 그룹화하여,
각 그룹에 맞춤형 정산서 테이블을 포함한 이메일을 발송하는 엔터프라이즈 솔루션

Author: Senior Solution Architect (20 Years Experience)
Version: 3.0.0 - Enterprise Dashboard UI
================================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import time
import io
from jinja2 import Template
import re
import base64
import extra_streamlit_components as stx

# 로컬 모듈
from style import (
    render_email, render_preview, format_currency, format_percent, clean_id_column, format_date,
    get_styles, STREAMLIT_CUSTOM_CSS,
    DEFAULT_HEADER_TITLE, DEFAULT_HEADER_SUBTITLE, DEFAULT_GREETING,
    DEFAULT_INFO_MESSAGE, DEFAULT_ADDITIONAL_MESSAGE, DEFAULT_FOOTER_TEXT,
    DEFAULT_SUBJECT_TEMPLATE
)


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

APP_TITLE = "CSO 메일머지"
APP_SUBTITLE = "CSO 정산서 자동 발송 시스템"
VERSION = "3.0.0"

# SMTP 설정 우선순위: st.secrets > session_state > 수동 입력
DEFAULT_SENDER_NAME = "한국유니온제약"

STEPS = ["파일 업로드", "컬럼 설정", "데이터 검토", "템플릿 편집", "발송"]

SMTP_PROVIDERS = {
    "Hiworks (하이웍스)": {"server": "smtps.hiworks.com", "port": 465},
    "Gmail": {"server": "smtp.gmail.com", "port": 587},
    "Naver": {"server": "smtp.naver.com", "port": 587},
    "Daum/Kakao": {"server": "smtp.daum.net", "port": 465},
    "Outlook": {"server": "smtp-mail.outlook.com", "port": 587},
    "직접 입력": {"server": "", "port": 587},
}

DEFAULT_BATCH_SIZE = 10
DEFAULT_EMAIL_DELAY = 2
DEFAULT_BATCH_DELAY = 30


# ============================================================================
# CUSTOM CSS - Theme-Adaptive & Fully Responsive UI
# ============================================================================
# 단일 CSS 블록으로 SaaS급 UI 구현
# - Streamlit 테마 변수를 활용한 Light/Dark 모드 완벽 대응
# - 사이드바와 메인 화면의 위젯 스타일 통일
# - 8px 그리드 시스템 기반 일관된 여백
# ============================================================================

def apply_saas_style():
    """
    단일 CSS 블록으로 Streamlit 앱을 SaaS급 UI로 변환
    
    특징:
    - Light/Dark 모드 자동 대응 (Streamlit 테마 변수 활용)
    - 사이드바/메인 위젯 동일 스타일
    - 8px 그리드 기반 일관된 여백
    - Glass Morphism 효과
    - 부드러운 호버/트랜지션 효과
    """
    css = """
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        /* ============================================
           🎨 SaaS-Grade Design System
           Light/Dark 모드 완벽 대응
           ============================================ */
        
        /* ============================================
           🔧 extra-streamlit-components Material Icons 숨기기
           CookieManager 등이 사용하는 아이콘 텍스트 제거
           ============================================ */
        
        /* Material Icons 폰트 적용 */
        .material-icons {
            font-family: 'Material Icons' !important;
            font-size: 0 !important;
            visibility: hidden !important;
        }
        
        /* stx 컴포넌트의 아이콘 텍스트 완전 숨기기 */
        [class*="keyboard_double"],
        [class*="arrow_right"],
        [class*="arrow_left"],
        span:has(> .material-icons) {
            display: none !important;
        }
        
        /* iframe 내부 Material Icons도 숨기기 */
        iframe[title*="extra"] {
            display: none !important;
        }
        
        /* Expander summary 내 불필요한 텍스트 숨기기 */
        [data-testid="stExpander"] summary > div > div:first-child {
            display: flex !important;
            align-items: center !important;
        }
        
        /* _arrow 텍스트가 포함된 요소 숨기기 */
        [data-testid="stMarkdown"] p:empty,
        [data-testid="stMarkdown"]:has(> div:empty) {
            display: none !important;
        }
        
        :root {
            /* Streamlit 테마 변수 참조 */
            --st-primary: var(--primary-color);
            --st-bg: var(--background-color);
            --st-secondary-bg: var(--secondary-background-color);
            --st-text: var(--text-color);
            
            /* 시스템 폰트 - 이모지 완벽 지원 */
            --font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 
                           'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;
            
            /* Glass Morphism (테마 적응형) */
            --glass-overlay: rgba(128, 128, 128, 0.05);
            --glass-border: rgba(128, 128, 128, 0.12);
            --glass-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            --glass-hover-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
            
            /* 상태 색상 */
            --color-success: #10b981;
            --color-success-soft: rgba(16, 185, 129, 0.1);
            --color-warning: #f59e0b;
            --color-warning-soft: rgba(245, 158, 11, 0.1);
            --color-error: #ef4444;
            --color-error-soft: rgba(239, 68, 68, 0.1);
            --color-info: #3b82f6;
            --color-info-soft: rgba(59, 130, 246, 0.1);
            
            /* 8px 그리드 시스템 */
            --space-xs: 4px;
            --space-sm: 8px;
            --space-md: 16px;
            --space-lg: 24px;
            --space-xl: 32px;
            
            /* 모서리 반경 */
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-full: 9999px;
            
            /* 트랜지션 */
            --transition-fast: 150ms ease;
            --transition-normal: 250ms ease;
            
            /* 다크모드 지원 */
            color-scheme: light dark;
        }
        
        /* ============================================
           🌐 전역 폰트 적용
           ============================================ */
        html, body, [class*="st-"] {
            font-family: var(--font-family) !important;
        }
        
        /* ============================================
           📐 메인 레이아웃 컨테이너
           ============================================ */
        .main .block-container {
            max-width: 1200px;
            padding: var(--space-lg) var(--space-xl) !important;
        }
        
        /* ============================================
           🔧 사이드바 - 메인과 동일한 디자인 언어
           ============================================ */
        [data-testid="stSidebar"] {
            background: var(--st-secondary-bg) !important;
            border-right: 1px solid var(--glass-border);
        }
        
        [data-testid="stSidebar"] > div:first-child {
            padding: var(--space-md) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: var(--space-sm) !important;
        }
        
        /* ============================================
           🎯 Input Widgets - 통일된 스타일
           (사이드바 + 메인 동일 적용)
           ============================================ */
        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea,
        div[data-baseweb="input"] input,
        div[data-baseweb="select"] > div {
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--glass-border) !important;
            background: var(--st-bg) !important;
            color: var(--st-text) !important;
            box-shadow: var(--glass-shadow) !important;
            transition: all var(--transition-fast) !important;
            padding: 10px 14px !important;
        }
        
        [data-testid="stTextInput"] input:focus,
        [data-testid="stSelectbox"] > div > div:focus-within,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        div[data-baseweb="input"] input:focus {
            border-color: var(--st-primary) !important;
            box-shadow: 0 0 0 3px var(--color-info-soft) !important;
            outline: none !important;
        }
        
        /* ============================================
           🔘 Buttons - 통일된 스타일 + 호버 효과
           (사이드바 + 메인 동일 적용)
           ============================================ */
        .stButton > button {
            border-radius: var(--radius-md) !important;
            font-weight: 500 !important;
            transition: all var(--transition-normal) !important;
            border: 1px solid var(--glass-border) !important;
            min-height: 38px !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: var(--glass-hover-shadow) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) !important;
        }
        
        /* Primary 버튼 */
        .stButton > button[data-testid="baseButton-primary"],
        .stButton > button[kind="primary"] {
            background: var(--st-primary) !important;
            border-color: var(--st-primary) !important;
            color: white !important;
        }
        
        .stButton > button[data-testid="baseButton-primary"]:hover,
        .stButton > button[kind="primary"]:hover {
            filter: brightness(1.1) !important;
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35) !important;
        }
        
        /* Secondary 버튼 */
        .stButton > button[data-testid="baseButton-secondary"],
        .stButton > button[kind="secondary"] {
            background: var(--glass-overlay) !important;
            border: 1px solid var(--st-primary) !important;
            color: var(--st-primary) !important;
        }
        
        .stButton > button[data-testid="baseButton-secondary"]:hover,
        .stButton > button[kind="secondary"]:hover {
            background: var(--color-info-soft) !important;
        }
        
        /* ============================================
           📦 Expander - 깔끔한 접이식
           ============================================ */
        [data-testid="stExpander"] {
            border: 1px solid var(--glass-border) !important;
            border-radius: var(--radius-md) !important;
            background: var(--glass-overlay) !important;
            overflow: hidden;
            margin: var(--space-xs) 0 !important;
        }
        
        [data-testid="stExpander"] summary {
            padding: 12px 16px !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stExpander"] summary:hover {
            background: var(--glass-border) !important;
        }
        
        /* ============================================
           📊 Metrics - 카드 스타일
           ============================================ */
        [data-testid="stMetric"] {
            background: var(--glass-overlay) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: var(--radius-md) !important;
            padding: var(--space-md) !important;
            transition: all var(--transition-normal) !important;
        }
        
        [data-testid="stMetric"]:hover {
            box-shadow: var(--glass-hover-shadow) !important;
            transform: translateY(-2px) !important;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* ============================================
           💡 LED 상태 인디케이터
           ============================================ */
        .led-indicator {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 16px;
            border-radius: var(--radius-full);
            font-size: 0.8rem;
            font-weight: 500;
            background: var(--glass-overlay);
            border: 1px solid var(--glass-border);
            color: var(--st-text);
            transition: all var(--transition-normal);
        }
        
        .led-indicator .led-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        /* 연결됨 - 녹색 */
        .led-indicator.connected {
            background: var(--color-success-soft);
            border-color: var(--color-success);
        }
        .led-indicator.connected .led-dot {
            background: var(--color-success);
            box-shadow: 0 0 8px var(--color-success);
            animation: led-pulse 2s ease-in-out infinite;
        }
        
        /* 연결 필요 - 노란색 */
        .led-indicator.disconnected {
            background: var(--color-warning-soft);
            border-color: var(--color-warning);
        }
        .led-indicator.disconnected .led-dot {
            background: var(--color-warning);
            box-shadow: 0 0 8px var(--color-warning);
            animation: led-pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes led-pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(0.9); }
        }
        
        /* ============================================
           📁 파일 업로드 - Drag & Drop
           ============================================ */
        [data-testid="stFileUploader"] {
            border: 2px dashed var(--glass-border) !important;
            border-radius: var(--radius-md);
            padding: var(--space-lg);
            background: var(--glass-overlay);
            transition: all var(--transition-normal);
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: var(--st-primary) !important;
            background: var(--color-info-soft);
            box-shadow: 0 0 0 4px var(--color-info-soft);
        }
        
        /* ============================================
           📦 컨테이너/카드 (테마 적응형)
           ============================================ */
        [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--glass-border) !important;
            background: var(--glass-overlay);
        }
        
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--radius-md) !important;
        }
        
        /* ============================================
           📋 데이터프레임
           ============================================ */
        .stDataFrame {
            border-radius: var(--radius-md) !important;
            overflow: hidden;
            border: 1px solid var(--glass-border) !important;
        }
        
        /* ============================================
           ⚠️ 알림 메시지
           ============================================ */
        .stAlert {
            border-radius: var(--radius-sm) !important;
            border-left-width: 4px !important;
        }
        
        /* ============================================
           📈 프로그레스 바
           ============================================ */
        .stProgress > div > div {
            background: var(--st-primary);
            border-radius: var(--radius-full);
        }
        
        /* ============================================
           🏷️ 상태 배지 (Status Badge)
           ============================================ */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: var(--radius-full);
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-badge.success {
            background: var(--color-success-soft);
            color: var(--color-success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .status-badge.warning {
            background: var(--color-warning-soft);
            color: var(--color-warning);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        
        .status-badge.error {
            background: var(--color-error-soft);
            color: var(--color-error);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .status-badge.info {
            background: var(--color-info-soft);
            color: var(--color-info);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        
        .status-badge.sm {
            padding: 4px 10px;
            font-size: 0.7rem;
        }
        
        /* ============================================
           🔽 사이드바 푸터
           ============================================ */
        .sidebar-footer {
            text-align: center;
            padding: var(--space-md) 0;
            margin-top: var(--space-lg);
            font-size: 0.7rem;
            opacity: 0.7;
            border-top: 1px solid var(--glass-border);
            color: var(--st-text);
        }
        
        /* ============================================
           📱 탭 스타일
           ============================================ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: var(--glass-overlay);
            border-radius: var(--radius-md);
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: var(--radius-sm);
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background: var(--st-primary) !important;
        }
        
        /* ============================================
           🎯 스텝 인디케이터
           ============================================ */
        .step-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: var(--space-xs);
            padding: var(--space-md) var(--space-sm);
            background: var(--glass-overlay);
            border-radius: var(--radius-md);
            border: 1px solid var(--glass-border);
        }
        
        .step-item {
            flex: 1;
            text-align: center;
        }
        
        .step-circle {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: var(--space-xs);
            transition: all 0.3s ease;
        }
        
        .step-circle.active {
            background: var(--st-primary);
            color: white;
            box-shadow: 0 0 0 4px var(--color-info-soft), 0 4px 12px rgba(59, 130, 246, 0.3);
            transform: scale(1.05);
        }
        
        .step-circle.completed {
            background: var(--color-success);
            color: white;
            box-shadow: 0 2px 8px var(--color-success-soft);
        }
        
        .step-circle.pending {
            background: var(--st-secondary-bg);
            color: var(--st-text);
            border: 2px solid var(--glass-border);
            opacity: 0.6;
        }
        
        .step-label {
            font-size: 0.72rem;
            font-weight: 500;
            color: var(--st-text);
        }
        
        .step-label.active { color: var(--st-primary); font-weight: 600; }
        .step-label.completed { color: var(--color-success); }
        .step-label.pending { opacity: 0.6; }
        
        .step-line {
            flex: 0.5;
            height: 3px;
            background: var(--glass-border);
            margin-bottom: 22px;
            border-radius: 2px;
        }
        
        .step-line.completed {
            background: var(--color-success);
            box-shadow: 0 0 8px var(--color-success-soft);
        }
        
        .step-line.active {
            background: linear-gradient(90deg, var(--color-success), var(--st-primary));
        }
        
        /* ============================================
           🔄 로딩/스피너 스타일
           ============================================ */
        .stSpinner > div {
            border-top-color: var(--st-primary) !important;
        }
        
        .loading-shimmer {
            background: linear-gradient(90deg, var(--glass-overlay) 25%, rgba(128, 128, 128, 0.15) 50%, var(--glass-overlay) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* ============================================
           ✨ 전역 트랜지션 (테마 전환 부드럽게)
           ============================================ */
        * {
            transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        }
        
        /* 스크롤바 스타일 */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--glass-overlay); border-radius: var(--radius-full); }
        ::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: var(--radius-full); }
        ::-webkit-scrollbar-thumb:hover { background: var(--st-primary); }
        
        /* 포커스 가시성 (접근성) */
        *:focus-visible {
            outline: 2px solid var(--st-primary);
            outline-offset: 2px;
        }
        
        /* ============================================
           🍪 쿠키/Secrets 로드 입력 필드 강조
           ============================================ */
        .input-loaded-from-session input,
        .input-loaded-from-session textarea {
            border-color: var(--color-success) !important;
            border-width: 2px !important;
            box-shadow: 0 0 0 3px var(--color-success-soft) !important;
        }
        
        /* 비밀번호 필드 */
        .stTextInput input[type="password"] {
            letter-spacing: 2px;
            font-family: monospace;
        }
        
        /* ============================================
           📱 반응형 (모바일/태블릿)
           ============================================ */
        @media (max-width: 768px) {
            .main .block-container {
                padding: var(--space-md) var(--space-sm) !important;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }
            
            .step-circle {
                width: 32px;
                height: 32px;
                font-size: 0.8rem;
            }
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# 하위 호환성을 위한 CUSTOM_CSS 변수 유지 (apply_saas_style 함수 사용 권장)
CUSTOM_CSS = ""


# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        'current_step': 1,
        'df': None,
        'df_original': None,
        'df_email': None,
        'excel_file': None,
        'sheet_names': [],
        'selected_data_sheet': None,
        'selected_email_sheet': None,
        'use_separate_email_sheet': False,
        'group_key_col': None,
        'email_col': None,
        'join_col_data': None,
        'join_col_email': None,
        'amount_cols': [],
        'percent_cols': [],
        'date_cols': [],
        'id_cols': [],
        'display_cols': [],
        'display_cols_order': [],  # 컬럼 순서 저장
        'use_wildcard_grouping': True,
        'wildcard_suffixes': [' 합계'],
        'calculate_totals_auto': False,
        'grouped_data': {},
        'email_conflicts': [],
        'subject_template': DEFAULT_SUBJECT_TEMPLATE,
        'header_title': DEFAULT_HEADER_TITLE,
        'greeting_template': DEFAULT_GREETING,
        'info_template': DEFAULT_INFO_MESSAGE,
        'additional_template': DEFAULT_ADDITIONAL_MESSAGE,
        'footer_template': DEFAULT_FOOTER_TEXT,
        'send_results': [],
        'sent_count': 0,
        'failed_count': 0,
        'smtp_config': None,
        'conflict_resolution': 'first',
        # 발송 설정 기억
        'batch_size': DEFAULT_BATCH_SIZE,
        'email_delay_min': 5,
        'email_delay_max': 10,
        'batch_delay': DEFAULT_BATCH_DELAY,
        # 시트별 컬럼 설정 기억 (캐시)
        'column_settings_cache': {},
        # 운영 로그 (Operation First)
        'activity_log': [],
        'emergency_stop': False,
        # 발송 상태 추적 (멱등성 보장)
        'sent_groups': set(),  # 이미 발송 완료된 그룹
        # UI 상태
        'show_smtp_settings': False,  # SMTP 설정 패널 열기
        'current_page': '📧 메일 발송',  # 현재 페이지 (메일 발송 / 발송 이력)
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_column_settings(sheet_name: str):
    """현재 컬럼 설정을 캐시에 저장"""
    if 'column_settings_cache' not in st.session_state:
        st.session_state.column_settings_cache = {}
    
    st.session_state.column_settings_cache[sheet_name] = {
        'group_key_col': st.session_state.get('group_key_col'),
        'email_col': st.session_state.get('email_col'),
        'amount_cols': st.session_state.get('amount_cols', []),
        'percent_cols': st.session_state.get('percent_cols', []),
        'date_cols': st.session_state.get('date_cols', []),
        'id_cols': st.session_state.get('id_cols', []),
        'display_cols': st.session_state.get('display_cols', []),
        'display_cols_order': st.session_state.get('display_cols_order', []),
        'join_col_data': st.session_state.get('join_col_data'),
        'join_col_email': st.session_state.get('join_col_email'),
    }


def load_column_settings(sheet_name: str) -> bool:
    """캐시에서 컬럼 설정 로드 - 성공 시 True 반환"""
    cache = st.session_state.get('column_settings_cache', {})
    if sheet_name in cache:
        settings = cache[sheet_name]
        for key, value in settings.items():
            if value is not None:
                st.session_state[key] = value
        return True
    return False


def reset_workflow():
    """워크플로우 초기화"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()


def add_log(message: str, level: str = "info"):
    """운영 로그 추가 (Activity Log)"""
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(level, "📝")
    st.session_state.activity_log.append({
        'time': timestamp,
        'level': level,
        'icon': icon,
        'message': message
    })
    # 최대 100개 로그 유지
    if len(st.session_state.activity_log) > 100:
        st.session_state.activity_log = st.session_state.activity_log[-100:]


def sanity_check(grouped_data: dict) -> List[dict]:
    """발송 전 데이터 검증 (Sanity Check)"""
    warnings = []
    
    for group_name, data in grouped_data.items():
        # 금액 0원 체크
        if data.get('totals'):
            for col, val in data['totals'].items():
                try:
                    amount = float(str(val).replace(',', '').replace('원', ''))
                    if amount == 0:
                        warnings.append({
                            'group': group_name,
                            'type': 'zero_amount',
                            'message': f"금액 0원 ({col})"
                        })
                except:
                    pass
        
        # 이메일 없음 체크
        if not data.get('recipient_email'):
            warnings.append({
                'group': group_name,
                'type': 'no_email',
                'message': "이메일 주소 없음"
            })
        
        # 데이터 행 없음 체크
        if data.get('row_count', 0) == 0:
            warnings.append({
                'group': group_name,
                'type': 'no_data',
                'message': "데이터 행 없음"
            })
    
    return warnings


# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def load_excel_file(uploaded_file) -> Tuple[Optional[pd.ExcelFile], List[str], Optional[str]]:
    """엑셀 파일 로드"""
    try:
        file_name = uploaded_file.name.lower()
        if file_name.endswith(('.xlsx', '.xls')):
            xlsx = pd.ExcelFile(uploaded_file)
            return xlsx, xlsx.sheet_names, None
        elif file_name.endswith('.csv'):
            return None, ['CSV 데이터'], None
        else:
            return None, [], "지원하지 않는 파일 형식입니다."
    except Exception as e:
        return None, [], f"파일 로드 오류: {str(e)}"


def load_sheet(xlsx: pd.ExcelFile, sheet_name: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """시트 로드 - 항상 (DataFrame, error_message) 튜플 반환"""
    try:
        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        if df.empty:
            return None, "시트에 데이터가 없습니다."
        return df, None  # 성공 시 (df, None) 반환
    except Exception as e:
        return None, f"시트 로드 오류: {str(e)}"


def merge_email_data(df_data, df_email, join_col_data, join_col_email, email_col):
    """이메일 데이터 병합"""
    df_data = df_data.copy()
    df_email = df_email.copy()
    df_data['_join_key'] = df_data[join_col_data].astype(str).str.strip()
    df_email['_join_key'] = df_email[join_col_email].astype(str).str.strip()
    df_merged = df_data.merge(
        df_email[['_join_key', email_col]].drop_duplicates('_join_key'),
        on='_join_key', how='left'
    )
    df_merged.drop('_join_key', axis=1, inplace=True)
    return df_merged


def clean_dataframe(df, amount_cols, percent_cols, date_cols, id_cols):
    """데이터 정리"""
    df_cleaned = df.copy()
    for col in id_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].apply(clean_id_column)
    for col in date_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].apply(format_date)
    for col in amount_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(
                df_cleaned[col].astype(str).str.replace(',', '').str.replace('₩', '').str.strip(),
                errors='coerce'
            ).fillna(0)
    for col in percent_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(
                df_cleaned[col].astype(str).str.replace(',', '').str.replace('%', '').str.strip(),
                errors='coerce'
            ).fillna(0)
    return df_cleaned


def group_data_with_wildcard(df, group_key_col, email_col, amount_cols, percent_cols, display_cols,
                             conflict_resolution='first', use_wildcard=True,
                             wildcard_suffixes=None, calculate_totals=True):
    """와일드카드 그룹화"""
    if wildcard_suffixes is None:
        wildcard_suffixes = [" 합계"]
    
    grouped_data = {}
    conflicts = []
    
    def get_base_key(val):
        val_str = str(val).strip()
        for suffix in wildcard_suffixes:
            if val_str.endswith(suffix):
                return val_str[:-len(suffix)].strip()
        return val_str
    
    if use_wildcard:
        df = df.copy()
        df['_base_group_key'] = df[group_key_col].apply(get_base_key)
        group_col = '_base_group_key'
    else:
        group_col = group_key_col
    
    for base_key, group_df in df.groupby(group_col):
        base_key_str = str(base_key)
        if not base_key_str or base_key_str.lower() in ['nan', 'none', '(비어 있음)']:
            continue
        
        # 이메일 컬럼 존재 여부 확인
        if email_col and email_col in group_df.columns:
            unique_emails = [str(e).strip() for e in group_df[email_col].dropna().unique()
                            if str(e).strip() and str(e).strip().lower() not in ['nan', 'none', '']]
        else:
            unique_emails = []
        
        has_conflict = len(unique_emails) > 1
        if len(unique_emails) == 0:
            recipient_email = None
        elif len(unique_emails) == 1:
            recipient_email = unique_emails[0]
        else:
            if conflict_resolution == 'first':
                recipient_email = unique_emails[0]
            elif conflict_resolution == 'most_common' and email_col and email_col in group_df.columns:
                recipient_email = str(group_df[email_col].value_counts().index[0])
            else:
                recipient_email = unique_emails[0] if unique_emails else None
            conflicts.append({'group_key': base_key_str, 'emails': unique_emails,
                            'selected': recipient_email})
        
        def sort_key(row_val):
            return 1 if any(str(row_val).endswith(s) for s in wildcard_suffixes) else 0
        
        if use_wildcard:
            sorted_indices = group_df[group_key_col].apply(sort_key).sort_values().index
            group_df = group_df.loc[sorted_indices]
        
        rows = []
        for _, row in group_df.iterrows():
            row_dict = {}
            for col in display_cols:
                if col in row.index:
                    value = row[col]
                    # NaN/0 처리: 숫자면 0 표시, 그 외는 빈칸
                    if col in amount_cols:
                        row_dict[col] = format_currency(value)
                    elif col in percent_cols:
                        row_dict[col] = format_percent(value)
                    elif pd.isna(value) or value is None:
                        # 숫자 컬럼이면 0, 아니면 빈칸
                        row_dict[col] = ''
                    elif isinstance(value, (int, float)):
                        if value == 0 or pd.isna(value):
                            row_dict[col] = '0'
                        else:
                            row_dict[col] = str(value)
                    else:
                        str_val = str(value).strip()
                        if str_val.lower() in ['nan', 'none', 'nat', '']:
                            row_dict[col] = ''
                        else:
                            row_dict[col] = str_val
                else:
                    row_dict[col] = ''
            rows.append(row_dict)
        
        totals = {}
        if calculate_totals and use_wildcard:
            non_total_mask = ~group_df[group_key_col].apply(
                lambda x: any(str(x).endswith(s) for s in wildcard_suffixes))
            non_total_df = group_df[non_total_mask]
            for col in amount_cols:
                if col in non_total_df.columns:
                    totals[col] = format_currency(non_total_df[col].sum())
        else:
            for col in amount_cols:
                if col in group_df.columns:
                    totals[col] = format_currency(group_df[col].sum())
        
        grouped_data[base_key_str] = {
            'recipient_email': recipient_email,
            'rows': rows,
            'totals': totals,
            'row_count': len(rows),
            'has_conflict': has_conflict,
            'conflict_emails': unique_emails if has_conflict else [],
        }
    
    return grouped_data, conflicts


# ============================================================================
# EMAIL FUNCTIONS
# ============================================================================

def validate_email(email: str) -> bool:
    if not email:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email.strip()))


def create_smtp_connection(config, max_retries=3):
    """
    SMTP 연결 생성 - 하이웍스(Hiworks) SSL 최적화
    
    필수 조건:
    - Server: smtps.hiworks.com
    - Port: 465 (SSL)
    - smtplib.SMTP_SSL 사용 (일반 SMTP 아님)
    - From 헤더와 로그인 이메일 일치 필수 (553 에러 방지)
    """
    import ssl
    import socket
    last_error = None
    timeout = config.get('timeout', 30)
    
    for attempt in range(max_retries):
        try:
            if config['port'] == 465:
                # SSL 컨텍스트 설정 (하이웍스 호환)
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.set_ciphers('DEFAULT@SECLEVEL=1')
                
                # SMTP_SSL로 465 포트 직접 연결 (STARTTLS 아님)
                server = smtplib.SMTP_SSL(
                    config['server'], 
                    config['port'], 
                    context=context,
                    timeout=timeout
                )
            else:
                # 587 포트 등 STARTTLS 방식
                server = smtplib.SMTP(config['server'], config['port'], timeout=timeout)
                server.ehlo()
                if config.get('use_tls', True):
                    server.starttls()
                    server.ehlo()
            
            # 로그인 (이메일과 앱 비밀번호)
            server.login(config['username'], config['password'])
            return server, None
            
        except smtplib.SMTPAuthenticationError as e:
            error_code = e.smtp_code if hasattr(e, 'smtp_code') else 0
            error_str = str(e)
            
            # 454: 임시 인증 서버 오류 → 재시도
            if error_code == 454 or '454' in error_str or 'Temporary' in error_str:
                last_error = f"인증 서버 임시 오류 (시도 {attempt+1}/{max_retries})"
                time.sleep(2)
                continue
            
            # 535: 인증 거부 (비밀번호 오류)
            if error_code == 535 or '535' in error_str:
                return None, "❌ 인증 거부: 비밀번호가 틀렸거나 2차 앱 비밀번호가 필요합니다."
            
            # 553: 발신자 불일치 또는 IP 차단
            if error_code == 553 or '553' in error_str:
                if 'IP' in error_str:
                    return None, "❌ IP 차단: 하이웍스 관리자 설정에서 이 IP를 허용해야 합니다."
                return None, "❌ 발신자 불일치: From 주소와 로그인 이메일이 다릅니다."
            
            return None, f"❌ 인증 실패: {error_str[:150]}"
            
        except socket.timeout:
            last_error = f"연결 시간 초과 ({timeout}초) - 네트워크 확인 필요"
            time.sleep(2)
            continue
            
        except socket.gaierror:
            return None, "❌ 서버를 찾을 수 없음: 서버 주소 또는 인터넷 연결을 확인하세요."
            
        except ssl.SSLError as e:
            error_str = str(e)
            if 'handshake' in error_str.lower():
                last_error = f"SSL 핸드셰이크 실패 (시도 {attempt+1}/{max_retries})"
                time.sleep(2)
                continue
            return None, f"❌ SSL 오류: {error_str[:100]}"
            
        except ConnectionRefusedError:
            return None, "❌ 연결 거부: 서버 주소/포트가 올바른지 확인하세요."
            
        except Exception as e:
            error_str = str(e)
            if 'handshake' in error_str.lower() or 'ssl' in error_str.lower():
                last_error = f"SSL 연결 오류 (시도 {attempt+1}/{max_retries})"
                time.sleep(2)
                continue
            return None, f"❌ 연결 오류: {error_str[:100]}"
    
    return None, f"❌ 연결 실패: {last_error} - 네트워크 상태를 확인하고 잠시 후 다시 시도하세요."


def send_email(server, sender_email, recipient, subject, html_content, sender_name=None):
    """이메일 발송 함수"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        if sender_name:
            msg['From'] = formataddr((sender_name, sender_email))
        else:
            msg['From'] = formataddr((DEFAULT_SENDER_NAME, sender_email))
        msg['To'] = recipient
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        server.sendmail(sender_email, recipient, msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


def render_email_content(group_key, group_data, display_cols, amount_cols, templates):
    template_vars = {
        'company_name': group_key,
        'company_code': group_key,
        'period': datetime.now().strftime('%Y년 %m월'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'row_count': group_data['row_count'],
    }
    
    try:
        # 새로운 단순 본문 형식 지원
        greeting_text = templates.get('greeting', '')
        # 줄바꿈을 <br>로 변환
        greeting = Template(greeting_text).render(**template_vars)
        greeting = greeting.replace('\n', '<br>')
        
        info_text = templates.get('info', '')
        info_message = Template(info_text).render(**template_vars) if info_text else ''
        
        additional_text = templates.get('additional', '')
        additional = Template(additional_text).render(**template_vars) if additional_text else ''
        
        footer_text = templates.get('footer', '')
        footer = Template(footer_text).render(**template_vars) if footer_text else ''
    except Exception as e:
        greeting = templates.get('greeting', '').replace('\n', '<br>')
        info_message = templates.get('info', '')
        additional = templates.get('additional', '')
        footer = templates.get('footer', '')
    
    return render_email(
        subject=templates['subject'],
        header_title=templates['header_title'],
        greeting=greeting,
        columns=display_cols,
        rows=group_data['rows'],
        amount_columns=amount_cols,
        totals=group_data['totals'],
        info_message=info_message,
        additional_message=additional,
        footer_text=footer
    )


# ============================================================================
# UI COMPONENTS - Enterprise Dashboard Style
# ============================================================================

def render_header():
    """헤더 - SaaS Enterprise Dashboard 스타일 (사용되지 않음 - 사이드바로 이동)"""
    # 메인 영역 상단 여백만 추가 (헤더는 사이드바로 통합)
    pass


def render_step_indicator():
    """스텝 진행 상태 표시 - 테마 적응형 CSS 클래스 사용 (강화된 시각적 구분)"""
    current = st.session_state.current_step
    
    # 스텝 진행 바 (CSS 클래스 기반 - 테마 적응형)
    steps_html = '<div class="step-container">'
    
    for i, step_name in enumerate(STEPS, 1):
        if i < current:
            circle_class = "completed"
            label_class = "completed"
            icon = "✓"
        elif i == current:
            circle_class = "active"
            label_class = "active"
            icon = str(i)
        else:
            circle_class = "pending"
            label_class = "pending"
            icon = str(i)
        
        steps_html += f'''
        <div class="step-item">
            <div class="step-circle {circle_class}">{icon}</div>
            <div class="step-label {label_class}">{step_name}</div>
        </div>
        '''
        
        # 스텝 사이 연결선 (마지막 제외)
        if i < len(STEPS):
            if i < current:
                line_class = "completed"
            elif i == current:
                line_class = "active"
            else:
                line_class = ""
            steps_html += f'<div class="step-line {line_class}"></div>'
    
    steps_html += '</div>'
    st.markdown(steps_html, unsafe_allow_html=True)
    
    # 클릭 가능한 버튼 (완료된 스텝으로 이동) - 소형 버튼
    if current > 1:
        cols = st.columns(len(STEPS))
        for i, (col, step_name) in enumerate(zip(cols, STEPS), 1):
            with col:
                if i < current:
                    if st.button(f"← {i}", key=f"step_nav_{i}", help=f"{step_name}로 이동"):
                        st.session_state.current_step = i
                        st.rerun()
    
    st.divider()


def get_cookie_manager():
    """쿠키 매니저 - 세션별 싱글톤 (Material Icons 텍스트 숨김)"""
    if 'cookie_manager' not in st.session_state:
        # CookieManager 초기화 시 Material Icons 텍스트가 렌더링되므로 숨김 처리
        st.markdown('<div style="display:none !important; height:0; overflow:hidden;">', unsafe_allow_html=True)
        st.session_state.cookie_manager = stx.CookieManager(key="smtp_cookie_manager")
        st.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.cookie_manager


def encode_credential(value: str) -> str:
    """자격증명 인코딩 (Base64)"""
    if not value:
        return ""
    return base64.b64encode(value.encode()).decode()


def decode_credential(value: str) -> str:
    """자격증명 디코딩 (Base64)"""
    if not value:
        return ""
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception:
        return ""


def save_to_cookie(provider: str, username: str, password: str):
    """SMTP 자격증명을 쿠키에 저장 (90일 유효)"""
    try:
        cookie_manager = get_cookie_manager()
        expires = datetime.now() + timedelta(days=90)
        
        cookie_manager.set("smtp_provider", provider, expires_at=expires, key="set_provider")
        cookie_manager.set("smtp_username", encode_credential(username), expires_at=expires, key="set_username")
        cookie_manager.set("smtp_password", encode_credential(password), expires_at=expires, key="set_password")
    except Exception as e:
        pass


def load_from_cookie() -> dict:
    """쿠키에서 SMTP 자격증명 로드 (기본 동작)"""
    config = {
        'username': '',
        'password': '',
        'provider': 'Hiworks (하이웍스)',
        'from_cookie': False
    }
    
    try:
        cookie_manager = get_cookie_manager()
        
        provider = cookie_manager.get("smtp_provider")
        username_encoded = cookie_manager.get("smtp_username")
        password_encoded = cookie_manager.get("smtp_password")
        
        if username_encoded and password_encoded:
            config['provider'] = provider or 'Hiworks (하이웍스)'
            config['username'] = decode_credential(username_encoded)
            config['password'] = decode_credential(password_encoded)
            config['from_cookie'] = True
    except Exception:
        pass
    
    return config


def load_from_secrets() -> dict:
    """Secrets에서 SMTP 자격증명 로드 (버튼 클릭 시에만)"""
    config = {
        'username': '',
        'password': '',
        'provider': 'Hiworks (하이웍스)',
        'from_secrets': False
    }
    
    try:
        # .get() 메서드로 예외 처리
        username = st.secrets.get('SMTP_ID', '')
        password = st.secrets.get('SMTP_PW', '')
        
        if username and password:
            config['username'] = username
            config['password'] = password
            config['from_secrets'] = True
            config['provider'] = st.secrets.get('SMTP_PROVIDER', 'Hiworks (하이웍스)')
    except Exception:
        pass
    
    return config


def has_secrets_config() -> bool:
    """Secrets에 SMTP 설정이 있는지 확인"""
    try:
        return bool(st.secrets.get('SMTP_ID') and st.secrets.get('SMTP_PW'))
    except Exception:
        return False


def clear_cookie_credentials():
    """쿠키에서 SMTP 자격증명 삭제"""
    try:
        cookie_manager = get_cookie_manager()
        cookie_manager.delete("smtp_provider", key="del_provider")
        cookie_manager.delete("smtp_username", key="del_username")
        cookie_manager.delete("smtp_password", key="del_password")
    except Exception:
        pass


def get_smtp_config() -> dict:
    """SMTP 설정 로드 (Cookie 우선 > Secrets > Session)
    
    자동 로드 순서:
    1. Session State (이미 로드된 값)
    2. Cookie (브라우저 저장)
    3. Secrets (secrets.toml)
    """
    config = {
        'username': '',
        'password': '',
        'provider': 'Hiworks (하이웍스)',
        'from_secrets': False,
        'from_cookie': False
    }
    
    # 1. Session State에서 로드 (이미 로드된 값이 있으면)
    if st.session_state.get('saved_smtp_user'):
        config['username'] = st.session_state.saved_smtp_user
        config['password'] = st.session_state.get('saved_smtp_pass', '')
        config['provider'] = st.session_state.get('saved_smtp_provider', 'Hiworks (하이웍스)')
        config['from_cookie'] = st.session_state.get('loaded_from_cookie', False)
        config['from_secrets'] = st.session_state.get('loaded_from_secrets', False)
        return config
    
    # 2. Cookie에서 로드 (우선)
    cookie_config = load_from_cookie()
    if cookie_config.get('from_cookie') and cookie_config.get('username'):
        config.update(cookie_config)
        # 세션에도 저장
        st.session_state.saved_smtp_user = config['username']
        st.session_state.saved_smtp_pass = config['password']
        st.session_state.saved_smtp_provider = config['provider']
        st.session_state.loaded_from_cookie = True
        return config
    
    # 3. Cookie 없으면 Secrets에서 자동 로드
    secrets_config = load_from_secrets()
    if secrets_config.get('from_secrets') and secrets_config.get('username'):
        config.update(secrets_config)
        # 세션에도 저장
        st.session_state.saved_smtp_user = config['username']
        st.session_state.saved_smtp_pass = config['password']
        st.session_state.saved_smtp_provider = config['provider']
        st.session_state.loaded_from_secrets = True
    
    return config


def save_to_session(provider: str, username: str, password: str, save_cookie: bool = True):
    """SMTP 자격증명 세션 저장 (+ 쿠키 저장, 90일 유효)"""
    st.session_state.saved_smtp_provider = provider
    st.session_state.saved_smtp_user = username
    st.session_state.saved_smtp_pass = password
    
    # 쿠키에도 저장 (30일 유효)
    if save_cookie:
        save_to_cookie(provider, username, password)
        st.session_state.loaded_from_cookie = True


def clear_session_credentials():
    """세션 및 쿠키 자격증명 삭제"""
    for key in ['saved_smtp_provider', 'saved_smtp_user', 'saved_smtp_pass']:
        if key in st.session_state:
            del st.session_state[key]
    
    # 쿠키도 삭제
    clear_cookie_credentials()


def render_local_guide_dialog():
    """로컬 실행 가이드 다이얼로그"""
    
    @st.dialog("💻 로컬에서 실행하기", width="large")
    def show_guide():
        st.markdown("""
        <style>
        .guide-step {
            background: rgba(74, 158, 255, 0.1);
            border-left: 4px solid #4a9eff;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        .guide-code {
            background: rgba(0,0,0,0.3);
            padding: 0.8rem 1rem;
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            margin: 0.5rem 0;
            overflow-x: auto;
        }
        .guide-note {
            background: rgba(255, 193, 7, 0.15);
            border-left: 4px solid #ffc107;
            padding: 0.8rem 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 왜 로컬 실행이 필요한가요?")
        st.info("하이웍스 SMTP는 **허용된 IP에서만** 메일 발송이 가능합니다. 회사 네트워크(로컬)에서 실행하면 정상 작동합니다.", icon="💡")
        
        st.markdown("---")
        st.markdown("### 📋 설치 및 실행 가이드")
        
        # Step 1
        st.markdown('<div class="guide-step"><strong>Step 1.</strong> Python 설치 확인</div>', unsafe_allow_html=True)
        st.markdown('<div class="guide-code">python --version</div>', unsafe_allow_html=True)
        st.caption("Python 3.8 이상 필요 → [python.org](https://www.python.org/downloads/) 에서 다운로드")
        
        # Step 2
        st.markdown('<div class="guide-step"><strong>Step 2.</strong> 프로젝트 다운로드</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("📦 ZIP 다운로드", "https://github.com/yurielk82/mm-project/archive/refs/heads/main.zip", use_container_width=True)
        with col2:
            st.link_button("🔗 GitHub 열기", "https://github.com/yurielk82/mm-project", use_container_width=True)
        
        st.markdown('<div class="guide-code">git clone https://github.com/yurielk82/mm-project.git<br>cd mm-project</div>', unsafe_allow_html=True)
        st.caption("ZIP 다운로드 후 압축 해제하거나, 위 명령어로 클론")
        
        # Step 3
        st.markdown('<div class="guide-step"><strong>Step 3.</strong> 필수 패키지 설치</div>', unsafe_allow_html=True)
        st.markdown('<div class="guide-code">pip install -r requirements.txt</div>', unsafe_allow_html=True)
        
        # Step 4
        st.markdown('<div class="guide-step"><strong>Step 4.</strong> SMTP 설정 파일 생성 (선택)</div>', unsafe_allow_html=True)
        st.markdown("`.streamlit/secrets.toml` 파일 생성:")
        st.markdown('''<div class="guide-code">SMTP_ID = "your_email@company.com"<br>SMTP_PW = "your_app_password"<br>SMTP_PROVIDER = "Hiworks (하이웍스)"<br>SENDER_NAME = "발신자명"</div>''', unsafe_allow_html=True)
        
        # Step 5
        st.markdown('<div class="guide-step"><strong>Step 5.</strong> 앱 실행</div>', unsafe_allow_html=True)
        st.markdown('<div class="guide-code">streamlit run app.py</div>', unsafe_allow_html=True)
        st.caption("브라우저가 자동으로 열립니다 (http://localhost:8501)")
        
        st.markdown("---")
        
        # 주의사항
        st.markdown('<div class="guide-note">⚠️ <strong>주의:</strong> secrets.toml 파일은 절대 GitHub에 업로드하지 마세요!</div>', unsafe_allow_html=True)
        
        # 빠른 복사용
        with st.expander("📋 전체 명령어 복사"):
            st.code("""# 1. 프로젝트 다운로드
git clone https://github.com/yurielk82/mm-project.git
cd mm-project

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 앱 실행
streamlit run app.py""", language="bash")
        
        if st.button("닫기", use_container_width=True, type="primary"):
            st.rerun()
    
    return show_guide


def render_circular_progress(current_step: int, total_steps: int):
    """원형 프로그레스 인디케이터 (원래 크기 140px)"""
    progress = (current_step / total_steps) * 100
    size = 140
    stroke_width = 10
    radius = (size - stroke_width) / 2
    circumference = 2 * 3.14159 * radius
    stroke_dashoffset = circumference - (progress / 100) * circumference
    
    current_step_name = STEPS[current_step - 1] if current_step <= len(STEPS) else ""
    
    return f'''
<style>
.progress-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 8px 0 4px 0;
}}
.progress-circle {{
    position: relative;
    width: {size}px;
    height: {size}px;
}}
.progress-glow {{
    position: absolute;
    inset: 10px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,212,255,0.15) 0%, transparent 70%);
    filter: blur(10px);
}}
.progress-center {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}
.progress-step {{
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-color);
    line-height: 1;
}}
.progress-total {{
    font-size: 1rem;
    color: rgba(128,128,128,0.6);
}}
.progress-percent {{
    font-size: 0.85rem;
    color: #00d4ff;
    font-weight: 600;
}}
.progress-label {{
    text-align: center;
    margin-top: 6px;
}}
.progress-step-name {{
    font-size: 0.85rem;
    font-weight: 600;
    color: #00d4ff;
}}
.progress-status {{
    font-size: 0.65rem;
    color: rgba(128,128,128,0.7);
    margin-top: 1px;
    margin-top: 2px;
}}
</style>

<div class="progress-container">
    <div class="progress-circle">
        <div class="progress-glow"></div>
        <svg width="{size}" height="{size}" style="transform:rotate(-90deg);">
            <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="rgba(128,128,128,0.15)" stroke-width="{stroke_width}"/>
            <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="url(#progressGrad)" stroke-width="{stroke_width}" stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}" style="transition:stroke-dashoffset 0.5s ease-out;filter:drop-shadow(0 0 6px rgba(0,212,255,0.6));"/>
            <defs>
                <linearGradient id="progressGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#00d4ff"/>
                    <stop offset="100%" stop-color="#7c3aed"/>
                </linearGradient>
            </defs>
        </svg>
        <div class="progress-center">
            <div style="display:flex;align-items:baseline;gap:2px;">
                <span class="progress-step">{current_step}</span>
                <span class="progress-total">/ {total_steps}</span>
            </div>
            <span class="progress-percent">{int(progress)}%</span>
        </div>
    </div>
    <div class="progress-label">
        <div class="progress-step-name">{current_step_name}</div>
        <div class="progress-status">진행 중...</div>
    </div>
</div>
'''


def render_step_nav_buttons(current_step: int, total_steps: int):
    """이전/다음 텍스트 버튼 - 프로그레스 바와 밀착"""
    prev_disabled = current_step <= 1
    next_disabled = current_step >= total_steps
    
    # 컴팩트 네비게이션 버튼 CSS
    st.markdown("""
    <style>
    /* 네비게이션 버튼 - 8px 그리드 */
    .step-nav-container .stButton > button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 4px 8px !important;
        min-height: 28px !important;
        line-height: 1.2 !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
    }
    /* 이전 버튼 */
    .step-nav-container .nav-prev .stButton > button {
        color: rgba(128,128,128,0.65) !important;
    }
    .step-nav-container .nav-prev .stButton > button:hover:not(:disabled) {
        color: #fff !important;
    }
    /* 다음 버튼 */
    .step-nav-container .nav-next .stButton > button {
        color: #1E88E5 !important;
        font-weight: 600 !important;
    }
    .step-nav-container .nav-next .stButton > button:hover:not(:disabled) {
        color: #42A5F5 !important;
    }
    /* 비활성화 */
    .step-nav-container .stButton > button:disabled {
        opacity: 0.3 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 레이아웃: [이전] [다음]
    st.markdown('<div class="step-nav-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="nav-prev">', unsafe_allow_html=True)
        if st.button("‹ 이전", key="nav_prev", disabled=prev_disabled, use_container_width=True):
            st.session_state.current_step = current_step - 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="nav-next">', unsafe_allow_html=True)
        if st.button("다음 ›", key="nav_next", disabled=next_disabled, use_container_width=True):
            st.session_state.current_step = current_step + 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_smtp_sidebar():
    """사이드바 - Theme-Adaptive & Responsive UI"""
    with st.sidebar:
        
        # ============================================================
        # 🔝 원형 프로그레스 인디케이터 (메일 발송 페이지에서만 표시)
        # ============================================================
        current_page = st.session_state.get('current_page', '📧 메일 발송')
        
        if current_page == "📧 메일 발송":
            current_step = st.session_state.current_step
            total_steps = len(STEPS)
            
            # 원형 프로그레스 바
            st.markdown(render_circular_progress(current_step, total_steps), unsafe_allow_html=True)
            
            # 이전/다음 텍스트 버튼
            render_step_nav_buttons(current_step, total_steps)
            
            # 구분선
            st.markdown('<hr style="margin: 12px 0; border: none; border-top: 1px solid rgba(128,128,128,0.15);">', unsafe_allow_html=True)
        
        if st.session_state.smtp_config:
            # 연결됨 - 녹색 LED
            st.markdown("""
            <div class="led-indicator connected" style="width: 100%; justify-content: center; margin: 8px 0;">
                <span class="led-dot"></span>
                <span>SMTP 연결됨</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 연결 필요 - 노란색 LED (클릭 유도)
            st.markdown("""
            <div class="led-indicator disconnected" style="width: 100%; justify-content: center; margin: 8px 0; cursor: pointer;" title="아래 SMTP 설정을 열어 연결하세요">
                <span class="led-dot"></span>
                <span>SMTP 연결 필요</span>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================================
        # SMTP 계정 설정 (연결 성공 시 자동으로 닫힘)
        # ============================================================
        # SMTP 연결 상태에 따라 expander 열림/닫힘 결정
        smtp_connected = st.session_state.get('smtp_config') is not None
        smtp_expanded = not smtp_connected  # 연결 안됨 = 열림, 연결됨 = 닫힘
        
        with st.expander("⚙️ SMTP 설정", expanded=smtp_expanded):
            # 자동 로드: Cookie 우선 > Secrets
            smtp_defaults = get_smtp_config()
            from_cookie = smtp_defaults.get('from_cookie', False)
            from_secrets = smtp_defaults.get('from_secrets', False)
            
            # 로드 소스 표시 (미니멀 배지)
            if from_cookie:
                st.markdown('<div class="status-badge success" style="width:100%; justify-content:center; display:flex; margin-bottom:0.5rem;">🍪 저장된 설정 로드됨</div>', unsafe_allow_html=True)
            elif from_secrets:
                st.markdown('<div class="status-badge success" style="width:100%; justify-content:center; display:flex; margin-bottom:0.5rem;">🔐 관리자 설정 적용</div>', unsafe_allow_html=True)
            
            # 메일 서비스 선택
            provider_list = list(SMTP_PROVIDERS.keys())
            default_provider_idx = provider_list.index(smtp_defaults['provider']) if smtp_defaults['provider'] in provider_list else 0
            
            provider = st.selectbox(
                "메일 서비스", 
                provider_list, 
                index=default_provider_idx, 
                key="smtp_provider",
                help="사용 중인 메일 서비스를 선택하세요"
            )
            
            # 서버/포트 설정
            if provider == "직접 입력":
                smtp_server = st.text_input("SMTP 서버", key="smtp_server_input", placeholder="smtp.example.com")
                smtp_port = st.number_input("포트", value=587, key="smtp_port_input")
            else:
                smtp_server = SMTP_PROVIDERS[provider]["server"]
                smtp_port = SMTP_PROVIDERS[provider]["port"]
                st.caption(f"📡 `{smtp_server}:{smtp_port}`")
            
            # 자격증명 입력 (쿠키/Secrets 로드 시 시각적 표시)
            # 쿠키/Secrets에서 로드된 경우 CSS 클래스 추가
            session_loaded = from_cookie or from_secrets
            
            if session_loaded:
                st.markdown('<div class="input-loaded-from-session">', unsafe_allow_html=True)
            
            smtp_username = st.text_input(
                "📧 이메일 주소" if session_loaded else "이메일 주소", 
                value=smtp_defaults['username'],
                key="smtp_user",
                placeholder="your-email@company.com",
                help="🍪 저장된 세션에서 로드됨" if from_cookie else ("🔐 관리자 설정에서 로드됨" if from_secrets else None)
            )
            
            smtp_password = st.text_input(
                "🔑 앱 비밀번호" if session_loaded else "앱 비밀번호", 
                type="password",
                value=smtp_defaults['password'],
                key="smtp_pass",
                help="2단계 인증 사용 시 앱 비밀번호 필요" + (" (저장됨 ✓)" if session_loaded else "")
            )
            
            if session_loaded:
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 연결 테스트 버튼
            if st.button("🔌 연결 테스트", use_container_width=True, type="primary"):
                final_username = smtp_username or smtp_defaults['username']
                final_password = smtp_password or smtp_defaults['password']
                
                if final_username and final_password:
                    config = {
                        'server': smtp_server, 
                        'port': smtp_port,
                        'username': final_username, 
                        'password': final_password, 
                        'use_tls': True
                    }
                    with st.spinner("연결 중..."):
                        server, error = create_smtp_connection(config)
                        if server:
                            st.success("✅ 연결 성공!")
                            server.quit()
                            st.session_state.smtp_config = config
                            # 쿠키에 자동 저장 (90일)
                            save_to_session(provider, final_username, final_password, save_cookie=True)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"{error}")
                else:
                    st.warning("이메일과 비밀번호를 입력하세요")
        
        # ============================================================
        # 도움말 (접이식)
        # ============================================================
        with st.expander("📖 도움말", expanded=False):
            st.markdown("""
**secrets.toml 설정** (자동 로드용)
```toml
SMTP_ID = "email@company.com"
SMTP_PW = "app_password"
```
📁 위치: `.streamlit/secrets.toml`

**로드 우선순위:**
1. 🍪 브라우저 쿠키 (90일)
2. 🔐 secrets.toml 파일
3. ✏️ 수동 입력
            """)
        
        # ============================================================
        # 메뉴 (페이지 네비게이션) - expander
        # ============================================================
        current_page = st.session_state.get('current_page', '📧 메일 발송')
        
        with st.expander("📋 메뉴", expanded=False):
            if st.button("📧 메일 발송", use_container_width=True, 
                        type="primary" if current_page == "📧 메일 발송" else "secondary",
                        key="goto_mail"):
                st.session_state.current_page = '📧 메일 발송'
                st.rerun()
            
            if st.button("📜 발송 이력", use_container_width=True,
                        type="primary" if current_page == "📜 발송 이력" else "secondary",
                        key="goto_history"):
                st.session_state.current_page = '📜 발송 이력'
                st.rerun()
        
        # ============================================================
        # 로컬 실행 가이드 - expander
        # ============================================================
        with st.expander("💻 로컬 실행 가이드", expanded=False):
            if st.button("📖 가이드 보기", use_container_width=True, key="local_guide_btn"):
                st.session_state.show_local_guide = True
                st.rerun()
            
            st.link_button("📦 ZIP 다운로드", 
                          "https://github.com/yurielk82/mm-project/archive/refs/heads/main.zip",
                          use_container_width=True)
        
        st.markdown("""
        <div class="sidebar-footer">
            <strong>Designed by Kwon Dae-hwan</strong><br>
            © 2026 KUP Sales Management
        </div>
        """, unsafe_allow_html=True)


def render_step1():
    """Step 1: 파일 업로드"""
    
    # 파일 업로드
    with st.container(border=True):
        st.markdown("##### 📂 엑셀 파일 업로드")
        
        uploaded_file = st.file_uploader(
            "파일 선택", 
            type=['xlsx', 'xls', 'csv'],
            label_visibility="collapsed",
            help="xlsx, xls, csv 형식 지원"
        )
    
    if uploaded_file:
        xlsx, sheet_names, error = load_excel_file(uploaded_file)
        if error:
            st.error(error, icon="❌")
            return
        
        st.session_state.excel_file = xlsx
        st.session_state.sheet_names = sheet_names
        
        # ============================================================
        # 데이터 분석 요약 (파일 업로드 직후 표시)
        # ============================================================
        def analyze_data(df_data, df_email, use_separate, group_col=None):
            """데이터 분석 및 통계 계산"""
            stats = {
                'total_rows': 0,
                'total_groups': 0,
                'has_email': 0,
                'no_email': 0,
                'no_data': 0,
                'valid_for_send': 0
            }
            
            if df_data is None or df_data.empty:
                return stats
            
            stats['total_rows'] = len(df_data)
            
            # 그룹 컬럼 자동 탐지
            if group_col is None:
                group_candidates = [c for c in df_data.columns if 'CSO' in c or '관리업체' in c]
                group_col = group_candidates[0] if group_candidates else df_data.columns[0]
            
            # 유니크 그룹 수 (업체 수)
            unique_groups = df_data[group_col].dropna().unique()
            # 합계 행 제외
            unique_groups = [g for g in unique_groups if not str(g).endswith(' 합계') and str(g).lower() not in ['nan', 'none', '']]
            stats['total_groups'] = len(unique_groups)
            
            # 이메일 분석
            if use_separate and df_email is not None:
                # 별도 이메일 시트 사용
                email_col_candidates = [c for c in df_email.columns if '이메일' in c or 'mail' in c.lower()]
                if email_col_candidates:
                    email_col = email_col_candidates[0]
                    stats['has_email'] = df_email[email_col].notna().sum()
                    stats['no_email'] = len(df_email) - stats['has_email']
            else:
                # 같은 시트에서 이메일
                email_cols = [c for c in df_data.columns if '이메일' in c or 'mail' in c.lower()]
                if email_cols:
                    email_col = email_cols[0]
                    # 그룹별 이메일 보유 여부
                    for g in unique_groups:
                        group_data = df_data[df_data[group_col] == g]
                        if group_data[email_col].notna().any():
                            stats['has_email'] += 1
                        else:
                            stats['no_email'] += 1
            
            # 데이터 없는 그룹 (행이 0인 경우는 없으므로 0으로 유지)
            stats['valid_for_send'] = stats['has_email']
            
            return stats
        
        # 시트 선택 - 세로 배치
        with st.container(border=True):
            st.markdown("##### 📑 시트 선택")
            
            data_sheet = st.selectbox(
                "정산 데이터 시트", 
                sheet_names,
                index=sheet_names.index('정산서') if '정산서' in sheet_names else 0,
                help="정산 데이터가 있는 시트"
            )
            st.session_state.selected_data_sheet = data_sheet
            
            st.markdown("---")
            
            use_separate = st.checkbox(
                "이메일이 별도 시트에 있음",
                value=any('사업자' in s for s in sheet_names),
                help="이메일 주소가 다른 시트에 있는 경우"
            )
            st.session_state.use_separate_email_sheet = use_separate
            
            if use_separate:
                email_sheets = [s for s in sheet_names if s != data_sheet]
                if email_sheets:
                    default_idx = next((i for i, s in enumerate(email_sheets) if '사업자' in s), 0)
                    email_sheet = st.selectbox(
                        "이메일 시트", 
                        email_sheets, 
                        index=default_idx
                    )
                    st.session_state.selected_email_sheet = email_sheet
        
        # 데이터 로드
        if xlsx and data_sheet:
            df_data, err = load_sheet(xlsx, data_sheet)
            if not err and df_data is not None:
                st.session_state.df = df_data
                st.session_state.df_original = df_data.copy()
        
        # 이메일 시트 로드
        df_email_loaded = None
        if use_separate and st.session_state.get('selected_email_sheet'):
            df_email, err = load_sheet(xlsx, st.session_state.selected_email_sheet)
            if not err and df_email is not None:
                st.session_state.df_email = df_email
                df_email_loaded = df_email
        
        # ============================================================
        # 📊 데이터 분석 요약 (파일 업로드 직후 - 초록색 박스)
        # ============================================================
        if st.session_state.df is not None:
            stats = analyze_data(
                st.session_state.df, 
                df_email_loaded, 
                use_separate
            )
            
            # 분석 결과 표시 (초록색 success 박스)
            summary_parts = []
            
            # 전체 데이터 행
            summary_parts.append(f"📊 전체 데이터: **{stats['total_rows']:,}행**")
            
            # 전체 업체 수
            if stats['total_groups'] > 0:
                summary_parts.append(f"🏢 전체 업체: **{stats['total_groups']}개**")
            
            # 이메일 보유/미보유
            if stats['has_email'] > 0 or stats['no_email'] > 0:
                summary_parts.append(f"✉️ 이메일 보유: **{stats['has_email']}개**")
                if stats['no_email'] > 0:
                    summary_parts.append(f"❌ 이메일 없음: **{stats['no_email']}개**")
            
            # 발송 가능
            if stats['valid_for_send'] > 0:
                summary_parts.append(f"🚀 발송 가능: **{stats['valid_for_send']}개**")
            
            # 요약 표시
            st.success(" | ".join(summary_parts))
        
        # 데이터 미리보기 (접힘)
        if st.session_state.df is not None:
            with st.expander(f"📋 데이터 미리보기 ({len(st.session_state.df):,}행)", expanded=False):
                st.dataframe(st.session_state.df.head(10), use_container_width=True, hide_index=True)
        
        # 네비게이션
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("다음 단계 →", type="primary", use_container_width=True):
                if st.session_state.df is not None:
                    st.session_state.current_step = 2
                    st.rerun()


def render_step2():
    """Step 2: 컬럼 설정 - 기억 기능 및 중복 방지"""
    df = st.session_state.df
    if df is None:
        st.warning("먼저 파일을 업로드하세요", icon="⚠")
        return
    
    columns = df.columns.tolist()
    df_email = st.session_state.df_email
    use_separate = st.session_state.use_separate_email_sheet
    
    # 시트 이름으로 이전 설정 로드 시도
    sheet_name = st.session_state.get('selected_data_sheet', 'default')
    if 'column_settings_loaded' not in st.session_state:
        if load_column_settings(sheet_name):
            st.toast(f"'{sheet_name}' 시트의 이전 설정을 불러왔습니다", icon="💾")
        st.session_state.column_settings_loaded = True
    
    # 데이터 병합 설정
    if use_separate and df_email is not None:
        with st.container(border=True):
            st.markdown("##### 데이터 병합 설정")
            st.caption("정산서와 이메일 시트를 연결할 컬럼을 선택하세요")
            
            email_columns = df_email.columns.tolist()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                join_data = [c for c in columns if any(k in c for k in ['CSO', '관리업체'])]
                saved_join_data = st.session_state.get('join_col_data')
                default_idx = columns.index(saved_join_data) if saved_join_data in columns else (columns.index(join_data[0]) if join_data else 0)
                join_col_data = st.selectbox(
                    "정산서 매칭 컬럼", 
                    columns,
                    index=default_idx,
                    help="정산서에서 업체를 식별하는 컬럼"
                )
                st.session_state.join_col_data = join_col_data
            
            with col2:
                join_email = [c for c in email_columns if '거래처' in c]
                saved_join_email = st.session_state.get('join_col_email')
                default_idx = email_columns.index(saved_join_email) if saved_join_email in email_columns else (email_columns.index(join_email[0]) if join_email else 0)
                join_col_email = st.selectbox(
                    "이메일시트 매칭 컬럼", 
                    email_columns,
                    index=default_idx,
                    help="이메일 시트에서 업체를 식별하는 컬럼"
                )
                st.session_state.join_col_email = join_col_email
            
            with col3:
                email_cols = [c for c in email_columns if '이메일' in c or 'mail' in c.lower()]
                saved_email_col = st.session_state.get('email_col')
                default_idx = email_columns.index(saved_email_col) if saved_email_col in email_columns else (email_columns.index(email_cols[0]) if email_cols else 0)
                email_col = st.selectbox(
                    "이메일 주소 컬럼", 
                    email_columns,
                    index=default_idx,
                    help="이메일 주소가 있는 컬럼"
                )
                st.session_state.email_col = email_col
    
    # 그룹화 설정
    with st.container(border=True):
        st.markdown("##### 그룹화 설정")
        st.caption("데이터를 그룹으로 묶을 기준을 설정하세요")
        
        col1, col2 = st.columns(2)
        
        with col1:
            group_candidates = [c for c in columns if 'CSO' in c or '관리업체' in c]
            saved_group = st.session_state.get('group_key_col')
            default_idx = columns.index(saved_group) if saved_group in columns else (columns.index(group_candidates[0]) if group_candidates else 0)
            group_key_col = st.selectbox(
                "그룹화 기준 컬럼", 
                columns,
                index=default_idx,
                help="이 컬럼 값이 같은 행들이 하나의 그룹이 됩니다"
            )
            st.session_state.group_key_col = group_key_col
        
        with col2:
            use_wildcard = st.checkbox(
                "와일드카드 그룹핑", 
                value=st.session_state.get('use_wildcard_grouping', True),
                help="'에스투비'와 '에스투비 합계'를 같은 그룹으로 묶습니다"
            )
            st.session_state.use_wildcard_grouping = use_wildcard
        
        if use_wildcard:
            col1, col2 = st.columns(2)
            with col1:
                current_suffixes = ', '.join(st.session_state.get('wildcard_suffixes', [' 합계']))
                suffixes = st.text_input(
                    "접미사 패턴", 
                    current_suffixes,
                    help="쉼표로 구분하여 여러 패턴 입력 가능"
                )
                st.session_state.wildcard_suffixes = [s.strip() for s in suffixes.split(',') if s.strip()]
            with col2:
                calc_auto = st.checkbox(
                    "합계 자동 계산", 
                    value=st.session_state.get('calculate_totals_auto', False),
                    help="체크 해제 시 기존 합계 행의 값을 사용합니다"
                )
                st.session_state.calculate_totals_auto = calc_auto
            
            if st.session_state.wildcard_suffixes:
                def get_base(val):
                    v = str(val).strip()
                    for s in st.session_state.wildcard_suffixes:
                        if v.endswith(s):
                            return v[:-len(s)].strip()
                    return v
                
                unique_keys = df[group_key_col].dropna().unique()
                base_keys = set(get_base(k) for k in unique_keys)
                base_keys = [k for k in base_keys if k and k.lower() not in ['nan', '(비어 있음)']]
                st.success(f"예상 그룹 수: **{len(base_keys)}개**", icon="📊")
    
    # 데이터 타입 설정 (세로 나열, 중복 선택 방지)
    with st.container(border=True):
        st.markdown("##### 컬럼 타입 설정")
        st.caption("금액, 퍼센트, 날짜, ID 컬럼을 지정하면 자동 포맷팅됩니다 (중복 선택 불가)")
        
        # 이전 저장된 값 또는 기본값
        saved_amount = st.session_state.get('amount_cols', [])
        saved_percent = st.session_state.get('percent_cols', [])
        saved_date = st.session_state.get('date_cols', [])
        saved_id = st.session_state.get('id_cols', [])
        
        # 기본 후보
        amount_candidates = [c for c in columns if any(k in c for k in ['금액', '처방', '수수료'])]
        percent_candidates = [c for c in columns if any(k in c for k in ['%', '율', '퍼센트', 'percent', 'rate'])]
        date_candidates = [c for c in columns if '월' in c or 'date' in c.lower()]
        id_candidates = [c for c in columns if '코드' in c or '번호' in c]
        
        # 금액 컬럼
        amount_default = [c for c in saved_amount if c in columns] or [c for c in amount_candidates if c in columns]
        amount_cols = st.multiselect(
            "💰 금액 컬럼", 
            columns, 
            default=amount_default,
            help="천단위 쉼표가 적용됩니다 (예: 1,250,000)"
        )
        st.session_state.amount_cols = amount_cols
        
        # 퍼센트 컬럼 (금액과 겹치지 않게)
        available_for_percent = [c for c in columns if c not in amount_cols]
        percent_default = [c for c in saved_percent if c in available_for_percent] or [c for c in percent_candidates if c in available_for_percent]
        percent_cols = st.multiselect(
            "📊 퍼센트 컬럼", 
            available_for_percent, 
            default=percent_default,
            help="% 기호가 적용됩니다 (예: 15.0%)"
        )
        st.session_state.percent_cols = percent_cols
        
        # 날짜 컬럼 (금액/퍼센트와 겹치지 않게)
        available_for_date = [c for c in columns if c not in amount_cols and c not in percent_cols]
        date_default = [c for c in saved_date if c in available_for_date] or [c for c in date_candidates if c in available_for_date]
        date_cols = st.multiselect(
            "📅 날짜 컬럼", 
            available_for_date, 
            default=date_default,
            help="YYYY-MM-DD 형식으로 통일됩니다"
        )
        st.session_state.date_cols = date_cols
        
        # ID 컬럼 (금액/퍼센트/날짜와 겹치지 않게)
        available_for_id = [c for c in columns if c not in amount_cols and c not in percent_cols and c not in date_cols]
        id_default = [c for c in saved_id if c in available_for_id] or [c for c in id_candidates if c in available_for_id]
        id_cols = st.multiselect(
            "🔢 ID 컬럼", 
            available_for_id, 
            default=id_default,
            help="숫자 끝의 .0이 제거됩니다"
        )
        st.session_state.id_cols = id_cols
    
    # 표시 컬럼 선택 + 순서 조절
    with st.container(border=True):
        st.markdown("##### 이메일 표시 컬럼")
        st.caption("이메일 본문 테이블에 표시할 컬럼을 선택하고 순서를 조절하세요")
        
        # 최초 로드 시 모든 컬럼 선택 (그룹키 제외)
        saved_display = st.session_state.get('display_cols', [])
        if not saved_display:
            default_display = [c for c in columns if c != group_key_col]
        else:
            default_display = [c for c in saved_display if c in columns]
        
        display_cols = st.multiselect(
            "컬럼 선택 (전체)", 
            columns, 
            default=default_display,
            label_visibility="collapsed"
        )
        
        # 컬럼 순서 조절
        if display_cols and len(display_cols) > 1:
            st.markdown("**컬럼 순서 조절** (드래그 또는 번호로 조절)")
            
            # 현재 순서 또는 기본 순서
            current_order = st.session_state.get('display_cols_order', [])
            ordered_cols = [c for c in current_order if c in display_cols]
            ordered_cols += [c for c in display_cols if c not in ordered_cols]
            
            # 순서 조절 UI - 간단한 selectbox 방식
            new_order = []
            cols_per_row = 4
            for i in range(0, len(ordered_cols), cols_per_row):
                row_cols = st.columns(cols_per_row)
                for j, col in enumerate(row_cols):
                    idx = i + j
                    if idx < len(ordered_cols):
                        with col:
                            available = [c for c in ordered_cols if c not in new_order]
                            if available:
                                selected = st.selectbox(
                                    f"{idx+1}번째",
                                    available,
                                    index=available.index(ordered_cols[idx]) if ordered_cols[idx] in available else 0,
                                    key=f"col_order_{idx}"
                                )
                                new_order.append(selected)
            
            display_cols = new_order if new_order else display_cols
            st.session_state.display_cols_order = display_cols
        
        st.session_state.display_cols = display_cols
    
    # 충돌 해결
    with st.container(border=True):
        st.markdown("##### 이메일 충돌 처리")
        st.caption("한 그룹에 여러 이메일이 있을 때 처리 방법")
        
        saved_resolution = st.session_state.get('conflict_resolution', 'first')
        options = ['first', 'most_common', 'skip']
        conflict_resolution = st.radio(
            "충돌 해결 방식",
            options,
            index=options.index(saved_resolution) if saved_resolution in options else 0,
            format_func=lambda x: {'first': '첫 번째 이메일 사용', 'most_common': '가장 많이 등장한 이메일', 'skip': '해당 그룹 건너뛰기'}[x],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.conflict_resolution = conflict_resolution
    
    # 네비게이션 버튼
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            # 한 단계만 뒤로 (파일 선택 화면으로)
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        if st.button("다음 단계 →", type="primary", use_container_width=True):
            if not display_cols:
                st.error("표시할 컬럼을 1개 이상 선택하세요", icon="❌")
            else:
                # 현재 설정 저장
                save_column_settings(sheet_name)
                
                with st.spinner("데이터 처리 중..."):
                    df_work = df.copy()
                    
                    if use_separate and df_email is not None:
                        df_work = merge_email_data(df_work, df_email,
                            st.session_state.join_col_data,
                            st.session_state.join_col_email,
                            st.session_state.email_col)
                    
                    df_cleaned = clean_dataframe(df_work, amount_cols, percent_cols, date_cols, id_cols)
                    st.session_state.df = df_cleaned
                    
                    grouped, conflicts = group_data_with_wildcard(
                        df_cleaned, group_key_col, st.session_state.email_col,
                        amount_cols, percent_cols, display_cols, conflict_resolution,
                        use_wildcard, st.session_state.wildcard_suffixes,
                        st.session_state.calculate_totals_auto)
                    
                    st.session_state.grouped_data = grouped
                    st.session_state.email_conflicts = conflicts
                
                st.session_state.current_step = 3
                st.rerun()


def render_step3():
    """Step 3: 데이터 검토"""
    grouped = st.session_state.grouped_data
    if not grouped:
        st.warning("그룹 데이터가 없습니다", icon="⚠")
        return
    
    # 요약 메트릭 (상단 고정)
    total = len(grouped)
    valid = sum(1 for g in grouped.values() if g['recipient_email'] and validate_email(g['recipient_email']))
    no_email = total - valid
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 그룹", f"{total:,}개")
    with col2:
        st.metric("발송 가능", f"{valid:,}개", delta=f"{valid/total*100:.0f}%" if total > 0 else "0%")
    with col3:
        st.metric("이메일 없음", f"{no_email:,}개", delta=f"-{no_email}" if no_email > 0 else None, delta_color="inverse")
    
    st.divider()
    
    # 상세 검토 (위로 이동)
    with st.container(border=True):
        st.markdown("##### 상세 데이터 검토")
        st.caption("그룹을 선택하여 실제 발송될 데이터를 확인하세요")
        
        selected = st.selectbox(
            "그룹 선택",
            list(grouped.keys()),
            format_func=lambda x: f"{x} ({grouped[x]['row_count']}행)",
            label_visibility="collapsed"
        )
        
        if selected:
            g = grouped[selected]
            
            st.markdown(f"**수신자:** `{g['recipient_email'] or '없음'}`")
            if g['has_conflict']:
                st.warning(f"이메일 충돌: {', '.join(g['conflict_emails'])}", icon="⚠")
            
            st.dataframe(
                pd.DataFrame(g['rows']), 
                use_container_width=True, 
                hide_index=True,
                height=250
            )
    
    # 발송 대상 목록 (아래로 이동)
    with st.container(border=True):
        st.markdown("##### 발송 대상 목록")
        
        valid_list = [(k, v) for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])]
        
        if valid_list:
            preview_df = pd.DataFrame([
                {'업체명': k, '이메일': v['recipient_email'], '데이터 행수': v['row_count']}
                for k, v in valid_list
            ])
            
            st.dataframe(
                preview_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "업체명": st.column_config.TextColumn("업체명", width="medium"),
                    "이메일": st.column_config.TextColumn("이메일", width="large"),
                    "데이터 행수": st.column_config.NumberColumn("행수", format="%d", width="small")
                }
            )
        else:
            st.info("발송 가능한 대상이 없습니다", icon="ℹ")
    
    # 네비게이션
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    with col2:
        if st.button("다음 단계 →", type="primary", use_container_width=True, disabled=valid==0):
            st.session_state.current_step = 4
            st.rerun()


def render_step4():
    """Step 4: 템플릿 편집 - 세로 레이아웃, 미리보기 버튼"""
    
    # 템플릿 프리셋 정의
    TEMPLATE_PRESETS = {
        "기본 (정산서)": {
            "subject": "[한국유니온제약] {{ company_name }} {{ period }} 정산서",
            "header": "정산 내역 안내",
            "body": """안녕하세요, {{ company_name }} 담당자님.

{{ period }} 정산 내역을 안내드립니다.
아래 표를 확인해 주시기 바랍니다.

문의사항이 있으시면 회신 부탁드립니다.
감사합니다.""",
            "footer": "본 메일은 발신 전용입니다.\n문의: 영업관리팀"
        },
        "간단형": {
            "subject": "{{ company_name }} {{ period }} 정산 안내",
            "header": "정산서",
            "body": """{{ company_name }} 담당자님께,

{{ period }} 정산 내역 송부드립니다.
확인 부탁드립니다.""",
            "footer": ""
        },
        "상세형": {
            "subject": "[한국유니온제약] {{ company_name }} 귀하 - {{ period }} 월간 정산서",
            "header": "{{ period }} 월간 정산 내역서",
            "body": """안녕하세요, {{ company_name }} 담당자님.

항상 저희 한국유니온제약과 협력해 주셔서 감사합니다.

{{ period }} 정산 내역을 아래와 같이 송부 드리오니 
내용 확인 후 이상이 있으시면 연락 부탁드립니다.

감사합니다.""",
            "footer": "본 메일은 자동 발송되었습니다.\n문의사항: 영업관리팀 (내선 XXX)"
        }
    }
    
    # 템플릿 선택
    col_preset, col_apply = st.columns([3, 1])
    with col_preset:
        preset_name = st.selectbox(
            "📋 템플릿 프리셋",
            list(TEMPLATE_PRESETS.keys()),
            label_visibility="collapsed",
            help="미리 정의된 템플릿을 선택하세요"
        )
    with col_apply:
        if st.button("적용", use_container_width=True):
            preset = TEMPLATE_PRESETS[preset_name]
            st.session_state.subject_template = preset["subject"]
            st.session_state.header_title = preset["header"]
            st.session_state.email_body_text = preset["body"]
            st.session_state.footer_template = preset["footer"]
            st.rerun()
    
    st.divider()
    
    # 1. 이메일 제목
    st.markdown("##### 📧 이메일 제목")
    subject = st.text_input(
        "제목", 
        st.session_state.subject_template,
        label_visibility="collapsed",
        placeholder="예: [한국유니온제약] {{ company_name }} {{ period }} 정산서"
    )
    st.session_state.subject_template = subject
    
    # 2. 헤더
    st.markdown("##### 🏷️ 헤더 타이틀")
    header = st.text_input(
        "헤더", 
        st.session_state.header_title,
        label_visibility="collapsed",
        placeholder="정산 내역 안내"
    )
    st.session_state.header_title = header
    
    # 3. 본문 내용
    st.markdown("##### ✏️ 본문 내용")
    st.caption("테이블 위에 표시될 내용 ({{ company_name }}, {{ period }} 변수 사용 가능)")
    
    if 'email_body_text' not in st.session_state:
        st.session_state.email_body_text = TEMPLATE_PRESETS["기본 (정산서)"]["body"]
    
    body_text = st.text_area(
        "본문",
        st.session_state.email_body_text,
        height=180,
        label_visibility="collapsed",
        placeholder="안녕하세요, {{ company_name }} 담당자님..."
    )
    st.session_state.email_body_text = body_text
    st.session_state.greeting_template = body_text
    st.session_state.info_template = ""
    st.session_state.additional_template = ""
    
    # 4. (표 위치) - 안내만
    st.markdown("##### 📊 정산 테이블")
    st.info("이 위치에 데이터 테이블이 자동으로 삽입됩니다", icon="📊")
    
    # 5. 푸터
    st.markdown("##### 📝 푸터")
    footer = st.text_area(
        "푸터",
        st.session_state.footer_template,
        height=60,
        label_visibility="collapsed",
        placeholder="본 메일은 발신 전용입니다. 문의: 담당자 연락처"
    )
    st.session_state.footer_template = footer
    
    # 변수 설명 (접힘)
    with st.expander("💡 사용 가능한 변수", expanded=False):
        st.markdown("""
        | 변수 | 설명 | 예시 |
        |------|------|------|
        | `{{ company_name }}` | 업체명 | 에스투비 |
        | `{{ period }}` | 정산월 | 2024년 12월 |
        | `{{ company_code }}` | 업체코드 | 에스투비 |
        """)
    
    st.divider()
    
    # 미리보기 섹션
    grouped = st.session_state.grouped_data
    valid_list = [(k, v) for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])]
    
    if valid_list:
        st.markdown("##### 👁️ 미리보기")
        
        preview_options = [f"{k}" for k, v in valid_list[:20]]
        selected_idx = st.selectbox(
            "미리보기 대상 선택",
            range(len(preview_options)),
            format_func=lambda x: preview_options[x],
            label_visibility="collapsed"
        )
        
        # 선택된 데이터로 미리보기 생성
        sample_key, sample_data = valid_list[selected_idx]
        
        try:
            # 제목 렌더링
            subject_preview = Template(subject).render(
                company_name=sample_key,
                period=datetime.now().strftime('%Y년 %m월')
            )
            
            # 인사말 렌더링
            greeting_rendered = Template(body_text).render(
                company_name=sample_key,
                company_code=sample_key,
                period=datetime.now().strftime('%Y년 %m월')
            ).replace('\n', '<br>')
            
            # 실제 이메일 HTML 생성 (테이블 포함)
            display_cols = st.session_state.get('display_cols', [])
            amount_cols = st.session_state.get('amount_cols', [])
            
            email_html = render_email(
                subject=subject_preview,
                header_title=header,
                greeting=greeting_rendered,
                columns=display_cols,
                rows=sample_data.get('rows', []),
                amount_columns=amount_cols,
                totals=sample_data.get('totals'),
                footer_text=footer.replace('\n', '<br>') if footer else None
            )
            
            # 미리보기 정보 표시
            with st.container(border=True):
                st.markdown(f"**📧 수신자:** `{sample_data.get('recipient_email', 'N/A')}`")
                st.markdown(f"**📋 제목:** {subject_preview}")
                st.markdown(f"**📊 데이터:** {sample_data.get('row_count', 0)}행")
            
            # 이메일 본문 미리보기
            st.markdown("**📬 이메일 본문 미리보기**")
            
            # 행 수에 따라 높이 동적 계산
            row_count = len(sample_data.get('rows', []))
            base_height = 400  # 기본 높이 (헤더, 인사말, 푸터)
            row_height = 40    # 행당 높이
            calculated_height = base_height + (row_count * row_height)
            iframe_height = min(max(calculated_height, 500), 1200)  # 최소 500, 최대 1200
            
            # components.html로 실제 HTML 렌더링
            components.html(email_html, height=iframe_height, scrolling=True)
                
        except Exception as e:
            st.error(f"미리보기 오류: {e}")
            with st.expander("오류 상세"):
                import traceback
                st.code(traceback.format_exc())
    else:
        st.info("미리보기할 데이터가 없습니다. 먼저 데이터를 업로드하고 설정을 완료하세요.", icon="ℹ️")
    
    # 네비게이션
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    with col2:
        if st.button("발송 단계로 →", type="primary", use_container_width=True):
            st.session_state.current_step = 5
            st.rerun()


def render_step5():
    """Step 5: 발송 - UX 최적화 (안심 장치, 즉각적 피드백)"""
    grouped = st.session_state.grouped_data
    valid_groups = {k: v for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])}
    
    # 발송 요약 (상단 메트릭 카드) - SMTP는 사이드바에 있으므로 제외
    st.markdown("##### 📊 발송 요약")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("발송 대상", f"{len(valid_groups)}건", help="유효한 이메일이 있는 업체 수")
    with col2:
        success_cnt = sum(1 for r in st.session_state.get('send_results', []) if r.get('상태') == '성공')
        st.metric("발송 성공", f"{success_cnt}건", delta=None if success_cnt == 0 else f"+{success_cnt}")
    with col3:
        fail_cnt = sum(1 for r in st.session_state.get('send_results', []) if r.get('상태') == '실패')
        if fail_cnt > 0:
            st.metric("발송 실패", f"{fail_cnt}건", delta=f"-{fail_cnt}", delta_color="inverse")
        else:
            st.metric("발송 실패", "0건")
    
    st.divider()
    
    if not st.session_state.smtp_config:
        st.warning("📧 사이드바에서 SMTP 연결을 먼저 완료해 주세요", icon="⚠️")
    
    # 발송 설정 (이전 값 기억)
    with st.expander("⚙️ 발송 설정", expanded=False):
        st.caption("스팸 차단 방지를 위해 이메일 발송 간격을 조절합니다")
        
        col1, col2 = st.columns(2)
        with col1:
            batch_size = st.number_input(
                "📦 배치 크기", 
                value=st.session_state.get('batch_size', DEFAULT_BATCH_SIZE), 
                min_value=1, 
                max_value=50,
                help="연속으로 발송할 이메일 수. 예: 10이면 10통 발송 후 '배치 간격'만큼 대기"
            )
            st.session_state.batch_size = batch_size
        with col2:
            batch_delay = st.number_input(
                "⏸️ 배치 간격(초)", 
                value=st.session_state.get('batch_delay', DEFAULT_BATCH_DELAY), 
                min_value=5, 
                max_value=120,
                help="배치 완료 후 다음 배치 시작 전 대기 시간. 예: 30이면 10통 발송 후 30초 휴식"
            )
            st.session_state.batch_delay = batch_delay
        
        st.divider()
        
        st.markdown("**이메일 간 딜레이 (랜덤)**")
        col1, col2 = st.columns(2)
        with col1:
            email_delay_min = st.number_input(
                "⏱️ 최소(초)", 
                value=st.session_state.get('email_delay_min', 5), 
                min_value=1, 
                max_value=30,
                help="각 이메일 발송 후 최소 대기 시간"
            )
            st.session_state.email_delay_min = email_delay_min
        with col2:
            email_delay_max = st.number_input(
                "⏱️ 최대(초)", 
                value=st.session_state.get('email_delay_max', 10), 
                min_value=email_delay_min, 
                max_value=60,
                help="각 이메일 발송 후 최대 대기 시간"
            )
            st.session_state.email_delay_max = email_delay_max
        
        # 설정 요약
        st.info(f"""
        📧 **발송 패턴 예시** (배치 크기 {batch_size}, 딜레이 {email_delay_min}~{email_delay_max}초)
        
        1통 → {email_delay_min}~{email_delay_max}초 대기 → 2통 → ... → {batch_size}통 
        → **{batch_delay}초 휴식** → {batch_size+1}통 → ...
        """, icon="💡")
    
    st.divider()
    
    # 발송 버튼 영역
    st.markdown("##### 🚀 발송")
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()
    
    with col2:
        test_btn = st.button(
            "📧 내게 테스트",
            use_container_width=True,
            disabled=not st.session_state.smtp_config,
            help="내 이메일로 샘플 1건 발송하여 미리 확인"
        )
    
    with col3:
        # 실패 건만 재발송 버튼
        failed_list = [r for r in st.session_state.get('send_results', []) if r.get('상태') == '실패']
        resend_btn = st.button(
            f"🔄 실패 재발송 ({len(failed_list)})",
            use_container_width=True,
            disabled=not st.session_state.smtp_config or len(failed_list) == 0,
            help="실패한 건만 다시 발송"
        )
    
    with col4:
        send_btn = st.button(
            "🚀 전체 발송",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.smtp_config or len(valid_groups)==0,
            help=f"총 {len(valid_groups)}개 업체에 이메일 발송"
        )
    
    # 발송 확인 다이얼로그 상태
    if 'confirm_send' not in st.session_state:
        st.session_state.confirm_send = False
    
    # 전체 발송 클릭 시 확인
    if send_btn:
        st.session_state.confirm_send = True
    
    # 확인 다이얼로그
    if st.session_state.confirm_send:
        st.warning(f"⚠️ **총 {len(valid_groups)}개 업체**에 이메일을 발송합니다. 계속하시겠습니까?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            confirmed = st.button("✅ 예, 발송합니다", type="primary", use_container_width=True)
        with col_no:
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.confirm_send = False
                st.rerun()
        
        if not confirmed:
            send_btn = False  # 아직 확인 안됨
        else:
            st.session_state.confirm_send = False
            send_btn = True  # 확인됨, 발송 진행
    
    templates = {
        'subject': st.session_state.subject_template,
        'header_title': st.session_state.header_title,
        'greeting': st.session_state.greeting_template,
        'info': st.session_state.info_template,
        'additional': st.session_state.additional_template,
        'footer': st.session_state.footer_template
    }
    
    # 테스트 발송
    if test_btn and st.session_state.smtp_config and valid_groups:
        config = st.session_state.smtp_config
        sample_key, sample_data = list(valid_groups.items())[0]
        
        with st.spinner("테스트 발송 중..."):
            server, error = create_smtp_connection(config)
            if server:
                html = render_email_content(sample_key, sample_data,
                    st.session_state.display_cols, st.session_state.amount_cols, templates)
                subject = Template(templates['subject']).render(company_name=sample_key,
                    period=datetime.now().strftime('%Y년 %m월'))
                
                success, err = send_email(server, config['username'], config['username'],
                    f"[테스트] {subject}", html)
                server.quit()
                
                if success:
                    st.success(f"테스트 메일 발송 완료 → {config['username']}", icon="✅")
                else:
                    st.error(f"발송 실패: {err}", icon="❌")
            else:
                st.error(f"SMTP 연결 실패: {error}", icon="❌")
    
    # Sanity Check (발송 전 검증)
    if send_btn and st.session_state.smtp_config and valid_groups:
        warnings = sanity_check(st.session_state.grouped_data)
        if warnings:
            with st.expander(f"⚠️ 데이터 검증 경고 ({len(warnings)}건)", expanded=True):
                for w in warnings[:10]:  # 최대 10개만 표시
                    st.warning(f"**{w['group']}**: {w['message']}")
                if len(warnings) > 10:
                    st.caption(f"... 외 {len(warnings) - 10}건")
    
    # 전체 발송
    if send_btn and st.session_state.smtp_config and valid_groups:
        config = st.session_state.smtp_config
        add_log(f"발송 시작 - 총 {len(valid_groups)}건", "info")
        
        # 긴급 정지 버튼 + 진행률 표시 영역
        progress_container = st.container()
        with progress_container:
            col_progress, col_stop = st.columns([4, 1])
            with col_progress:
                progress_bar = st.progress(0)
            with col_stop:
                if st.button("🛑 긴급 정지", type="secondary", use_container_width=True):
                    st.session_state.emergency_stop = True
            
            status_col1, status_col2 = st.columns([3, 1])
            with status_col1:
                status_text = st.empty()
            with status_col2:
                count_text = st.empty()
        
        results = []
        success_cnt = fail_cnt = skipped_cnt = 0
        total = len(valid_groups)
        
        # 이미 발송된 그룹 확인 (멱등성)
        sent_groups = st.session_state.get('sent_groups', set())
        
        server, error = create_smtp_connection(config)
        if not server:
            st.error(f"SMTP 연결 실패: {error}", icon="❌")
            add_log(f"SMTP 연결 실패: {error}", "error")
        else:
            st.session_state.emergency_stop = False
            
            for i, (gk, gd) in enumerate(valid_groups.items()):
                # 긴급 정지 확인
                if st.session_state.get('emergency_stop', False):
                    status_text.markdown("**🛑 긴급 정지됨!**")
                    add_log(f"긴급 정지 - {i}건 발송 후 중단", "warning")
                    break
                
                # 멱등성 체크 - 이미 발송된 그룹은 건너뜀
                if gk in sent_groups:
                    skipped_cnt += 1
                    results.append({'그룹': gk, '이메일': gd['recipient_email'], '상태': '건너뜀', '사유': '이미 발송됨'})
                    continue
                
                progress_bar.progress((i+1)/total)
                status_text.markdown(f"**발송 중:** {gk}")
                count_text.markdown(f"`{i+1}/{total}`")
                
                try:
                    html = render_email_content(gk, gd, st.session_state.display_cols,
                        st.session_state.amount_cols, templates)
                    subject = Template(templates['subject']).render(company_name=gk,
                        period=datetime.now().strftime('%Y년 %m월'))
                    
                    ok, err = send_email(server, config['username'], gd['recipient_email'], subject, html)
                    
                    if ok:
                        success_cnt += 1
                        results.append({'그룹': gk, '이메일': gd['recipient_email'], '상태': '성공', '사유': ''})
                        sent_groups.add(gk)  # 발송 완료 표시
                        add_log(f"✓ {gk} → {gd['recipient_email']}", "success")
                    else:
                        fail_cnt += 1
                        # 상세 오류 메시지 파싱
                        error_detail = err
                        if 'SMTPAuthenticationError' in str(err):
                            error_detail = "인증 오류 (비밀번호 확인)"
                        elif 'SMTPRecipientsRefused' in str(err):
                            error_detail = "수신자 거부 (이메일 주소 확인)"
                        results.append({'그룹': gk, '이메일': gd['recipient_email'], '상태': '실패', '사유': error_detail})
                        add_log(f"✗ {gk}: {error_detail}", "error")
                except Exception as e:
                    fail_cnt += 1
                    results.append({'그룹': gk, '이메일': gd['recipient_email'], '상태': '실패', '사유': str(e)})
                    add_log(f"✗ {gk}: {str(e)}", "error")
                
                # 랜덤 딜레이 적용
                import random
                random_delay = random.uniform(email_delay_min, email_delay_max)
                time.sleep(random_delay)
                if (i+1) % batch_size == 0 and i < total-1:
                    time.sleep(batch_delay)
            
            server.quit()
            st.session_state.send_results = results
            st.session_state.sent_groups = sent_groups
            
            if not st.session_state.get('emergency_stop', False):
                status_text.markdown("**완료!**")
                add_log(f"발송 완료 - 성공: {success_cnt}, 실패: {fail_cnt}, 건너뜀: {skipped_cnt}", "info")
                
                # 발송 이력 DB 저장 (데이터 영속성)
                try:
                    init_database()
                    save_send_history(results, datetime.now().strftime('%Y년 %m월'))
                    add_log("발송 이력 DB 저장 완료", "info")
                except Exception as db_err:
                    add_log(f"DB 저장 실패: {str(db_err)}", "warning")
            
            if fail_cnt == 0:
                st.success(f"전체 발송 완료! ({success_cnt}건)", icon="🎉")
            else:
                st.warning(f"완료: 성공 {success_cnt}건, 실패 {fail_cnt}건", icon="⚠")
    
    # 결과 리포트 - "심리적 마감" UX
    if st.session_state.send_results:
        st.divider()
        
        results_df = pd.DataFrame(st.session_state.send_results)
        success_cnt = len(results_df[results_df['상태'] == '성공'])
        fail_cnt = len(results_df[results_df['상태'] == '실패'])
        
        # 완료 메시지 - 심리적 마감
        if fail_cnt == 0:
            st.success("🎉 **고생하셨습니다!** 모든 발송이 완료되었습니다.", icon="✅")
        else:
            st.warning(f"⚠️ 발송 완료: 성공 {success_cnt}건, 실패 {fail_cnt}건 (실패 건은 재발송 버튼으로 다시 시도할 수 있습니다)")
        
        with st.container(border=True):
            st.markdown("##### 📋 발송 결과 리포트")
            
            # 결과 요약 카드
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 발송", f"{len(results_df)}건")
            with col2:
                st.metric("✅ 성공", f"{success_cnt}건", delta=f"{success_cnt/len(results_df)*100:.0f}%" if results_df.shape[0] > 0 else "0%")
            with col3:
                if fail_cnt > 0:
                    st.metric("❌ 실패", f"{fail_cnt}건", delta=f"-{fail_cnt}", delta_color="inverse")
                else:
                    st.metric("❌ 실패", "0건")
            
            # 실패 건 강조 표시
            if fail_cnt > 0:
                st.markdown("**❌ 실패 목록** (빨간색 강조)")
                failed_df = results_df[results_df['상태'] == '실패']
                st.dataframe(
                    failed_df.style.apply(lambda x: ['background-color: #ffebee' if x['상태'] == '실패' else '' for _ in x], axis=1),
                    use_container_width=True,
                    hide_index=True
                )
            
            # 전체 결과 (접이식)
            with st.expander(f"📊 전체 결과 보기 ({len(results_df)}건)", expanded=False):
                # 상태별 색상 표시
                def highlight_status(row):
                    if row['상태'] == '성공':
                        return ['background-color: #e8f5e9'] * len(row)
                    else:
                        return ['background-color: #ffebee'] * len(row)
                
                st.dataframe(
                    results_df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    hide_index=True
                )
            
            # 다운로드 버튼
            st.markdown("---")
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    results_df.to_excel(writer, index=False, sheet_name='전체결과')
                    if fail_cnt > 0:
                        failed_df.to_excel(writer, index=False, sheet_name='실패목록')
                
                st.download_button(
                    "📥 전체 결과 다운로드",
                    output.getvalue(),
                    f"발송결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col_dl2:
                if fail_cnt > 0:
                    output_fail = io.BytesIO()
                    with pd.ExcelWriter(output_fail, engine='openpyxl') as writer:
                        failed_df.to_excel(writer, index=False)
                    
                    st.download_button(
                        "📥 실패 건만 다운로드",
                        output_fail.getvalue(),
                        f"발송실패_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
    
    # 운영 로그 (Activity Log) - Expander로 표시
    if st.session_state.get('activity_log'):
        with st.expander(f"📋 운영 로그 ({len(st.session_state.activity_log)}건)", expanded=False):
            log_container = st.container()
            with log_container:
                # 최신 로그가 위에 오도록 역순 정렬
                for log in reversed(st.session_state.activity_log[-50:]):
                    color = {"success": "#28a745", "error": "#dc3545", "warning": "#ffc107", "info": "#6c757d"}.get(log['level'], "#6c757d")
                    st.markdown(
                        f"<div style='font-family: monospace; font-size: 0.85rem; padding: 4px 8px; margin: 2px 0; "
                        f"border-left: 3px solid {color}; background: rgba(0,0,0,0.02);'>"
                        f"<span style='color: #888;'>[{log['time']}]</span> {log['icon']} {log['message']}</div>",
                        unsafe_allow_html=True
                    )


# ============================================================================
# DATA PERSISTENCE - 이력 저장 및 조회 (레퍼런스 4)
# ============================================================================

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'mail_history.db')


def init_database():
    """SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS send_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            period TEXT,
            company_name TEXT,
            company_code TEXT,
            recipient_email TEXT,
            subject TEXT,
            status TEXT,
            reason TEXT,
            row_count INTEGER,
            total_amount TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 인덱스 생성 (빠른 조회용)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_period ON send_history(period)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON send_history(company_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON send_history(timestamp)')
    
    conn.commit()
    conn.close()


def save_send_history(results: List[dict], period: str = None):
    """발송 결과를 DB에 저장"""
    if not period:
        period = datetime.now().strftime('%Y년 %m월')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for r in results:
        cursor.execute('''
            INSERT INTO send_history (period, company_name, recipient_email, subject, status, reason, row_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            period,
            r.get('그룹', ''),
            r.get('이메일', ''),
            r.get('subject', ''),
            r.get('상태', ''),
            r.get('사유', ''),
            r.get('row_count', 0)
        ))
    
    conn.commit()
    conn.close()


def get_send_history(period: str = None, company: str = None, limit: int = 100, offset: int = 0) -> pd.DataFrame:
    """발송 이력 조회 (페이지네이션 지원)"""
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT * FROM send_history WHERE 1=1"
    params = []
    
    if period:
        query += " AND period = ?"
        params.append(period)
    
    if company:
        query += " AND company_name LIKE ?"
        params.append(f"%{company}%")
    
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_statistics(period: str = None) -> dict:
    """발송 통계 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    where_clause = f"WHERE period = '{period}'" if period else ""
    
    # 총 발송 수
    cursor.execute(f"SELECT COUNT(*) FROM send_history {where_clause}")
    total = cursor.fetchone()[0]
    
    # 성공/실패 수
    cursor.execute(f"SELECT status, COUNT(*) FROM send_history {where_clause} GROUP BY status")
    status_counts = dict(cursor.fetchall())
    
    # 업체별 발송 수 (Top 10)
    cursor.execute(f'''
        SELECT company_name, COUNT(*) as cnt 
        FROM send_history {where_clause} 
        GROUP BY company_name 
        ORDER BY cnt DESC LIMIT 10
    ''')
    top_companies = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'success': status_counts.get('성공', 0),
        'failed': status_counts.get('실패', 0),
        'skipped': status_counts.get('건너뜀', 0),
        'top_companies': top_companies
    }


def render_history_tab():
    """발송 내역 조회 탭 (History Dashboard)"""
    st.markdown("### 📊 발송 내역 조회")
    
    # DB 초기화
    init_database()
    
    # 필터링 옵션
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        period_filter = st.text_input("정산월 검색", placeholder="예: 2025년 01월")
    
    with col2:
        company_filter = st.text_input("업체명 검색", placeholder="업체명 일부 입력")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍 검색", use_container_width=True)
    
    # 통계 카드
    stats = get_statistics(period_filter if period_filter else None)
    
    if stats['total'] > 0:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 발송", f"{stats['total']}건")
        with col2:
            rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            st.metric("성공률", f"{rate:.1f}%", delta=f"+{stats['success']}")
        with col3:
            st.metric("실패", f"{stats['failed']}건")
        with col4:
            st.metric("건너뜀", f"{stats['skipped']}건")
        
        # 업체별 발송 빈도 차트
        if stats['top_companies']:
            with st.expander("📈 업체별 발송 빈도 (Top 10)", expanded=False):
                import plotly.express as px
                chart_data = pd.DataFrame(stats['top_companies'], columns=['업체명', '발송 수'])
                fig = px.bar(chart_data, x='업체명', y='발송 수', title='업체별 발송 빈도')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # 이력 테이블
    df_history = get_send_history(
        period=period_filter if period_filter else None,
        company=company_filter if company_filter else None,
        limit=50
    )
    
    if not df_history.empty:
        st.markdown(f"**검색 결과: {len(df_history)}건**")
        
        # 상태별 색상
        def highlight_history(row):
            if row['status'] == '성공':
                return ['background-color: #e8f5e9'] * len(row)
            elif row['status'] == '실패':
                return ['background-color: #ffebee'] * len(row)
            return [''] * len(row)
        
        display_cols = ['timestamp', 'period', 'company_name', 'recipient_email', 'status', 'reason']
        display_names = {'timestamp': '발송시간', 'period': '정산월', 'company_name': '업체명', 
                        'recipient_email': '수신이메일', 'status': '상태', 'reason': '사유'}
        
        df_display = df_history[display_cols].rename(columns=display_names)
        st.dataframe(
            df_display.style.apply(highlight_history, axis=1),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("발송 이력이 없습니다.", icon="ℹ️")


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # SaaS급 CSS 스타일 적용
    apply_saas_style()
    
    init_session_state()
    
    # 로컬 실행 가이드 다이얼로그
    if st.session_state.get('show_local_guide', False):
        show_guide = render_local_guide_dialog()
        show_guide()
        st.session_state.show_local_guide = False
    
    render_smtp_sidebar()
    
    # DB 초기화 (History 탭용)
    try:
        init_database()
    except:
        pass
    
    # ============================================================
    # 메인 영역: 페이지 라우팅 (사이드바 메뉴 기반)
    # ============================================================
    current_page = st.session_state.get('current_page', '📧 메일 발송')
    
    if current_page == "📧 메일 발송":
        # ========== 메일 발송 페이지 ==========
        # 단계 표시는 사이드바의 원형 프로그레스로 대체 (중복 제거)
        
        # 현재 단계 렌더링
        step = st.session_state.current_step
        if step == 1:
            render_step1()
        elif step == 2:
            render_step2()
        elif step == 3:
            render_step3()
        elif step == 4:
            render_step4()
        elif step == 5:
            render_step5()
    
    elif current_page == "📜 발송 이력":
        # ========== 발송 이력 페이지 ==========
        st.markdown("## 📜 발송 이력")
        render_history_tab()


if __name__ == "__main__":
    main()
