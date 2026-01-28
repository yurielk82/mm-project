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
import json
import os
import extra_streamlit_components as stx
from streamlit_sortables import sort_items

# 로컬 모듈 - 리팩토링된 통합 모듈
from email_template import (
    render_email, render_email_content, render_preview,
    format_currency, format_percent, clean_id_column, format_date,
    get_styles, EmailContext, EmailStyleConfig,
    DEFAULT_HEADER_TITLE, DEFAULT_HEADER_SUBTITLE, DEFAULT_GREETING,
    DEFAULT_INFO_MESSAGE, DEFAULT_ADDITIONAL_MESSAGE, DEFAULT_FOOTER_TEXT,
    DEFAULT_SUBJECT_TEMPLATE
)
from constants import (
    APP_TITLE, APP_SUBTITLE, VERSION, STEPS,
    SMTP_PROVIDERS, DEFAULT_SENDER_NAME,
    DEFAULT_BATCH_SIZE, DEFAULT_EMAIL_DELAY_MIN, DEFAULT_EMAIL_DELAY_MAX, DEFAULT_BATCH_DELAY,
    MAX_RETRY_COUNT, TEMPLATE_PRESETS, SemanticColors,
    SESSION_STATE_DEFAULTS, CONFIG_COLUMNS_PATH, MAIL_HISTORY_DB_PATH,
    validate_email as validate_email_pattern, get_default_period, get_template_variables
)
from style import STREAMLIT_CUSTOM_CSS


# ============================================================================
# CONFIGURATION & CONSTANTS (constants.py에서 import)
# ============================================================================
# 주요 상수는 constants.py에서 중앙 관리됩니다.
# APP_TITLE, APP_SUBTITLE, VERSION, STEPS, SMTP_PROVIDERS, 
# DEFAULT_SENDER_NAME, DEFAULT_BATCH_SIZE 등

# 하위 호환성을 위한 로컬 참조 (constants.py에서 import됨)
DEFAULT_EMAIL_DELAY = 2  # 레거시 - DEFAULT_EMAIL_DELAY_MIN/MAX 사용 권장


# ============================================================================
# CUSTOM CSS - Theme-Adaptive & Fully Responsive UI
# ============================================================================
# 핵심 원칙:
# 1. 하드코딩 색상 금지 - Streamlit 테마 변수만 사용
# 2. rgba() 기반 반투명 효과 - 테마 적응형
# 3. Flexbox/Grid + 미디어 쿼리 - 완전 반응형
# ============================================================================

CUSTOM_CSS = """
<style>
    /* ============================================
       🎨 Theme-Adaptive CSS Variables
       Streamlit 테마 엔진 변수 전용
       하드코딩 색상 완전 제거
       ============================================ */
    
    :root {
        /* Streamlit 테마 변수 참조 (하드코딩 금지) */
        --st-primary: var(--primary-color);
        --st-bg: var(--background-color);
        --st-secondary-bg: var(--secondary-background-color);
        --st-text: var(--text-color);
        
        /* 반투명 효과 (테마 적응형 - 중립 회색) */
        --glass-overlay: rgba(128, 128, 128, 0.06);
        --glass-border: rgba(128, 128, 128, 0.12);
        --glass-shadow: 0 4px 16px rgba(128, 128, 128, 0.08);
        --glass-hover-shadow: 0 8px 24px rgba(128, 128, 128, 0.12);
        
        /* 상태 색상 (의미론적 고정 - 접근성 유지) */
        --color-success: #22c55e;
        --color-success-soft: rgba(34, 197, 94, 0.12);
        --color-warning: #f59e0b;
        --color-warning-soft: rgba(245, 158, 11, 0.12);
        --color-error: #ef4444;
        --color-error-soft: rgba(239, 68, 68, 0.12);
        --color-info: #3b82f6;
        --color-info-soft: rgba(59, 130, 246, 0.12);
        
        /* 반응형 간격 */
        --space-xs: 0.25rem;
        --space-sm: 0.5rem;
        --space-md: 1rem;
        --space-lg: 1.5rem;
        --space-xl: 2rem;
        
        /* 모서리 반경 */
        --radius-sm: 6px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-full: 50px;
        
        /* 타이포그래피 */
        --font-weight-normal: 400;
        --font-weight-medium: 500;
        --font-weight-semibold: 600;
        --font-weight-bold: 700;
    }
    
    /* ============================================
       📱 반응형 미디어 쿼리 (완전 반응형)
       ============================================ */
    
    /* 모바일 (< 640px) */
    @media (max-width: 640px) {
        .main .block-container {
            padding: var(--space-sm) !important;
        }
        [data-testid="stMetric"] {
            padding: var(--space-sm) !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricLabel"] {
            font-size: 0.65rem !important;
        }
        .step-container {
            flex-wrap: wrap;
            gap: var(--space-sm);
        }
        .step-circle {
            width: 28px !important;
            height: 28px !important;
            font-size: 0.75rem !important;
        }
        .step-label {
            font-size: 0.65rem !important;
        }
        .led-indicator {
            padding: 6px 12px !important;
            font-size: 0.75rem !important;
        }
    }
    
    /* 태블릿 (640px - 1024px) */
    @media (min-width: 640px) and (max-width: 1024px) {
        .main .block-container {
            padding: var(--space-md) !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
        }
    }
    
    /* 데스크톱 (> 1024px) */
    @media (min-width: 1024px) {
        .main .block-container {
            max-width: 1200px;
            padding: var(--space-lg) var(--space-xl) !important;
        }
    }
    
    /* 대형 화면 (> 1400px) */
    @media (min-width: 1400px) {
        .main .block-container {
            max-width: 1400px;
        }
    }
    
    /* ============================================
       🔧 사이드바 - 테마 적응형 (깔끔한 구분)
       ============================================ */
    [data-testid="stSidebar"] {
        background: var(--st-secondary-bg) !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding: var(--space-md);
        display: flex;
        flex-direction: column;
        gap: var(--space-sm);
    }
    
    /* 사이드바 텍스트 - 테마 색상 상속 + 가독성 확보 */
    [data-testid="stSidebar"] * {
        color: var(--st-text) !important;
    }
    
    /* 사이드바 섹션 구분 */
    [data-testid="stSidebar"] hr {
        margin: var(--space-sm) 0;
        border: none;
        border-top: 1px solid var(--glass-border);
        opacity: 0.5;
    }
    
    /* 사이드바 메트릭 카드 - 세로 배치, 가로로 길게 */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: var(--glass-overlay) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: var(--radius-md) !important;
        padding: var(--space-md) var(--space-md) !important;
        margin-bottom: var(--space-sm) !important;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: var(--font-weight-bold) !important;
        text-align: right;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        font-weight: var(--font-weight-medium) !important;
        opacity: 0.9;
        text-align: left;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricDelta"] {
        font-size: 0.7rem !important;
        text-align: right;
    }
    
    /* ============================================
       💡 LED 상태 인디케이터 (강화된 글로우 효과)
       Light/Dark 모두에서 선명하게 보임
       ============================================ */
    .led-indicator {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 10px 18px;
        border-radius: var(--radius-full);
        font-size: 0.85rem;
        font-weight: var(--font-weight-semibold);
        background: var(--glass-overlay);
        border: 1px solid var(--glass-border);
        color: var(--st-text);
        transition: all 0.3s ease;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    
    .led-indicator .led-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        position: relative;
    }
    
    /* 연결됨 - 초록색 LED 글로우 (강화) */
    .led-indicator.connected {
        background: var(--color-success-soft);
        border-color: var(--color-success);
    }
    
    .led-indicator.connected .led-dot {
        background: var(--color-success);
        animation: led-pulse-success 2s ease-in-out infinite;
        box-shadow: 
            0 0 6px var(--color-success),
            0 0 12px var(--color-success),
            0 0 20px rgba(34, 197, 94, 0.5),
            inset 0 0 4px rgba(255, 255, 255, 0.3);
    }
    
    /* 연결 필요 - 노란색 LED 글로우 (강화) */
    .led-indicator.disconnected {
        background: var(--color-warning-soft);
        border-color: var(--color-warning);
    }
    
    .led-indicator.disconnected .led-dot {
        background: var(--color-warning);
        animation: led-pulse-warning 1.5s ease-in-out infinite;
        box-shadow: 
            0 0 6px var(--color-warning),
            0 0 12px var(--color-warning),
            0 0 20px rgba(245, 158, 11, 0.5),
            inset 0 0 4px rgba(255, 255, 255, 0.3);
    }
    
    @keyframes led-pulse-success {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1);
            box-shadow: 
                0 0 6px var(--color-success),
                0 0 12px var(--color-success),
                0 0 20px rgba(34, 197, 94, 0.5);
        }
        50% { 
            opacity: 0.85; 
            transform: scale(0.95);
            box-shadow: 
                0 0 4px var(--color-success),
                0 0 8px var(--color-success),
                0 0 14px rgba(34, 197, 94, 0.3);
        }
    }
    
    @keyframes led-pulse-warning {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1);
            box-shadow: 
                0 0 6px var(--color-warning),
                0 0 12px var(--color-warning),
                0 0 20px rgba(245, 158, 11, 0.5);
        }
        50% { 
            opacity: 0.85; 
            transform: scale(0.95);
            box-shadow: 
                0 0 4px var(--color-warning),
                0 0 8px var(--color-warning),
                0 0 14px rgba(245, 158, 11, 0.3);
        }
    }
    
    /* ============================================
       🔌 SMTP 연결 버튼 (LED 스타일)
       클릭 가능한 상태 인디케이터
       ============================================ */
    
    /* SMTP 연결 필요 버튼 - 경고 LED 스타일 */
    [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:first-of-type,
    .smtp-connect-btn {
        background: var(--color-warning-soft) !important;
        border: 1px solid var(--color-warning) !important;
        color: var(--st-text) !important;
        border-radius: 50px !important;
        padding: 10px 18px !important;
        font-weight: 600 !important;
        position: relative;
        overflow: hidden;
    }
    
    .smtp-connect-btn::before {
        content: '';
        position: absolute;
        left: 16px;
        top: 50%;
        transform: translateY(-50%);
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--color-warning);
        animation: led-pulse-warning 1.5s ease-in-out infinite;
        box-shadow: 
            0 0 6px var(--color-warning),
            0 0 12px var(--color-warning);
    }
    
    .smtp-connect-btn:hover {
        background: rgba(245, 158, 11, 0.2) !important;
        transform: translateY(-2px);
        box-shadow: 
            0 4px 15px rgba(245, 158, 11, 0.3),
            0 0 20px rgba(245, 158, 11, 0.15) !important;
    }
    
    /* ============================================
       📊 메트릭 카드 - Glassmorphism (강화)
       테마 배경색 기반 반투명
       ============================================ */
    [data-testid="stMetric"] {
        background: var(--glass-overlay) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: var(--space-md);
        border-radius: var(--radius-md);
        border: 1px solid var(--glass-border) !important;
        box-shadow: var(--glass-shadow);
        transition: all 0.25s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: var(--glass-hover-shadow);
        border-color: rgba(128, 128, 128, 0.2) !important;
    }
    
    /* 메트릭 값 - 테마 텍스트 색상 상속 + 강조 */
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: var(--font-weight-bold) !important;
        color: var(--st-text) !important;
        line-height: 1.2;
    }
    
    /* 메트릭 레이블 - 명확한 가독성 */
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: var(--font-weight-medium);
        text-transform: uppercase;
        letter-spacing: 0.6px;
        opacity: 0.75;
        color: var(--st-text) !important;
        margin-bottom: 4px;
    }
    
    /* 메트릭 델타 (변화량) */
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
        font-weight: var(--font-weight-medium);
    }
    
    /* ============================================
       🔘 버튼 스타일 (테마 적응형)
       ============================================ */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-weight: var(--font-weight-medium);
        padding: var(--space-sm) var(--space-md);
        transition: all 0.2s ease;
        border: 1px solid var(--glass-border) !important;
        background: var(--glass-overlay) !important;
        color: var(--st-text) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--glass-hover-shadow);
        border-color: var(--st-primary) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Primary 버튼 - 강조 */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--st-primary) !important;
        border-color: var(--st-primary) !important;
        color: white !important;
        font-weight: var(--font-weight-semibold);
    }
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35);
        filter: brightness(1.1);
    }
    
    /* Secondary 버튼 */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--st-primary) !important;
        color: var(--st-primary) !important;
    }
    
    /* ============================================
       📁 파일 업로드 - Drag & Drop (강화)
       ============================================ */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--glass-border) !important;
        border-radius: var(--radius-md);
        padding: var(--space-lg);
        background: var(--glass-overlay);
        transition: all 0.3s ease;
        position: relative;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--st-primary) !important;
        border-style: dashed !important;
        background: var(--color-info-soft);
        box-shadow: 0 0 0 4px var(--color-info-soft);
    }
    
    [data-testid="stFileUploader"]:hover::after {
        content: "📂 파일을 놓으세요";
        position: absolute;
        bottom: 8px;
        right: 12px;
        font-size: 0.75rem;
        color: var(--st-primary);
        opacity: 0.8;
    }
    
    /* 파일 업로드 드래그 오버 상태 */
    [data-testid="stFileUploader"].drag-over {
        border-color: var(--color-success) !important;
        background: var(--color-success-soft);
    }
    
    /* ============================================
       📦 컨테이너/카드
       ============================================ */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--glass-border) !important;
        background: var(--glass-overlay);
        backdrop-filter: blur(8px);
    }
    
    /* ============================================
       ✏️ 입력 필드 스타일
       쿠키 로드 시 테두리 강조 (시각적 세션 표시)
       ============================================ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--glass-border) !important;
        background: var(--st-bg) !important;
        color: var(--st-text) !important;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--st-primary) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
        outline: none !important;
    }
    
    /* 쿠키/Secrets에서 로드된 입력 필드 강조 (녹색 테두리) */
    .input-loaded-from-session input,
    .input-loaded-from-session textarea {
        border-color: var(--color-success) !important;
        border-width: 2px !important;
        box-shadow: 
            0 0 0 3px var(--color-success-soft) !important,
            inset 0 0 0 1px rgba(34, 197, 94, 0.1) !important;
    }
    
    /* 쿠키에서 로드된 입력 필드 라벨 표시 */
    .input-loaded-from-session::before {
        content: "🍪";
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.8rem;
        opacity: 0.7;
    }
    
    /* 비밀번호 필드 특수 스타일 */
    .stTextInput input[type="password"] {
        letter-spacing: 2px;
        font-family: monospace;
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
       📂 Expander
       ============================================ */
    .streamlit-expanderHeader {
        font-weight: 600;
        border-radius: var(--radius-sm);
        background: var(--glass-overlay) !important;
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
       🏷️ 상태 배지 (Status Badge) - 테마 적응형
       ============================================ */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: var(--radius-full);
        font-size: 0.8rem;
        font-weight: var(--font-weight-semibold);
        transition: all 0.2s ease;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }
    
    .status-badge.success {
        background: var(--color-success-soft);
        color: var(--color-success);
        border: 1px solid rgba(34, 197, 94, 0.3);
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
    
    /* 작은 배지 변형 */
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
       🎯 스텝 인디케이터 (강화된 시각적 구분)
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
        position: relative;
    }
    
    .step-circle {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: var(--font-weight-semibold);
        font-size: 0.9rem;
        margin-bottom: var(--space-xs);
        transition: all 0.3s ease;
    }
    
    /* 현재 단계 - Primary 색상 + 강한 글로우 */
    .step-circle.active {
        background: var(--st-primary);
        color: white;
        box-shadow: 
            0 0 0 4px var(--color-info-soft),
            0 4px 12px rgba(59, 130, 246, 0.3);
        transform: scale(1.05);
    }
    
    /* 완료된 단계 - 성공 색상 */
    .step-circle.completed {
        background: var(--color-success);
        color: white;
        box-shadow: 0 2px 8px var(--color-success-soft);
    }
    
    /* 대기 단계 - 연한 배경 + 테두리 */
    .step-circle.pending {
        background: var(--st-secondary-bg);
        color: var(--st-text);
        border: 2px solid var(--glass-border);
        opacity: 0.6;
    }
    
    .step-label {
        font-size: 0.72rem;
        font-weight: var(--font-weight-medium);
        color: var(--st-text);
    }
    
    .step-label.active {
        font-weight: var(--font-weight-semibold);
        color: var(--st-primary);
    }
    
    .step-label.completed {
        color: var(--color-success);
    }
    
    .step-label.pending {
        opacity: 0.6;
    }
    
    .step-line {
        flex: 0.5;
        height: 3px;
        background: var(--glass-border);
        margin-bottom: 22px;
        border-radius: 2px;
        transition: all 0.3s ease;
    }
    
    .step-line.completed {
        background: linear-gradient(90deg, var(--color-success), var(--color-success));
        box-shadow: 0 0 8px var(--color-success-soft);
    }
    
    .step-line.active {
        background: linear-gradient(90deg, var(--color-success), var(--st-primary));
    }
    
    /* ============================================
       🔄 로딩 상태 표시
       ============================================ */
    .loading-shimmer {
        background: linear-gradient(
            90deg,
            var(--glass-overlay) 25%,
            rgba(128, 128, 128, 0.15) 50%,
            var(--glass-overlay) 75%
        );
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
    }
    
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* ============================================
       ✨ 전역 트랜지션 (부드러운 테마 전환)
       ============================================ */
    * {
        transition: background-color 0.15s ease, 
                    border-color 0.15s ease,
                    color 0.15s ease,
                    box-shadow 0.2s ease;
    }
    
    /* 스크롤바 스타일 (테마 적응) */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--glass-overlay);
        border-radius: var(--radius-full);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--glass-border);
        border-radius: var(--radius-full);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--st-primary);
    }
    
    /* ============================================
       🎭 포커스 가시성 (접근성)
       ============================================ */
    *:focus-visible {
        outline: 2px solid var(--st-primary);
        outline-offset: 2px;
    }
    
    /* ============================================
       📱 컨테이너/카드 추가 스타일
       ============================================ */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: var(--radius-md) !important;
    }
    
    /* 테마 적응형 카드 배경 */
    .main [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: var(--glass-overlay);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-md);
    }
    
    /* ============================================
       🔄 로딩/스피너 스타일
       ============================================ */
    .stSpinner > div {
        border-top-color: var(--st-primary) !important;
    }
    
    /* ============================================
       📊 탭 패널 내부 여백
       ============================================ */
    [data-testid="stTabs"] [data-testid="stVerticalBlock"] {
        padding-top: var(--space-md);
    }
    
    /* ============================================
       🔧 사이드바 버튼 - 모던 Full Width 디자인
       ============================================ */
    
    /* 사이드바 전체 레이아웃 - Flexbox Column */
    [data-testid="stSidebar"] > div:first-child {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        padding: 16px 12px !important;
    }
    
    /* 사이드바 내 모든 버튼 컨테이너 - Full Width 보장 */
    [data-testid="stSidebar"] .stButton {
        width: 100% !important;
        margin: 0 !important;
    }
    
    /* 사이드바 버튼 공통 스타일 - 100% Width, 테두리 없음, 여백으로 구분 */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        min-height: 40px !important;
        padding: 10px 16px !important;
        margin-bottom: 4px !important;
        
        /* 테두리 없음 - 면(Space)으로 구분 */
        border: none !important;
        border-radius: var(--radius-md) !important;
        
        /* 배경 연하게 */
        background: rgba(128, 128, 128, 0.06) !important;
        
        /* 텍스트 정렬 - 좌측 시작 */
        text-align: left !important;
        justify-content: flex-start !important;
        
        /* 폰트 */
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: var(--st-text) !important;
        
        /* 부드러운 전환 */
        transition: all 0.2s ease !important;
    }
    
    /* 사이드바 버튼 호버 효과 */
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(128, 128, 128, 0.12) !important;
        transform: translateX(4px) !important;
        box-shadow: none !important;
    }
    
    /* 사이드바 Primary 버튼 (활성 상태) */
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
        background: var(--color-info-soft) !important;
        color: var(--st-primary) !important;
        font-weight: 600 !important;
        border-left: 3px solid var(--st-primary) !important;
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    [data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"]:hover {
        background: rgba(59, 130, 246, 0.2) !important;
    }
    
    /* 사이드바 네비게이션 버튼 (이전/다음) - 컴팩트 */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {
        min-height: 32px !important;
        padding: 6px 12px !important;
        font-size: 0.75rem !important;
        text-align: center !important;
        justify-content: center !important;
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button:hover {
        background: rgba(128, 128, 128, 0.08) !important;
        transform: none !important;
    }
    
    /* 사이드바 내 가로 블록(columns) 정렬 */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 8px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="column"] {
        padding: 0 !important;
    }
    
    /* 사이드바 세로 블록 여백 통일 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 4px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        margin-bottom: 0 !important;
    }
    
    /* Expander 내부 버튼 - 약간 작게 */
    [data-testid="stSidebar"] [data-testid="stExpander"] .stButton > button {
        min-height: 36px !important;
        padding: 8px 14px !important;
        font-size: 0.8rem !important;
        margin-bottom: 6px !important;
    }
    
    /* 사이드바 Divider 숨기기 (선 대신 여백) */
    [data-testid="stSidebar"] hr {
        display: none !important;
    }
    
    /* LED 인디케이터 마진 조정 */
    [data-testid="stSidebar"] .led-indicator {
        margin: 8px 0 !important;
    }
    
    /* Expander 헤더 스타일 */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        border-radius: var(--radius-sm) !important;
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] .streamlit-expanderHeader:hover {
        background: rgba(128, 128, 128, 0.06) !important;
    }
    
    /* Link Button 스타일 통일 */
    [data-testid="stSidebar"] .stLinkButton > a {
        width: 100% !important;
        min-height: 36px !important;
        padding: 8px 14px !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        background: rgba(128, 128, 128, 0.06) !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.8rem !important;
        color: var(--st-text) !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stSidebar"] .stLinkButton > a:hover {
        background: rgba(128, 128, 128, 0.12) !important;
        transform: translateX(4px) !important;
    }
    
    /* LED 인디케이터와 Expander 사이 간격 */
    [data-testid="stSidebar"] .led-indicator {
        margin: 16px 0 !important;
    }
    
    /* Expander 간 간격 통일 */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        margin-bottom: 8px !important;
    }
    
    /* 사이드바 푸터 스타일 */
    .sidebar-footer {
        text-align: center;
        padding: 16px 0;
        margin-top: auto;
        font-size: 0.7rem;
        opacity: 0.6;
        border-top: 1px solid rgba(128, 128, 128, 0.15);
        color: var(--st-text);
    }
    
    /* ============================================
       🎯 드래그 앤 드롭 컬럼 칩 - 레이아웃 안정화
       클릭/드래그 시 크기 변화 완전 방지
       ============================================ */
    
    /* sortable 컨테이너 고정 높이 */
    .sortable-container {
        min-height: 120px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 12px;
        border-radius: var(--radius-md);
        background: var(--glass-overlay);
        border: 2px dashed var(--glass-border);
        transition: background 0.2s ease, border-color 0.2s ease;
    }
    
    .sortable-container:hover {
        border-color: var(--st-primary);
        background: rgba(59, 130, 246, 0.05);
    }
    
    /* 컬럼 칩 - box-sizing으로 크기 고정 */
    .column-chip {
        box-sizing: border-box !important;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 12px;
        height: 36px;  /* 고정 높이 */
        min-width: 80px;
        font-size: 0.85rem;
        font-weight: var(--font-weight-medium);
        background: var(--st-secondary-bg);
        border: 2px solid transparent;  /* 초기부터 테두리 공간 확보 */
        border-radius: var(--radius-full);
        cursor: grab;
        transition: box-shadow 0.15s ease, background 0.15s ease;
        user-select: none;
    }
    
    /* 호버 - 테두리 대신 그림자 사용 */
    .column-chip:hover {
        box-shadow: 0 0 0 3px var(--color-info-soft), var(--glass-shadow);
        background: var(--glass-overlay);
    }
    
    /* 활성/드래그 중 - 테두리 대신 내부 그림자 */
    .column-chip:active,
    .column-chip.dragging {
        cursor: grabbing;
        box-shadow: 0 0 0 3px var(--color-info), 0 4px 12px rgba(0,0,0,0.15);
        background: var(--color-info-soft);
    }
    
    /* 삭제 버튼 - 고정 크기 */
    .column-chip .remove-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        font-size: 12px;
        border-radius: 50%;
        background: rgba(239, 68, 68, 0.1);
        color: var(--color-error);
        border: none;
        cursor: pointer;
        transition: background 0.15s ease;
        flex-shrink: 0;  /* 축소 방지 */
    }
    
    .column-chip .remove-btn:hover {
        background: var(--color-error);
        color: white;
    }
    
    /* 형식 타입별 칩 색상 */
    .chip-amount {
        border-left: 3px solid #f59e0b !important;
    }
    
    .chip-percent {
        border-left: 3px solid #8b5cf6 !important;
    }
    
    .chip-date {
        border-left: 3px solid #22c55e !important;
    }
    
    .chip-id {
        border-left: 3px solid #3b82f6 !important;
    }
    
    /* 영역 헤더 스타일 */
    .area-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border-radius: var(--radius-md);
        margin-bottom: 8px;
        font-weight: var(--font-weight-semibold);
    }
    
    .area-header.display-area {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #1976d2;
        color: #1565c0;
    }
    
    .area-header.format-area {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-left: 4px solid #f57c00;
        color: #e65100;
    }
    
    /* ============================================
       🎯 Drag & Drop 칩 레이아웃 안정화
       - box-sizing: border-box 전역 적용
       - 고정 높이/패딩으로 출렁임 방지
       - box-shadow로 활성 상태 표시 (테두리 두께 변화 없음)
       ============================================ */
    
    /* streamlit-sortables 전역 컨테이너 안정화 */
    .element-container:has(.sortable-container) {
        min-height: 60px !important;
    }
    
    /* sortable 컨테이너 자체 */
    .sortable-container {
        min-height: 50px !important;
        padding: 8px !important;
        box-sizing: border-box !important;
    }
    
    /* 모든 sortable 아이템(칩) 안정화 */
    [data-testid="stVerticalBlock"] .sortable-item,
    .sortable-item {
        box-sizing: border-box !important;
        margin: 4px !important;
        padding: 8px 14px !important;
        min-height: 36px !important;
        max-height: 36px !important;
        height: 36px !important;
        line-height: 18px !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        /* 테두리는 항상 동일한 두께 유지 */
        border: 2px solid transparent !important;
        /* 활성 상태는 box-shadow로만 표시 */
        transition: box-shadow 0.15s ease, background-color 0.15s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        white-space: nowrap !important;
        cursor: grab !important;
        user-select: none !important;
    }
    
    /* 호버 상태 - 테두리 두께 변화 없음, 그림자로만 표시 */
    [data-testid="stVerticalBlock"] .sortable-item:hover,
    .sortable-item:hover {
        border: 2px solid transparent !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25), 0 2px 8px rgba(0,0,0,0.1) !important;
        background-color: rgba(59, 130, 246, 0.08) !important;
    }
    
    /* 드래그 중 상태 - 테두리 두께 변화 없음, 강한 그림자 */
    [data-testid="stVerticalBlock"] .sortable-item:active,
    [data-testid="stVerticalBlock"] .sortable-item.dragging,
    .sortable-item:active,
    .sortable-item.dragging {
        border: 2px solid transparent !important;
        box-shadow: 0 0 0 3px #3b82f6, 0 8px 20px rgba(0,0,0,0.2) !important;
        cursor: grabbing !important;
        transform: scale(1.02) !important;
    }
    
    /* 포커스 상태 (키보드 접근성) */
    [data-testid="stVerticalBlock"] .sortable-item:focus,
    .sortable-item:focus {
        border: 2px solid transparent !important;
        box-shadow: 0 0 0 3px #3b82f6, 0 0 0 5px rgba(59, 130, 246, 0.2) !important;
        outline: none !important;
    }
    
    /* 드래그 앤 드롭 컨테이너 영역 */
    .dnd-container {
        background: var(--st-secondary-bg, #f8f9fa);
        border: 2px dashed var(--glass-border, rgba(128, 128, 128, 0.2));
        border-radius: var(--radius-md, 12px);
        padding: 12px;
        min-height: 60px;
        box-sizing: border-box;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }
    
    .dnd-container:hover {
        border-color: rgba(59, 130, 246, 0.4);
        background: rgba(59, 130, 246, 0.02);
    }
    
    .dnd-container.drop-active {
        border-color: #3b82f6;
        background: rgba(59, 130, 246, 0.05);
    }
    
    /* 컬럼 타입별 칩 배경색 (sortable 내부) */
    .sortable-item[data-type="amount"] {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
        border-left: 3px solid #f59e0b !important;
    }
    
    .sortable-item[data-type="percent"] {
        background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%) !important;
        border-left: 3px solid #8b5cf6 !important;
    }
    
    .sortable-item[data-type="date"] {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%) !important;
        border-left: 3px solid #22c55e !important;
    }
    
    .sortable-item[data-type="id"] {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
        border-left: 3px solid #3b82f6 !important;
    }
    
</style>
"""


# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def init_session_state():
    """
    세션 상태 초기화
    기본값은 constants.py의 SESSION_STATE_DEFAULTS에서 중앙 관리됩니다.
    """
    # SESSION_STATE_DEFAULTS를 기반으로 초기화
    for key, value in SESSION_STATE_DEFAULTS.items():
        if key not in st.session_state:
            # set 타입은 복사해서 사용 (참조 문제 방지)
            if isinstance(value, (set, list, dict)):
                st.session_state[key] = value.copy() if hasattr(value, 'copy') else value
            else:
                st.session_state[key] = value


def reset_and_restart():
    """세션 초기화 후 Step 1로 이동"""
    # 보존할 설정 (SMTP 등)
    smtp_config = st.session_state.get('smtp_config')
    
    # 모든 세션 상태 초기화
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # 기본값 다시 설정
    for key, value in SESSION_STATE_DEFAULTS.items():
        if isinstance(value, (set, list, dict)):
            st.session_state[key] = value.copy() if hasattr(value, 'copy') else value
        else:
            st.session_state[key] = value
    
    # SMTP 설정 복원
    if smtp_config:
        st.session_state.smtp_config = smtp_config
    
    st.session_state.current_step = 1
    st.rerun()


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


# ============================================================================
# 컬럼 설정 JSON 파일 관리 (Drag & Drop 설정 영속성)
# ============================================================================
# CONFIG_COLUMNS_PATH는 constants.py에서 import됨


def load_column_config_from_json() -> dict:
    """JSON 파일에서 컬럼 설정 로드"""
    try:
        if os.path.exists(CONFIG_COLUMNS_PATH):
            with open(CONFIG_COLUMNS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"설정 파일 로드 오류: {e}")
    return {}


def save_column_config_to_json(config: dict):
    """JSON 파일에 컬럼 설정 저장"""
    try:
        with open(CONFIG_COLUMNS_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"설정 파일 저장 오류: {e}")


def apply_saved_config_to_columns(saved_config: dict, available_columns: list) -> Tuple[dict, list]:
    """
    저장된 설정을 현재 엑셀 컬럼에 적용
    존재하지 않는 컬럼은 제외하고 알림 목록 반환
    """
    result = {
        'display_cols': [],
        'amount_cols': [],
        'percent_cols': [],
        'date_cols': [],
        'id_cols': [],
        'available': []  # 아직 배치되지 않은 컬럼
    }
    missing_cols = []
    
    # 각 카테고리에서 존재하는 컬럼만 유지
    for key in ['display_cols', 'amount_cols', 'percent_cols', 'date_cols', 'id_cols']:
        saved_list = saved_config.get(key, [])
        for col in saved_list:
            if col in available_columns:
                result[key].append(col)
            else:
                if col not in missing_cols:
                    missing_cols.append(col)
    
    # 배치된 컬럼 목록
    placed_cols = set()
    for key in ['display_cols', 'amount_cols', 'percent_cols', 'date_cols', 'id_cols']:
        placed_cols.update(result[key])
    
    # 아직 배치되지 않은 컬럼
    result['available'] = [c for c in available_columns if c not in placed_cols]
    
    return result, missing_cols


def move_step(target_step: int, save_config: bool = True):
    """
    공통 스텝 이동 함수 - 본문/사이드바 버튼 모두 이 함수 사용
    
    Args:
        target_step: 이동할 스텝 번호 (1-5)
        save_config: 미사용 (하위 호환용)
    """
    current_step = st.session_state.get('current_step', 1)
    
    # 스텝 이동
    st.session_state.current_step = target_step
    add_log(f"Step {current_step} → Step {target_step} 이동")
    st.rerun()


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
    """시트 로드 - 항상 (DataFrame, error_message) 튜플 반환
    
    엑셀 원본 형식 유지:
    - 숫자에 콤마 있으면 콤마 포함 문자열로 보존
    - 바코드/코드는 숫자 그대로 유지
    """
    try:
        # 먼저 문자열로 읽어서 원본 형식 보존
        df_str = pd.read_excel(xlsx, sheet_name=sheet_name, dtype=str)
        # 일반 파싱도 수행 (숫자 계산용)
        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        
        if df.empty:
            return None, "시트에 데이터가 없습니다."
        
        # 원본 문자열 데이터 저장 (컬럼별 원본 형식 확인용)
        df.attrs['original_str'] = df_str
        
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
    """데이터 정리 - 엑셀 원본 유지, 숫자 컬럼만 numeric 변환"""
    df_cleaned = df.copy()
    
    # 숫자 컬럼만 numeric 변환 (합계 계산을 위해)
    # 나머지는 엑셀 원본 그대로 유지
    for col in amount_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(
                df_cleaned[col].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', '').str.strip(),
                errors='coerce'
            )
    for col in percent_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(
                df_cleaned[col].astype(str).str.replace(',', '').str.replace('%', '').str.strip(),
                errors='coerce'
            )
    
    # id_cols, date_cols는 원본 그대로 유지 (형식 변환 안 함)
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
        
        # ============================================================
        # 엑셀 원본 형식 완전 유지 + NaN/0만 빈칸 처리
        # - 엑셀에서 콤마 있으면 콤마 그대로
        # - 바코드/코드 등 콤마 없는 숫자는 그대로
        # ============================================================
        # 원본 문자열 데이터 가져오기
        original_str_df = df.attrs.get('original_str', None)
        
        rows = []
        for idx, row in group_df.iterrows():
            row_dict = {}
            for col in display_cols:
                if col in row.index:
                    value = row[col]
                    
                    # NaN 체크
                    if pd.isna(value) or value is None:
                        row_dict[col] = ''
                        continue
                    
                    # 원본 문자열 확인
                    orig_str = None
                    if original_str_df is not None and col in original_str_df.columns:
                        try:
                            orig_val = original_str_df.loc[idx, col]
                            if pd.notna(orig_val):
                                orig_str = str(orig_val).strip()
                        except:
                            pass
                    
                    # 숫자 0 체크 (빈칸 처리)
                    if isinstance(value, (int, float)) and value == 0:
                        row_dict[col] = ''
                        continue
                    
                    # 원본 문자열이 있으면 그대로 사용 (NaN/0 제외)
                    if orig_str:
                        # 원본이 '0' 또는 빈값이면 빈칸
                        if orig_str.lower() in ['nan', 'none', 'nat', '', '0', '0.0', '0.00']:
                            row_dict[col] = ''
                        else:
                            row_dict[col] = orig_str
                        continue
                    
                    # 원본 없으면 값 그대로 변환 (콤마 없이)
                    if isinstance(value, (int, float)):
                        if isinstance(value, float) and value == int(value):
                            row_dict[col] = str(int(value))
                        else:
                            row_dict[col] = str(value)
                    else:
                        str_val = str(value).strip()
                        if str_val.lower() in ['nan', 'none', 'nat', '', '0', '0.0']:
                            row_dict[col] = ''
                        else:
                            row_dict[col] = str_val
                else:
                    row_dict[col] = ''
            rows.append(row_dict)
        
        totals = {}
        if calculate_totals:
            # 합계 자동 계산이 활성화된 경우에만 totals 생성
            if use_wildcard:
                # 와일드카드 사용 시: 합계 행을 제외한 데이터만 합산
                non_total_mask = ~group_df[group_key_col].apply(
                    lambda x: any(str(x).endswith(s) for s in wildcard_suffixes))
                non_total_df = group_df[non_total_mask]
                for col in amount_cols:
                    if col in non_total_df.columns:
                        total_val = non_total_df[col].sum()
                        totals[col] = f"{total_val:,.0f}" if total_val != 0 else ''
            else:
                # 와일드카드 미사용 시: 전체 데이터 합산
                for col in amount_cols:
                    if col in group_df.columns:
                        total_val = group_df[col].sum()
                        totals[col] = f"{total_val:,.0f}" if total_val != 0 else ''
        # calculate_totals가 False이면 totals는 빈 딕셔너리 유지 (합계 행 표시 안함)
        
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


# render_email_content는 email_template.py에서 import됨
# 단일 소스 원칙 (Single Source of Truth) 적용


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
                        move_step(i)
    
    st.divider()


def get_cookie_manager():
    """쿠키 매니저 - 세션별 싱글톤 (캐싱 경고 해결)"""
    if 'cookie_manager' not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="smtp_cookie_manager")
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


def render_auto_login_guide_dialog():
    """자동로그인 설정 가이드 다이얼로그"""
    
    @st.dialog("🔐 자동로그인 설정", width="large")
    def show_auto_login_guide():
        st.markdown("""
        <style>
        .config-box {
            background: rgba(74, 158, 255, 0.1);
            border-left: 4px solid #4a9eff;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        .config-code {
            background: rgba(0,0,0,0.3);
            padding: 0.8rem 1rem;
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            margin: 0.5rem 0;
        }
        .config-note {
            background: rgba(255, 193, 7, 0.15);
            border-left: 4px solid #ffc107;
            padding: 0.8rem 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 자동로그인이란?")
        st.info("앱 실행 시 SMTP 계정 정보를 자동으로 불러와서 매번 입력할 필요가 없습니다.", icon="💡")
        
        st.markdown("---")
        st.markdown("### 📁 secrets.toml 파일 설정")
        
        # 파일 위치
        st.markdown('<div class="config-box"><strong>파일 위치:</strong> <code>.streamlit/secrets.toml</code></div>', unsafe_allow_html=True)
        st.caption("프로젝트 폴더 안에 `.streamlit` 폴더를 만들고 그 안에 `secrets.toml` 파일 생성")
        
        # 설정 내용
        st.markdown("### ✏️ 파일 내용")
        st.code('''# SMTP 자동로그인 설정
SMTP_ID = "your_email@company.com"
SMTP_PW = "your_app_password"
SMTP_PROVIDER = "Hiworks (하이웍스)"
SENDER_NAME = "한국유니온제약"''', language="toml")
        
        # 설정 항목 설명
        with st.expander("📋 설정 항목 설명"):
            st.markdown("""
| 항목 | 설명 | 예시 |
|------|------|------|
| `SMTP_ID` | 이메일 계정 | `sales@company.com` |
| `SMTP_PW` | 앱 비밀번호 | 이메일 서비스에서 발급 |
| `SMTP_PROVIDER` | 메일 서비스 | `Hiworks (하이웍스)`, `Gmail` 등 |
| `SENDER_NAME` | 발신자 표시명 | `한국유니온제약` |
            """)
        
        st.markdown("---")
        st.markdown("### 🔄 로드 우선순위")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**1순위**")
            st.markdown("🍪 브라우저 쿠키")
            st.caption("90일간 유지")
        with col2:
            st.markdown("**2순위**")
            st.markdown("🔐 secrets.toml")
            st.caption("파일 설정")
        with col3:
            st.markdown("**3순위**")
            st.markdown("✏️ 수동 입력")
            st.caption("직접 입력")
        
        st.markdown("---")
        st.markdown('<div class="config-note">⚠️ <strong>주의:</strong> secrets.toml 파일은 절대 GitHub에 업로드하지 마세요! (.gitignore에 추가)</div>', unsafe_allow_html=True)
        
        if st.button("닫기", width='stretch', type="primary"):
            st.rerun()
    
    return show_auto_login_guide


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
            st.link_button("📦 ZIP 다운로드", "https://github.com/yurielk82/mm-project/archive/refs/heads/main.zip", width='stretch')
        with col2:
            st.link_button("🔗 GitHub 열기", "https://github.com/yurielk82/mm-project", width='stretch')
        
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
        
        if st.button("닫기", width='stretch', type="primary"):
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
    padding: 0;
    margin-bottom: 4px;
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
    margin-top: 4px;
    margin-bottom: 0;
}}
.progress-step-name {{
    font-size: 0.95rem;
    font-weight: 600;
    color: #00d4ff;
}}
.progress-status {{
    font-size: 0.7rem;
    color: rgba(128,128,128,0.7);
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


def can_go_next_step(current_step: int) -> Tuple[bool, str]:
    """다음 단계로 이동 가능한지 검증하고 사유 반환"""
    
    if current_step == 1:
        # Step 1: 파일 업로드 완료 여부
        if st.session_state.df is None:
            return False, "먼저 파일을 업로드하세요"
        return True, ""
    
    elif current_step == 2:
        # Step 2: 표시 컬럼 선택 여부
        display_cols = st.session_state.get('display_cols', [])
        if not display_cols:
            return False, "표시할 컬럼을 1개 이상 선택하세요"
        return True, ""
    
    elif current_step == 3:
        # Step 3: 유효한 발송 대상 여부
        grouped = st.session_state.get('grouped_data', {})
        valid = sum(1 for g in grouped.values() if g.get('recipient_email') and validate_email(g.get('recipient_email', '')))
        if valid == 0:
            return False, "발송 가능한 대상이 없습니다"
        return True, ""
    
    elif current_step == 4:
        # Step 4: 항상 이동 가능
        return True, ""
    
    return False, "마지막 단계입니다"


def execute_step_transition(current_step: int, direction: str = "next") -> bool:
    """스텝 전환 시 필요한 로직 실행 (본문 버튼과 동일한 로직)
    
    Args:
        current_step: 현재 스텝 번호
        direction: "next" 또는 "prev"
    
    Returns:
        True if transition successful, False otherwise
    """
    
    if direction == "prev":
        # 이전 단계는 단순 이동
        if current_step > 1:
            st.session_state.current_step = current_step - 1
            return True
        return False
    
    # 다음 단계 로직
    can_go, error_msg = can_go_next_step(current_step)
    if not can_go:
        st.toast(error_msg, icon="⚠️")
        return False
    
    if current_step == 1:
        # Step 1 → 2: 단순 이동 (데이터는 이미 로드됨)
        st.session_state.current_step = 2
        return True
    
    elif current_step == 2:
        # Step 2 → 3: 데이터 처리 로직 실행
        df = st.session_state.df
        df_email = st.session_state.df_email
        use_separate = st.session_state.use_separate_email_sheet
        
        # 설정값 가져오기
        sheet_name = st.session_state.get('selected_data_sheet', 'default')
        group_key_col = st.session_state.get('group_key_col')
        display_cols = st.session_state.get('display_cols', [])
        amount_cols = st.session_state.get('amount_cols', [])
        percent_cols = st.session_state.get('percent_cols', [])
        date_cols = st.session_state.get('date_cols', [])
        id_cols = st.session_state.get('id_cols', [])
        use_wildcard = st.session_state.get('use_wildcard_grouping', True)
        conflict_resolution = st.session_state.get('conflict_resolution', 'first')
        
        if not group_key_col:
            st.toast("그룹화 기준 컬럼을 선택하세요", icon="⚠️")
            return False
        
        # 컬럼 설정 저장
        save_column_settings(sheet_name)
        
        # 데이터 처리
        df_work = df.copy()
        
        if use_separate and df_email is not None:
            df_work = merge_email_data(
                df_work, df_email,
                st.session_state.get('join_col_data'),
                st.session_state.get('join_col_email'),
                st.session_state.get('email_col')
            )
        
        df_cleaned = clean_dataframe(df_work, amount_cols, percent_cols, date_cols, id_cols)
        st.session_state.df = df_cleaned
        
        grouped, conflicts = group_data_with_wildcard(
            df_cleaned, group_key_col, st.session_state.get('email_col'),
            amount_cols, percent_cols, display_cols, conflict_resolution,
            use_wildcard, st.session_state.get('wildcard_suffixes', [' 합계']),
            st.session_state.get('calculate_totals_auto', False)
        )
        
        st.session_state.grouped_data = grouped
        st.session_state.email_conflicts = conflicts
        st.session_state.current_step = 3
        return True
    
    elif current_step == 3:
        # Step 3 → 4: 단순 이동
        st.session_state.current_step = 4
        return True
    
    elif current_step == 4:
        # Step 4 → 5: 단순 이동
        st.session_state.current_step = 5
        return True
    
    return False


def render_step_nav_buttons(current_step: int, total_steps: int):
    """이전단계/다음단계 텍스트 버튼 (본문 버튼과 동일한 로직 실행)"""
    prev_disabled = current_step <= 1
    next_disabled = current_step >= total_steps
    
    # 버튼 2개를 바로 columns로 배치
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("‹ 이전", key="nav_prev", disabled=prev_disabled, width='stretch'):
            if execute_step_transition(current_step, "prev"):
                st.rerun()
    
    with col2:
        if st.button("다음 ›", key="nav_next", disabled=next_disabled, width='stretch'):
            if execute_step_transition(current_step, "next"):
                st.rerun()


def render_smtp_sidebar():
    """사이드바 - Theme-Adaptive & Responsive UI"""
    with st.sidebar:
        
        # ============================================================
        # 🎨 사이드바 레이아웃 안정화 CSS
        # - 메뉴 간 일정한 간격 (gap)
        # - 호버 시 크기 흔들림 방지
        # ============================================================
        st.markdown("""
        <style>
            /* 사이드바 전체 레이아웃 */
            [data-testid="stSidebar"] > div:first-child {
                padding-top: 1rem;
            }
            
            /* 사이드바 버튼 안정화 - 호버/클릭 시 크기 고정 */
            [data-testid="stSidebar"] button {
                box-sizing: border-box !important;
                min-height: 38px !important;
                padding: 8px 16px !important;
                margin: 4px 0 !important;
                border: 2px solid transparent !important;
                transition: background-color 0.15s ease, box-shadow 0.15s ease !important;
            }
            
            [data-testid="stSidebar"] button:hover {
                border: 2px solid transparent !important;
                box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
            }
            
            [data-testid="stSidebar"] button:active {
                border: 2px solid transparent !important;
                transform: none !important;
            }
            
            /* Expander 내부 버튼들 간격 통일 */
            [data-testid="stSidebar"] [data-testid="stExpander"] > div > div {
                display: flex;
                flex-direction: column;
                gap: 6px !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # ============================================================
        # 🔝 원형 프로그레스 인디케이터 (메일 발송 페이지에서만 표시)
        # ============================================================
        current_page = st.session_state.get('current_page', '📧 메일 발송')
        
        if current_page == "📧 메일 발송":
            current_step = st.session_state.current_step
            total_steps = len(STEPS)
            
            # 원형 프로그레스 바 (원래 크기)
            st.markdown(render_circular_progress(current_step, total_steps), unsafe_allow_html=True)
            
            # 이전단계/다음단계 텍스트 버튼
            render_step_nav_buttons(current_step, total_steps)
        
        # ============================================================
        # SMTP 상태 LED 인디케이터
        # ============================================================
        if st.session_state.smtp_config:
            st.markdown("""<div class="led-indicator connected" style="width:100%; justify-content:center; margin:16px 0 0 0;">
                <span class="led-dot"></span><span>SMTP 연결됨</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="led-indicator disconnected" style="width:100%; justify-content:center; margin:16px 0 0 0;">
                <span class="led-dot"></span><span>SMTP 연결 필요</span>
            </div>""", unsafe_allow_html=True)
        
        # LED와 SMTP 설정 사이 간격 (메뉴 간격과 동일)
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        # ============================================================
        # SMTP 계정 설정
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
            if st.button("🔌 연결 테스트", width='stretch', type="primary"):
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
        
        # 메뉴 간 간격
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        # ============================================================
        # 메뉴 (페이지 네비게이션)
        # ============================================================
        current_page = st.session_state.get('current_page', '📧 메일 발송')
        
        with st.expander("📋 메뉴", expanded=False):
            if st.button("📧 메일 발송", width='stretch', 
                        type="primary" if current_page == "📧 메일 발송" else "secondary",
                        key="goto_mail"):
                st.session_state.current_page = '📧 메일 발송'
                st.rerun()
            
            if st.button("📜 발송 이력", width='stretch',
                        type="primary" if current_page == "📜 발송 이력" else "secondary",
                        key="goto_history"):
                st.session_state.current_page = '📜 발송 이력'
                st.rerun()
        
        # 메뉴 간 간격
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        # ============================================================
        # 가이드 (모든 가이드를 팝업으로)
        # ============================================================
        with st.expander("📖 가이드", expanded=False):
            st.link_button("📦 로컬 실행 파일 다운", 
                          "https://github.com/yurielk82/mm-project/archive/refs/heads/main.zip",
                          width='stretch')
            
            if st.button("💻 로컬 실행 가이드", width='stretch', key="local_guide_btn"):
                st.session_state.show_local_guide = True
                st.rerun()
            
            if st.button("🔐 자동로그인 설정", width='stretch', key="auto_login_guide_btn"):
                st.session_state.show_auto_login_guide = True
                st.rerun()
        
        # 푸터 전 여백
        st.markdown("<div style='flex-grow: 1; min-height: 20px;'></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="sidebar-footer">
            <strong>Designed by Kwon Dae-hwan</strong><br>
            © 2026 KUP Sales Management
        </div>
        """, unsafe_allow_html=True)





def render_page_header(step: int, title: str, description: str):
    """SaaS급 페이지 헤더 - Light/Dark 모드 적응형"""
    
    # 페이지 전환 시 자동 스크롤 최상단 (JavaScript 실행)
    import streamlit.components.v1 as components
    components.html("""
        <script>
            // 부모 프레임(Streamlit)의 main 영역을 최상단으로 스크롤
            window.parent.document.querySelector('section.main').scrollTo({top: 0, behavior: 'instant'});
        </script>
    """, height=0)
    
    # Light/Dark 테마 적응형 헤더 (CSS 변수 사용)
    st.markdown(f"""
    <style>
        .page-header {{
            background: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.15);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }}
        .page-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color) 0%, #7c3aed 100%);
        }}
        .page-header .decorative-circle {{
            position: absolute;
            top: -20px;
            right: -20px;
            width: 120px;
            height: 120px;
            background: rgba(128, 128, 128, 0.06);
            border-radius: 50%;
        }}
        .page-header .step-info {{
            font-size: 0.8rem;
            color: var(--primary-color);
            font-weight: 600;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }}
        .page-header .title {{
            margin: 0;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-color);
        }}
        .page-header .description {{
            margin: 8px 0 0 0;
            font-size: 0.9rem;
            color: var(--text-color);
            opacity: 0.7;
        }}
        .page-header .step-badge {{
            background: rgba(128, 128, 128, 0.1);
            border: 1px solid rgba(128, 128, 128, 0.15);
            border-radius: 12px;
            padding: 12px 20px;
            text-align: center;
        }}
        .page-header .step-number {{
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
            color: var(--primary-color);
        }}
        .page-header .step-total {{
            font-size: 0.7rem;
            color: var(--text-color);
            opacity: 0.6;
        }}
    </style>
    <div class="page-header">
        <div class="decorative-circle"></div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="step-info">STEP {step} / {len(STEPS)}</div>
                <h2 class="title">{title}</h2>
                <p class="description">{description}</p>
            </div>
            <div class="step-badge">
                <div class="step-number">{step}</div>
                <div class="step-total">of {len(STEPS)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_step1():
    """Step 1: 파일 업로드"""
    
    # 페이지 헤더
    render_page_header(1, "파일 업로드", "정산 데이터가 포함된 엑셀 파일을 업로드하세요")
    
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
            """데이터 분석 및 통계 계산
            
            발송 가능 계산: 전체 업체 - 이메일 없음 - 데이터 없음
            """
            stats = {
                'total_rows': 0,
                'total_groups': 0,
                'has_email': 0,
                'no_email': 0,
                'no_data': 0,  # 필수 데이터 없는 그룹
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
            
            # 금액 컬럼 탐지 (필수 데이터 체크용)
            amount_col_candidates = [c for c in df_data.columns 
                                     if '수수료' in c or '금액' in c or '합계' in c]
            
            # 이메일 컬럼 탐지
            email_cols = [c for c in df_data.columns if '이메일' in c or 'mail' in c.lower() or 'email' in c.lower()]
            email_col_in_data = email_cols[0] if email_cols else None
            
            # 별도 이메일 시트 처리
            email_lookup = {}
            if use_separate and df_email is not None:
                # 별도 이메일 시트에서 그룹별 이메일 매핑
                email_col_candidates = [c for c in df_email.columns if '이메일' in c or 'mail' in c.lower()]
                group_col_candidates = [c for c in df_email.columns if 'CSO' in c or '관리업체' in c or '업체' in c]
                
                if email_col_candidates and group_col_candidates:
                    e_col = email_col_candidates[0]
                    g_col = group_col_candidates[0]
                    for _, row in df_email.iterrows():
                        key = str(row.get(g_col, '')).strip()
                        email_val = row.get(e_col)
                        if key and pd.notna(email_val) and str(email_val).strip():
                            email_lookup[key] = str(email_val).strip()
            
            # 그룹별 분석
            for g in unique_groups:
                group_data = df_data[df_data[group_col] == g]
                
                # 1. 이메일 보유 여부 체크
                has_email_for_group = False
                
                if use_separate and df_email is not None:
                    # 별도 시트에서 이메일 확인
                    if str(g) in email_lookup:
                        has_email_for_group = True
                elif email_col_in_data:
                    # 같은 시트에서 이메일 확인
                    if group_data[email_col_in_data].notna().any():
                        email_vals = group_data[email_col_in_data].dropna()
                        if len(email_vals) > 0 and any(str(v).strip() for v in email_vals):
                            has_email_for_group = True
                
                # 2. 필수 데이터 보유 여부 체크 (금액 컬럼에 값이 있는지)
                has_required_data = True
                if amount_col_candidates:
                    # 합계 행 제외한 실제 데이터 행만 확인
                    data_rows = group_data[~group_data[group_col].astype(str).str.endswith(' 합계')]
                    if len(data_rows) == 0:
                        has_required_data = False
                    else:
                        # 금액 컬럼 중 하나라도 유효한 값이 있는지
                        has_any_amount = False
                        for amt_col in amount_col_candidates:
                            if amt_col in data_rows.columns:
                                vals = data_rows[amt_col].dropna()
                                if len(vals) > 0:
                                    # 0이 아닌 값이 있는지 확인
                                    numeric_vals = pd.to_numeric(vals, errors='coerce').dropna()
                                    if len(numeric_vals) > 0 and numeric_vals.sum() != 0:
                                        has_any_amount = True
                                        break
                        if not has_any_amount:
                            has_required_data = False
                
                # 3. 통계 업데이트
                if has_email_for_group:
                    stats['has_email'] += 1
                else:
                    stats['no_email'] += 1
                
                if not has_required_data:
                    stats['no_data'] += 1
            
            # 발송 가능 = 전체 업체 - 이메일 없음 - 데이터 없음
            # 단, 이메일과 데이터가 모두 없는 그룹은 중복 카운트 방지
            stats['valid_for_send'] = stats['total_groups'] - stats['no_email'] - stats['no_data']
            # 이메일 없음과 데이터 없음이 겹치는 그룹이 있을 수 있으므로 보정
            # 발송 가능 = 이메일 있고 AND 데이터 있는 그룹
            stats['valid_for_send'] = max(0, stats['has_email'] - stats['no_data'])
            
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
        # 데이터 미리보기 (접힘)
        if st.session_state.df is not None:
            with st.expander(f"📋 데이터 미리보기 ({len(st.session_state.df):,}행)", expanded=False):
                st.dataframe(st.session_state.df.head(10), width='stretch', hide_index=True)
        
        # 네비게이션 (하단 고정 스타일)
        st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col3:
            if st.button("다음 단계 →", type="primary", width='stretch', key="step1_next"):
                if st.session_state.df is not None:
                    st.session_state.current_step = 2
                    st.rerun()


def render_step2():
    """Step 2: 그룹화 및 데이터 설정
    
    간소화 원칙:
    1. 컬럼 선택/순서 없음 - 엑셀 원본 그대로 사용
    2. NaN/빈값 자동 제거 (강제)
    3. 숫자 0은 빈칸 처리 (강제)
    """
    
    # 페이지 헤더
    render_page_header(2, "그룹화 설정", "이메일 발송을 위한 그룹화 기준을 설정하세요")
    
    df = st.session_state.df
    if df is None:
        st.warning("먼저 파일을 업로드하세요", icon="⚠")
        return
    
    columns = df.columns.tolist()  # 엑셀 원본 순서 그대로 사용
    df_email = st.session_state.df_email
    use_separate = st.session_state.use_separate_email_sheet
    
    # ============================================================
    # 엑셀 원본 컬럼 그대로 사용 (선택/순서 설정 없음)
    # ============================================================
    st.session_state.display_cols = columns.copy()
    st.session_state.display_cols_order = columns.copy()
    st.session_state.excluded_cols = []
    
    # 금액 컬럼 자동 감지 (천단위 콤마용)
    st.session_state.amount_cols = [c for c in columns if any(k in c for k in ['금액', '수수료', '처방액', '합계'])]
    st.session_state.percent_cols = [c for c in columns if '율' in c or '%' in c or '퍼센트' in c]
    st.session_state.date_cols = [c for c in columns if '일' in c or '월' in c or '날짜' in c or 'date' in c.lower()]
    st.session_state.id_cols = [c for c in columns if '번호' in c or 'ID' in c.lower() or '코드' in c]
    
    # NaN/0 처리 - 항상 강제 적용
    st.session_state.zero_as_blank = True
    
    # 데이터 병합 설정 (별도 이메일 시트 사용 시)
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
        
        # 세금계산서 발행 정보 체크박스 (기본 활성화)
        st.markdown("---")
        show_tax_invoice = st.checkbox(
            "🧾 세금계산서 발행 정보 표시",
            value=st.session_state.get('show_tax_invoice_info', True),  # 기본값 True
            help="활성화 시 각 그룹의 세금계산서 발행 금액(합계 행의 총 수수료액)을 요약 표시합니다"
        )
        st.session_state.show_tax_invoice_info = show_tax_invoice
        
        # 금액 컬럼 후보 탐지 (체크박스 상태와 관계없이)
        amount_col_candidates = [c for c in columns if '총' in c and '수수료' in c]  # '총 수수료액' 우선
        if not amount_col_candidates:
            amount_col_candidates = [c for c in columns if '수수료' in c]
        if not amount_col_candidates:
            amount_col_candidates = [c for c in columns if '금액' in c or '합계' in c]
        
        # 기본 세금계산서 금액 컬럼 자동 설정 (없으면)
        if 'tax_amount_col' not in st.session_state or not st.session_state.tax_amount_col:
            if amount_col_candidates:
                st.session_state.tax_amount_col = amount_col_candidates[0]
        
        if show_tax_invoice:
            # 세금계산서 발행 금액 컬럼 선택
            current_tax_col = st.session_state.get('tax_amount_col', '')
            default_idx = 0
            if current_tax_col in columns:
                default_idx = columns.index(current_tax_col)
            elif amount_col_candidates and amount_col_candidates[0] in columns:
                default_idx = columns.index(amount_col_candidates[0])
            
            tax_amount_col = st.selectbox(
                "발행 금액 컬럼 (합계 행에서 추출)",
                columns,
                index=default_idx,
                help="합계 행에서 가져올 금액 컬럼 (예: 총 수수료액)",
                key="tax_amount_col_select"
            )
            st.session_state.tax_amount_col = tax_amount_col
            st.caption(f"ℹ️ 선택된 컬럼: **{tax_amount_col}**의 합계 행 값이 발행 금액으로 표시됩니다")
            
            # ============================================================
            # 🧾 세금계산서 발행 정보 미리보기 (Step 2 내에서 즉시 표시)
            # ============================================================
            st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
            
            # 그룹 컬럼 탐지
            group_col = st.session_state.get('group_key_col')
            if not group_col:
                group_candidates = [c for c in columns if 'CSO' in c or '관리업체' in c]
                group_col = group_candidates[0] if group_candidates else columns[0]
            
            # 현재 데이터에서 합계 행 추출하여 미리보기 생성
            if df is not None and tax_amount_col in df.columns and group_col in df.columns:
                # 합계 행 찾기 (그룹명 + ' 합계' 패턴)
                tax_preview_data = []
                total_amount = 0
                
                # 유니크 그룹 추출 (합계 행 제외)
                unique_groups = df[group_col].dropna().unique()
                base_groups = [g for g in unique_groups 
                              if not str(g).endswith(' 합계') 
                              and str(g).lower() not in ['nan', 'none', '']]
                
                for group_name in base_groups:
                    # 해당 그룹의 합계 행 찾기
                    sum_row_name = f"{group_name} 합계"
                    sum_rows = df[df[group_col] == sum_row_name]
                    
                    if len(sum_rows) > 0:
                        # 합계 행에서 금액 추출
                        try:
                            amt_val = sum_rows[tax_amount_col].iloc[0]
                            if pd.notna(amt_val):
                                amt_str = str(amt_val).replace(',', '').replace('원', '').strip()
                                if amt_str and amt_str not in ['', '-', 'nan', 'None']:
                                    amount = float(amt_str)
                                    if amount > 0:
                                        tax_preview_data.append({
                                            'CSO관리업체명': group_name,
                                            '발행 금액': amount
                                        })
                                        total_amount += amount
                        except (ValueError, TypeError, IndexError):
                            pass
                
                # 미리보기 표시
                if tax_preview_data:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                                padding: 12px 16px; border-radius: 8px; margin-top: 8px;
                                border-left: 4px solid #4caf50;">
                        <strong style="color: #2e7d32;">📋 미리보기</strong>
                        <span style="color: #666; font-size: 0.85em; margin-left: 8px;">
                            (3단계에서 상세 확인 가능)
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 요약 표시 (최대 5개)
                    preview_count = min(5, len(tax_preview_data))
                    preview_df = pd.DataFrame(tax_preview_data[:preview_count])
                    
                    col_preview, col_summary = st.columns([3, 1])
                    with col_preview:
                        st.dataframe(
                            preview_df,
                            width='stretch',
                            hide_index=True,
                            column_config={
                                "CSO관리업체명": st.column_config.TextColumn("CSO관리업체명", width="medium"),
                                "발행 금액": st.column_config.NumberColumn("발행 금액", format="₩%,.0f", width="small")
                            },
                            height=min(120, 35 + preview_count * 35)
                        )
                    with col_summary:
                        st.metric("총 발행 금액", f"₩{total_amount:,.0f}")
                        if len(tax_preview_data) > 5:
                            st.caption(f"외 {len(tax_preview_data) - 5}개 업체")
                else:
                    st.info("합계 행에서 발행 금액을 찾을 수 없습니다. 컬럼을 확인해 주세요.", icon="ℹ️")
    
    # ============================================================
    # 이메일 컬럼 자동 감지 (별도 시트 미사용 시)
    # ============================================================
    if not use_separate:
        # 현재 데이터에서 이메일 컬럼 자동 감지
        email_col_candidates = [c for c in columns if '이메일' in c or 'mail' in c.lower() or 'email' in c.lower()]
        if email_col_candidates:
            # 기존 설정이 있으면 유지, 없으면 첫 번째 후보 사용
            current_email_col = st.session_state.get('email_col')
            if current_email_col not in email_col_candidates:
                st.session_state.email_col = email_col_candidates[0]
        else:
            st.session_state.email_col = None
    
    # ============================================================
    # 📧 이메일 표시 컬럼 선택
    # ============================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                padding: 12px 16px; border-radius: 8px; margin-bottom: 8px;
                border-left: 4px solid #1976d2;">
        <strong style="color: #1565c0;">📧 이메일 표시 컬럼</strong>
        <br><small style="color: #1976d2;">이메일에 포함할 컬럼을 선택하세요</small>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        # 표시 컬럼 선택
        current_display = st.session_state.get('display_cols', columns.copy())
        # 유효한 컬럼만 필터링
        current_display = [c for c in current_display if c in columns]
        if not current_display:
            current_display = columns.copy()
        
        display_cols = st.multiselect(
            "표시할 컬럼 선택",
            options=columns,
            default=current_display,
            key="step2_display_cols",
            help="선택한 컬럼만 이메일 표에 표시됩니다"
        )
        
        if not display_cols:
            st.warning("⚠️ 최소 1개 이상의 컬럼을 선택하세요")
            display_cols = columns.copy()
        
        st.session_state.display_cols = display_cols
        st.caption(f"✅ **{len(display_cols)}개** 컬럼 선택됨")
    
    # ============================================================
    # 🏷️ 컬럼 형식 지정 (금액, 퍼센트, 날짜, ID)
    # ============================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); 
                padding: 12px 16px; border-radius: 8px; margin-bottom: 8px;
                border-left: 4px solid #f57c00;">
        <strong style="color: #e65100;">🏷️ 컬럼 형식 지정</strong>
        <br><small style="color: #f57c00;">각 컬럼의 데이터 형식을 지정하세요 (자동 감지됨)</small>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        # 자동 감지
        auto_amount = [c for c in columns if any(k in c for k in ['금액', '수수료', '처방액', '합계', '원'])]
        auto_percent = [c for c in columns if '율' in c or '%' in c or '퍼센트' in c]
        auto_date = [c for c in columns if '일' in c or '월' in c or '날짜' in c or 'date' in c.lower()]
        auto_id = [c for c in columns if '번호' in c or 'ID' in c.lower() or '코드' in c]
        
        # 현재 설정 또는 자동 감지 사용
        current_amount = st.session_state.get('amount_cols', auto_amount)
        current_amount = [c for c in current_amount if c in columns]
        current_percent = st.session_state.get('percent_cols', auto_percent)
        current_percent = [c for c in current_percent if c in columns]
        current_date = st.session_state.get('date_cols', auto_date)
        current_date = [c for c in current_date if c in columns]
        current_id = st.session_state.get('id_cols', auto_id)
        current_id = [c for c in current_id if c in columns]
        
        col1, col2 = st.columns(2)
        
        with col1:
            amount_cols = st.multiselect(
                "💰 금액 컬럼 (합계 계산용)",
                options=columns,
                default=current_amount,
                key="step2_amount_cols",
                help="숫자 합계 계산에 사용될 컬럼"
            )
            st.session_state.amount_cols = amount_cols
            
            percent_cols = st.multiselect(
                "📊 퍼센트 컬럼",
                options=columns,
                default=current_percent,
                key="step2_percent_cols",
                help="백분율 데이터가 포함된 컬럼"
            )
            st.session_state.percent_cols = percent_cols
        
        with col2:
            date_cols = st.multiselect(
                "📅 날짜 컬럼",
                options=columns,
                default=current_date,
                key="step2_date_cols",
                help="날짜/월 데이터가 포함된 컬럼"
            )
            st.session_state.date_cols = date_cols
            
            id_cols = st.multiselect(
                "🔢 ID/코드 컬럼",
                options=columns,
                default=current_id,
                key="step2_id_cols",
                help="바코드, 사업자번호 등 숫자 코드 컬럼"
            )
            st.session_state.id_cols = id_cols
        
        # 요약
        total_formatted = len(amount_cols) + len(percent_cols) + len(date_cols) + len(id_cols)
        if total_formatted > 0:
            st.caption(f"🏷️ 형식 지정: 금액 {len(amount_cols)}개 | 퍼센트 {len(percent_cols)}개 | 날짜 {len(date_cols)}개 | ID {len(id_cols)}개")
        
        # NaN/0 처리 안내
        st.info("**🔧 자동 처리**: 엑셀 원본 형식 유지 ✓ | NaN → 빈칸 ✓ | 0 → 빈칸 ✓", icon="ℹ️")
    
    # ============================================================
    # 이메일 충돌 처리
    # ============================================================
    with st.container(border=True):
        st.markdown("##### 이메일 충돌 처리")
        saved_resolution = st.session_state.get('conflict_resolution', 'first')
        options = ['first', 'most_common', 'skip']
        conflict_resolution = st.radio(
            "충돌 해결",
            options,
            index=options.index(saved_resolution) if saved_resolution in options else 0,
            format_func=lambda x: {'first': '첫 번째 이메일', 'most_common': '가장 많이 등장', 'skip': '건너뛰기'}[x],
            horizontal=True,
            label_visibility="collapsed",
            key="conflict_resolution_radio"
        )
        st.session_state.conflict_resolution = conflict_resolution
    
    # ============================================================
    # 네비게이션 버튼
    # ============================================================
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("🔄 다시 시작", width='stretch', key="step2_prev"):
            reset_and_restart()
    
    with col3:
        if st.button("다음 단계 →", type="primary", width='stretch', key="step2_next"):
            _save_step2_config_and_move(3, columns, df, df_email, use_separate,
                                       process_data=True, group_key_col=group_key_col,
                                       use_wildcard=use_wildcard, conflict_resolution=conflict_resolution)


def _save_step2_config_and_move(target_step: int, columns: list, df, df_email, 
                                 use_separate: bool,
                                 process_data: bool = False, group_key_col: str = None,
                                 use_wildcard: bool = False, conflict_resolution: str = 'first'):
    """Step 2 설정 후 스텝 이동 (내부 헬퍼 함수)
    
    간소화: JSON 저장 제거, 엑셀 원본 그대로 사용
    """
    # 엑셀 원본 컬럼 그대로 사용
    display_cols = columns.copy()
    amount_cols = st.session_state.get('amount_cols', [])
    percent_cols = st.session_state.get('percent_cols', [])
    date_cols = st.session_state.get('date_cols', [])
    id_cols = st.session_state.get('id_cols', [])
    
    add_log(f"Step 2 완료: {len(display_cols)}개 컬럼")
    
    # 데이터 처리 (다음 단계로 갈 때만)
    if process_data and target_step == 3:
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
            add_log(f"데이터 그룹화 완료: {len(grouped)}개 그룹")
    
    # 스텝 이동
    st.session_state.current_step = target_step
    st.rerun()


def render_step3():
    """Step 3: 데이터 검토 - 필터 기능 및 세금계산서 발행 정보 포함"""
    
    # 페이지 헤더
    render_page_header(3, "데이터 검토", "발송될 그룹 데이터를 확인하세요")
    
    grouped = st.session_state.grouped_data
    if not grouped:
        st.warning("그룹 데이터가 없습니다", icon="⚠")
        return
    
    # 요약 메트릭 계산
    total = len(grouped)
    valid = sum(1 for g in grouped.values() if g['recipient_email'] and validate_email(g['recipient_email']))
    no_email = sum(1 for g in grouped.values() if not g['recipient_email'] or not validate_email(g.get('recipient_email', '')))
    # 데이터 없는 거래처 = 행이 0이거나 필수 값 누락
    no_data = sum(1 for g in grouped.values() if g['row_count'] == 0)
    
    # ============================================================
    # 세금계산서 발행 정보 배너 (활성화 시)
    # ============================================================
    show_tax_invoice = st.session_state.get('show_tax_invoice_info', False)
    tax_amount_col = st.session_state.get('tax_amount_col', None)
    
    # tax_amount_col이 없으면 자동 탐지 시도
    if show_tax_invoice and not tax_amount_col and grouped:
        # 첫 번째 그룹의 row에서 컬럼 추출
        first_group = next(iter(grouped.values()), {})
        first_rows = first_group.get('rows', [])
        if first_rows:
            available_cols = list(first_rows[0].keys())
            candidates = [c for c in available_cols if '총' in str(c) and '수수료' in str(c)]
            if not candidates:
                candidates = [c for c in available_cols if '수수료' in str(c)]
            if not candidates:
                candidates = [c for c in available_cols if '금액' in str(c)]
            if candidates:
                tax_amount_col = candidates[0]
                st.session_state.tax_amount_col = tax_amount_col
    
    if show_tax_invoice and tax_amount_col:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                    padding: 16px 20px; border-radius: 10px; margin-bottom: 16px;
                    border-left: 4px solid #4caf50;">
            <strong style="color: #2e7d32; font-size: 1.1em;">🧾 세금계산서 발행 정보</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # 각 그룹의 합계 행에서 총 수수료액 추출
        tax_invoice_data = []
        total_tax_amount = 0
        
        for group_key, group_data in grouped.items():
            # 합계 행 찾기 (CSO관리업체 합계 또는 마지막 행)
            rows = group_data.get('rows', [])
            tax_amount = 0
            
            for row in rows:
                # 그룹명 + ' 합계' 패턴의 행에서 금액 추출
                row_values = list(row.values())
                is_total_row = any('합계' in str(v) for v in row_values)
                
                if is_total_row and tax_amount_col in row:
                    try:
                        amt_str = str(row[tax_amount_col]).replace(',', '').replace('원', '').strip()
                        if amt_str and amt_str not in ['', '-', 'nan', 'None']:
                            tax_amount = float(amt_str)
                    except (ValueError, TypeError):
                        pass
            
            # 합계 행이 없으면 totals에서 가져오기
            if tax_amount == 0 and group_data.get('totals'):
                totals = group_data.get('totals', {})
                if tax_amount_col in totals:
                    try:
                        amt_str = str(totals[tax_amount_col]).replace(',', '').replace('원', '').strip()
                        if amt_str and amt_str not in ['', '-', 'nan', 'None']:
                            tax_amount = float(amt_str)
                    except (ValueError, TypeError):
                        pass
            
            if tax_amount > 0:
                tax_invoice_data.append({
                    'CSO관리업체명': group_key,
                    '발행 금액': tax_amount
                })
                total_tax_amount += tax_amount
        
        if tax_invoice_data:
            col_summary, col_total = st.columns([3, 1])
            with col_summary:
                tax_df = pd.DataFrame(tax_invoice_data)
                st.dataframe(
                    tax_df,
                    width='stretch',
                    hide_index=True,
                    column_config={
                        "CSO관리업체명": st.column_config.TextColumn("CSO관리업체명", width="medium"),
                        "발행 금액": st.column_config.NumberColumn("발행 금액", format="₩%,.0f", width="medium")
                    },
                    height=min(150, 50 + len(tax_invoice_data) * 35)
                )
            with col_total:
                st.metric("총 발행 금액", f"₩{total_tax_amount:,.0f}")
        else:
            st.info("세금계산서 발행 정보가 없습니다", icon="ℹ️")
        
        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
    
    # ============================================================
    # 요약 메트릭 (상단 고정)
    # ============================================================
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 그룹", f"{total:,}개")
    with col2:
        st.metric("발송 가능", f"{valid:,}개", delta=f"{valid/total*100:.0f}%" if total > 0 else "0%")
    with col3:
        st.metric("이메일 없음", f"{no_email:,}개", delta=f"-{no_email}" if no_email > 0 else None, delta_color="inverse")
    
    # ============================================================
    # 필터 버튼 3종
    # ============================================================
    st.markdown("##### 🔍 필터")
    
    # 필터 상태 초기화
    if 'step3_filter' not in st.session_state:
        st.session_state.step3_filter = 'all'
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if st.button(
            f"📧 전체 발송 대상 ({valid})",
            width='stretch',
            type="primary" if st.session_state.step3_filter == 'all' else "secondary",
            key="filter_all"
        ):
            st.session_state.step3_filter = 'all'
            st.rerun()
    
    with col_f2:
        if st.button(
            f"📭 이메일 없음 ({no_email})",
            width='stretch',
            type="primary" if st.session_state.step3_filter == 'no_email' else "secondary",
            key="filter_no_email"
        ):
            st.session_state.step3_filter = 'no_email'
            st.rerun()
    
    with col_f3:
        if st.button(
            f"📋 데이터 없음 ({no_data})",
            width='stretch',
            type="primary" if st.session_state.step3_filter == 'no_data' else "secondary",
            key="filter_no_data"
        ):
            st.session_state.step3_filter = 'no_data'
            st.rerun()
    
    st.divider()
    
    # ============================================================
    # 필터링된 데이터 표시
    # ============================================================
    current_filter = st.session_state.step3_filter
    
    # 필터 적용
    if current_filter == 'all':
        filtered_groups = {k: v for k, v in grouped.items() 
                         if v['recipient_email'] and validate_email(v['recipient_email'])}
        filter_title = "전체 발송 대상"
    elif current_filter == 'no_email':
        filtered_groups = {k: v for k, v in grouped.items() 
                         if not v['recipient_email'] or not validate_email(v.get('recipient_email', ''))}
        filter_title = "이메일 없는 거래처"
    elif current_filter == 'no_data':
        filtered_groups = {k: v for k, v in grouped.items() if v['row_count'] == 0}
        filter_title = "데이터 없는 거래처"
    else:
        filtered_groups = grouped
        filter_title = "전체"
    
    # 상세 검토
    with st.container(border=True):
        st.markdown(f"##### 상세 데이터 검토 - {filter_title} ({len(filtered_groups)}개)")
        
        if filtered_groups:
            # 그룹 선택 상태 유지
            group_keys = list(filtered_groups.keys())
            prev_selected = st.session_state.get('step3_selected_group', None)
            default_idx = group_keys.index(prev_selected) if prev_selected in group_keys else 0
            
            selected = st.selectbox(
                "그룹 선택",
                group_keys,
                index=default_idx,
                format_func=lambda x: f"{x} ({filtered_groups[x]['row_count']}행)",
                label_visibility="collapsed",
                key="step3_group_select"
            )
            st.session_state.step3_selected_group = selected
            
            if selected:
                g = filtered_groups[selected]
                
                # 수신자 정보
                email_status = g['recipient_email'] if g['recipient_email'] else '❌ 없음'
                st.markdown(f"**수신자:** `{email_status}`")
                
                if g['has_conflict']:
                    st.warning(f"이메일 충돌: {', '.join(g['conflict_emails'])}", icon="⚠")
                
                # 데이터 테이블 - 사용자가 설정한 컬럼 순서 유지
                display_cols = st.session_state.get('display_cols', [])
                rows_data = g['rows']
                
                if rows_data:
                    # DataFrame 생성 시 컬럼 순서 유지
                    df_display = pd.DataFrame(rows_data)
                    
                    # 표시할 컬럼만 필터링 (순서 유지)
                    if display_cols:
                        available_cols = [c for c in display_cols if c in df_display.columns]
                        if available_cols:
                            df_display = df_display[available_cols]
                    
                    # '합계' 행의 거래처명 위치에 '총 합계' 표시
                    group_key_col = st.session_state.get('group_key_col', '')
                    if group_key_col and group_key_col in df_display.columns:
                        df_display[group_key_col] = df_display[group_key_col].apply(
                            lambda x: '📊 총 합계' if '합계' in str(x) else x
                        )
                    
                    st.dataframe(
                        df_display, 
                        width='stretch', 
                        hide_index=True,
                        height=250
                    )
                else:
                    st.info("데이터가 없습니다", icon="ℹ️")
        else:
            st.info(f"{filter_title}에 해당하는 항목이 없습니다", icon="ℹ️")
    
    # 발송 대상 목록
    with st.container(border=True):
        st.markdown(f"##### 📋 {filter_title} 목록")
        
        if filtered_groups:
            preview_data = []
            for k, v in filtered_groups.items():
                preview_data.append({
                    '업체명': k, 
                    '이메일': v['recipient_email'] or '-',
                    '데이터 행수': v['row_count'],
                    '상태': '✅ 발송 가능' if v['recipient_email'] and validate_email(v['recipient_email']) else '❌ 발송 불가'
                })
            
            preview_df = pd.DataFrame(preview_data)
            
            st.dataframe(
                preview_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "업체명": st.column_config.TextColumn("업체명", width="medium"),
                    "이메일": st.column_config.TextColumn("이메일", width="large"),
                    "데이터 행수": st.column_config.NumberColumn("행수", format="%d", width="small"),
                    "상태": st.column_config.TextColumn("상태", width="small")
                }
            )
        else:
            st.info("표시할 항목이 없습니다", icon="ℹ")
    
    # 네비게이션
    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🔄 다시 시작", width='stretch', key="step3_prev"):
            reset_and_restart()
    with col3:
        if st.button("다음 단계 →", type="primary", width='stretch', disabled=valid==0, key="step3_next"):
            st.session_state.current_step = 4
            st.rerun()


def render_step4():
    """Step 4: 템플릿 편집 - 세로 레이아웃, 미리보기 버튼"""
    
    # 페이지 헤더
    render_page_header(4, "템플릿 편집", "이메일 제목과 본문을 커스터마이징하세요")
    
    # 템플릿 프리셋은 constants.py에서 import (TEMPLATE_PRESETS)
    # to_dict() 메서드로 딕셔너리 형태로 변환하여 사용
    
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
        if st.button("적용", width='stretch'):
            preset = TEMPLATE_PRESETS[preset_name]
            st.session_state.subject_template = preset.subject
            st.session_state.header_title = preset.header
            st.session_state.email_body_text = preset.body
            st.session_state.footer_template = preset.footer
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
        st.session_state.email_body_text = TEMPLATE_PRESETS["기본 (정산서)"].body
    
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
    
    # ============================================================
    # 실제 발송 이메일 미리보기
    # ============================================================
    grouped = st.session_state.grouped_data
    valid_list = [(k, v) for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])]
    
    if valid_list:
        st.markdown("##### 📬 실제 발송 이메일 미리보기")
        
        # 업체 선택
        preview_options = [f"{k} ({v['recipient_email']})" for k, v in valid_list[:20]]
        selected_idx = st.selectbox(
            "미리보기 대상 선택",
            range(len(preview_options)),
            format_func=lambda x: preview_options[x],
            key="step4_preview_select"
        )
        
        sample_key, sample_data = valid_list[selected_idx]
        
        try:
            # 템플릿 데이터 준비
            templates = {
                'subject': subject,
                'header': header,
                'greeting': body_text,
                'info': '',
                'additional': '',
                'footer': footer
            }
            
            display_cols = st.session_state.get('display_cols', [])
            amount_cols = st.session_state.get('amount_cols', [])
            
            # 세금계산서 발행 정보 HTML 생성
            tax_invoice_html = ""
            show_tax_invoice = st.session_state.get('show_tax_invoice_info', False)
            tax_amount_col = st.session_state.get('tax_amount_col')
            
            if show_tax_invoice and tax_amount_col:
                rows = sample_data.get('rows', [])
                tax_amount = 0
                
                for row in rows:
                    row_values = list(row.values())
                    is_total_row = any('합계' in str(v) for v in row_values)
                    
                    if is_total_row and tax_amount_col in row:
                        try:
                            amt_str = str(row[tax_amount_col]).replace(',', '').replace('원', '').strip()
                            if amt_str and amt_str not in ['', '-', 'nan', 'None']:
                                tax_amount = float(amt_str)
                        except (ValueError, TypeError):
                            pass
                
                if tax_amount == 0:
                    totals = sample_data.get('totals', {})
                    if tax_amount_col in totals:
                        try:
                            amt_str = str(totals[tax_amount_col]).replace(',', '').replace('원', '').strip()
                            if amt_str and amt_str not in ['', '-', 'nan', 'None']:
                                tax_amount = float(amt_str)
                        except (ValueError, TypeError):
                            pass
                
                if tax_amount > 0:
                    tax_invoice_html = f'''
                    <div style="background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%); 
                                padding: 16px 20px; border-radius: 10px; margin: 16px 0;
                                border-left: 4px solid #ffc107; border: 1px solid #ffca28;">
                        <strong style="color: #856404; font-size: 1.1em;">🧾 세금계산서 발행 정보</strong>
                        <div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <span style="color: #665c00;">CSO관리업체명:</span>
                                <strong style="color: #333; margin-left: 8px;">{sample_key}</strong>
                            </div>
                            <div style="white-space: nowrap;">
                                <span style="color: #665c00;">발행 금액:</span>
                                <strong style="color: #856404; font-size: 1.3em; margin-left: 8px;">₩{tax_amount:,.0f}</strong>
                            </div>
                        </div>
                    </div>
                    '''
            
            # render_email_content로 실제 이메일 HTML 생성
            email_html = render_email_content(
                sample_key, 
                sample_data, 
                display_cols, 
                amount_cols, 
                templates,
                extra_html_before_table=tax_invoice_html
            )
            
            # 제목 미리보기
            subject_preview = Template(subject).render(
                company_name=sample_key,
                period=datetime.now().strftime('%Y년 %m월')
            )
            
            # 발송 정보 표시
            st.info(f"**수신:** {sample_data.get('recipient_email')} | **제목:** {subject_preview}", icon="📧")
            
            # 실제 이메일 HTML 미리보기
            st.components.v1.html(email_html, height=600, scrolling=True)
                    
        except Exception as e:
            st.error(f"미리보기 오류: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.info("미리보기할 데이터가 없습니다. 먼저 데이터를 업로드하고 설정을 완료하세요.", icon="ℹ️")
    
    # 네비게이션
    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🔄 다시 시작", width='stretch', key="step4_prev"):
            reset_and_restart()
    with col3:
        if st.button("발송 단계로 →", type="primary", width='stretch', key="step4_next"):
            st.session_state.current_step = 5
            st.rerun()


def render_step5():
    """Step 5: 발송 - UX 최적화 (안심 장치, 즉각적 피드백)"""
    
    # 세금계산서 발행 정보 HTML 생성 헬퍼 함수
    def get_tax_invoice_html(group_key: str, group_data: dict) -> str:
        """그룹 데이터에서 세금계산서 발행 정보 HTML 생성"""
        show_tax_invoice = st.session_state.get('show_tax_invoice_info', False)
        tax_amount_col = st.session_state.get('tax_amount_col')
        
        if not show_tax_invoice or not tax_amount_col:
            return ""
        
        # 합계 행에서 세금계산서 금액 추출
        rows = group_data.get('rows', [])
        tax_amount = 0
        
        for row in rows:
            row_values = list(row.values())
            is_total_row = any('합계' in str(v) for v in row_values)
            
            if is_total_row and tax_amount_col in row:
                try:
                    amt_str = str(row[tax_amount_col]).replace(',', '').replace('원', '').strip()
                    if amt_str and amt_str not in ['', '-', 'nan', 'None']:
                        tax_amount = float(amt_str)
                except (ValueError, TypeError):
                    pass
        
        # 합계 행에서 못 찾으면 totals에서
        if tax_amount == 0:
            totals = group_data.get('totals', {})
            if tax_amount_col in totals:
                try:
                    amt_str = str(totals[tax_amount_col]).replace(',', '').replace('원', '').strip()
                    if amt_str and amt_str not in ['', '-', 'nan', 'None']:
                        tax_amount = float(amt_str)
                except (ValueError, TypeError):
                    pass
        
        if tax_amount > 0:
            return f'''
            <div style="background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%); 
                        padding: 16px 20px; border-radius: 10px; margin: 16px 0;
                        border-left: 4px solid #ffc107; border: 1px solid #ffca28;">
                <strong style="color: #856404; font-size: 1.1em;">🧾 세금계산서 발행 정보</strong>
                <div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span style="color: #665c00;">CSO관리업체명:</span>
                        <strong style="color: #333; margin-left: 8px;">{group_key}</strong>
                    </div>
                    <div style="white-space: nowrap;">
                        <span style="color: #665c00;">발행 금액:</span>
                        <strong style="color: #856404; font-size: 1.3em; margin-left: 8px; white-space: nowrap;">₩{tax_amount:,.0f}</strong>
                    </div>
                </div>
            </div>
            '''
        return ""
    
    # 페이지 헤더
    render_page_header(5, "메일 발송", "최종 확인 후 이메일을 발송하세요")
    
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
        if st.button("🔄 다시 시작", width='stretch', key="step5_prev"):
            reset_and_restart()
    
    with col2:
        test_btn = st.button(
            "📧 내게 테스트",
            width='stretch',
            disabled=not st.session_state.smtp_config,
            help="내 이메일로 샘플 1건 발송하여 미리 확인"
        )
    
    with col3:
        # 실패 건만 재발송 버튼
        failed_list = [r for r in st.session_state.get('send_results', []) if r.get('상태') == '실패']
        resend_btn = st.button(
            f"🔄 실패 재발송 ({len(failed_list)})",
            width='stretch',
            disabled=not st.session_state.smtp_config or len(failed_list) == 0,
            help="실패한 건만 다시 발송"
        )
    
    with col4:
        send_btn = st.button(
            "🚀 전체 발송",
            type="primary",
            width='stretch',
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
            confirmed = st.button("✅ 예, 발송합니다", type="primary", width='stretch')
        with col_no:
            if st.button("❌ 취소", width='stretch'):
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
                # 세금계산서 정보 HTML 생성
                tax_html = get_tax_invoice_html(sample_key, sample_data)
                html = render_email_content(sample_key, sample_data,
                    st.session_state.display_cols, st.session_state.amount_cols, templates,
                    extra_html_before_table=tax_html)
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
                if st.button("🛑 긴급 정지", type="secondary", width='stretch'):
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
                    # 세금계산서 정보 HTML 생성
                    tax_html = get_tax_invoice_html(gk, gd)
                    html = render_email_content(gk, gd, st.session_state.display_cols,
                        st.session_state.amount_cols, templates,
                        extra_html_before_table=tax_html)
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
                    width='stretch',
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
                    width='stretch',
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
                    width='stretch'
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
                        width='stretch'
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
        search_btn = st.button("🔍 검색", width='stretch')
    
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
                st.plotly_chart(fig, width='stretch')
    
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
            width='stretch',
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
    
    # Custom CSS 적용
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    init_session_state()
    
    # 로컬 실행 가이드 다이얼로그
    if st.session_state.get('show_local_guide', False):
        show_guide = render_local_guide_dialog()
        show_guide()
        st.session_state.show_local_guide = False
    
    # 자동로그인 설정 가이드 다이얼로그
    if st.session_state.get('show_auto_login_guide', False):
        show_auto_login = render_auto_login_guide_dialog()
        show_auto_login()
        st.session_state.show_auto_login_guide = False
    
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
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            color: white;
        ">
            <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: white;">
                📜 발송 이력
            </h2>
            <p style="margin: 8px 0 0 0; opacity: 0.85; font-size: 0.9rem; color: white;">
                이전에 발송한 이메일 기록을 확인하세요
            </p>
        </div>
        """, unsafe_allow_html=True)
        render_history_tab()


if __name__ == "__main__":
    main()
