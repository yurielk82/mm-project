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
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import time
import io
from jinja2 import Template
import re

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
# CUSTOM CSS - Enterprise Dashboard Style
# ============================================================================

CUSTOM_CSS = """
<style>
    /* 전체 레이아웃 */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* 사이드바 전체 가운데 정렬 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        text-align: center;
    }
    [data-testid="stSidebar"] .stButton {
        display: flex;
        justify-content: center;
    }
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        text-align: center;
    }
    [data-testid="stSidebar"] .stAlert {
        text-align: center;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* 데이터프레임 스타일 */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* 상태 배지 */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .status-success { background: rgba(40, 167, 69, 0.2); color: var(--success-color); }
    .status-warning { background: rgba(255, 193, 7, 0.2); color: var(--warning-color); }
    .status-error { background: rgba(220, 53, 69, 0.2); color: #dc3545; }
</style>
"""


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
    """헤더 - 깔끔한 브랜딩"""
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
            <span style="font-size: 2rem;">📨</span>
            <div>
                <h1 style="margin: 0; font-size: 1.8rem; color: #1e3c72;">{APP_TITLE}</h1>
                <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">{APP_SUBTITLE}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 0.5rem;">
            <span style="background: #e9ecef; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; color: #6c757d;">
                v{VERSION}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()


def render_step_indicator():
    """스텝 진행 상태 표시 (Streamlit 네이티브)"""
    current = st.session_state.current_step
    
    # 스텝 컬럼 생성
    cols = st.columns(len(STEPS))
    
    for i, (col, step_name) in enumerate(zip(cols, STEPS), 1):
        with col:
            if i < current:
                # 완료된 스텝 - 클릭하면 이동
                if st.button(f"✓ {step_name}", key=f"step_{i}", use_container_width=True):
                    st.session_state.current_step = i
                    st.rerun()
            elif i == current:
                # 현재 스텝
                st.button(f"● {step_name}", key=f"step_{i}", type="primary", disabled=True, use_container_width=True)
            else:
                # 대기 스텝
                st.button(f"{i}. {step_name}", key=f"step_{i}", disabled=True, use_container_width=True)
    
    st.divider()


def get_smtp_config() -> dict:
    """SMTP 설정 로드 (Secrets First)"""
    config = {
        'username': '',
        'password': '',
        'provider': 'Hiworks (하이웍스)',
        'from_secrets': False
    }
    
    try:
        if 'SMTP_ID' in st.secrets and 'SMTP_PW' in st.secrets:
            config['username'] = st.secrets['SMTP_ID']
            config['password'] = st.secrets['SMTP_PW']
            config['from_secrets'] = True
            if 'SMTP_PROVIDER' in st.secrets:
                config['provider'] = st.secrets['SMTP_PROVIDER']
            return config
    except Exception:
        pass
    
    if st.session_state.get('saved_smtp_user'):
        config['username'] = st.session_state.saved_smtp_user
        config['password'] = st.session_state.get('saved_smtp_pass', '')
        config['provider'] = st.session_state.get('saved_smtp_provider', 'Hiworks (하이웍스)')
    
    return config


def save_to_session(provider: str, username: str, password: str):
    """SMTP 자격증명 세션 저장"""
    st.session_state.saved_smtp_provider = provider
    st.session_state.saved_smtp_user = username
    st.session_state.saved_smtp_pass = password


def clear_session_credentials():
    """세션 자격증명 삭제"""
    for key in ['saved_smtp_provider', 'saved_smtp_user', 'saved_smtp_pass']:
        if key in st.session_state:
            del st.session_state[key]


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
        st.markdown('<div class="guide-code">git clone https://github.com/yurielk82/mm-project.git<br>cd mm-project</div>', unsafe_allow_html=True)
        st.caption("또는 GitHub에서 ZIP 다운로드 후 압축 해제")
        
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


def render_smtp_sidebar():
    """사이드바 - 제목 → SMTP상태 → 현재상태 → 처음부터 다시 → SMTP설정 → 가이드 → 저작권"""
    with st.sidebar:
        
        # ============================================================
        # 0. 앱 제목 + SMTP 상태 (최상단, 가장 중요한 정보)
        # ============================================================
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; font-weight: 700;">{APP_TITLE}</span>
            <span style="font-size: 0.65rem; opacity: 0.5;">v{VERSION}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # SMTP 상태를 제목 바로 아래에 눈에 띄게 배치
        if st.session_state.smtp_config:
            st.success("✅ SMTP 연결됨", icon=None)
        else:
            st.info("📧 SMTP를 연결해 주세요", icon=None)
        
        st.divider()
        
        # ============================================================
        # 1. 현재 상태 (데이터/발송대상)
        # ============================================================
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.df is not None:
                st.metric("데이터", f"{len(st.session_state.df):,}")
            else:
                st.metric("데이터", "0")
        
        with col2:
            if st.session_state.grouped_data:
                valid = sum(1 for g in st.session_state.grouped_data.values() 
                           if g['recipient_email'] and validate_email(g['recipient_email']))
                total = len(st.session_state.grouped_data)
                st.metric("발송", f"{valid}/{total}")
            else:
                st.metric("발송", "0")
        
        # ============================================================
        # 2. 처음부터 다시
        # ============================================================
        if st.button("🔄 처음부터", use_container_width=True):
            reset_workflow()
            st.rerun()
        
        st.divider()
        
        # ============================================================
        # 3. SMTP 설정 (항상 닫힌 상태로 시작)
        # ============================================================
        with st.expander("⚙️ SMTP 설정", expanded=False):
            smtp_defaults = get_smtp_config()
            from_secrets = smtp_defaults['from_secrets']
            
            if from_secrets:
                st.caption("🔐 Secrets에서 자동 로드됨")
            
            provider_list = list(SMTP_PROVIDERS.keys())
            default_provider_idx = 0
            if smtp_defaults['provider'] in provider_list:
                default_provider_idx = provider_list.index(smtp_defaults['provider'])
            
            provider = st.selectbox(
                "메일 서비스", 
                provider_list, 
                index=default_provider_idx, 
                key="smtp_provider",
                label_visibility="collapsed"
            )
            
            if provider == "직접 입력":
                smtp_server = st.text_input("SMTP 서버", key="smtp_server_input")
                smtp_port = st.number_input("포트", value=587, key="smtp_port_input")
            else:
                smtp_server = SMTP_PROVIDERS[provider]["server"]
                smtp_port = SMTP_PROVIDERS[provider]["port"]
                st.caption(f"`{smtp_server}:{smtp_port}`")
            
            smtp_username = st.text_input(
                "발신자 이메일", 
                value=smtp_defaults['username'],
                key="smtp_user",
                placeholder="example@company.com"
            )
            
            smtp_password = st.text_input(
                "앱 비밀번호", 
                type="password",
                value=smtp_defaults['password'],
                key="smtp_pass"
            )
            
            if st.button("연결 테스트", use_container_width=True, type="primary"):
                final_username = smtp_username if smtp_username else smtp_defaults['username']
                final_password = smtp_password if smtp_password else smtp_defaults['password']
                
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
                            st.success("연결 성공!", icon="✅")
                            server.quit()
                            st.session_state.smtp_config = config
                            if not from_secrets:
                                save_to_session(provider, final_username, final_password)
                            st.rerun()
                        else:
                            st.error(f"{error}", icon="❌")
                else:
                    st.warning("이메일과 비밀번호 입력 필요", icon="⚠")
        
        # ============================================================
        # 4. 설정 가이드
        # ============================================================
        with st.expander("📖 설정 가이드", expanded=False):
            st.markdown("""
            **secrets.toml 설정**
            ```toml
            SMTP_ID = "email@company.com"
            SMTP_PW = "app_password"
            SMTP_PROVIDER = "Hiworks (하이웍스)"
            SENDER_NAME = "회사명"
            ```
            
            📁 위치: `.streamlit/secrets.toml`
            
            ⚠️ `.gitignore`에 추가 필수!
            """)
        
        # ============================================================
        # 5. 로컬 실행 가이드 버튼 (눈에 띄게)
        # ============================================================
        st.markdown("")  # 간격
        if st.button("💻 로컬에서 실행하기", use_container_width=True, help="회사 네트워크에서 직접 실행하는 방법"):
            st.session_state.show_local_guide = True
            st.rerun()
        
        # ============================================================
        # 6. 저작권 (맨 아래)
        # ============================================================
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; padding-top: 1rem;">
            <p style="font-size: 0.6rem; opacity: 0.3; line-height: 1.4; margin: 0;">
                © 2026. Kwon Daehwan<br>
                Planned & Built by Sales Management Team, KUP<br>
                In collaboration with Genspark & Gemini
            </p>
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
        st.session_state.email_body_text = """안녕하세요, {{ company_name }} 담당자님.

{{ period }} 정산 내역을 안내드립니다.
아래 표를 확인해 주시기 바랍니다.

문의사항이 있으시면 회신 부탁드립니다.
감사합니다."""
    
    body_text = st.text_area(
        "본문",
        st.session_state.email_body_text,
        height=200,
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
        height=80,
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
    
    # 미리보기 버튼
    grouped = st.session_state.grouped_data
    valid_list = [(k, v) for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])]
    
    if valid_list:
        col_select, col_btn = st.columns([3, 1])
        with col_select:
            preview_options = [f"{k}" for k, v in valid_list[:20]]
            selected_idx = st.selectbox(
                "미리보기 대상",
                range(len(preview_options)),
                format_func=lambda x: preview_options[x],
                label_visibility="collapsed"
            )
        with col_btn:
            show_preview = st.button("👁️ 미리보기", use_container_width=True)
        
        # 미리보기 표시 (버튼 클릭 시 또는 세션에 저장된 상태)
        if 'show_email_preview' not in st.session_state:
            st.session_state.show_email_preview = False
        
        if show_preview:
            st.session_state.show_email_preview = True
        
        if st.session_state.show_email_preview and valid_list:
            sample_key, sample_data = valid_list[selected_idx]
            
            with st.container(border=True):
                st.markdown("##### 📬 이메일 미리보기")
                
                try:
                    # 제목 미리보기
                    subject_preview = Template(subject).render(
                        company_name=sample_key,
                        period=datetime.now().strftime('%Y년 %m월')
                    )
                    st.markdown(f"**제목:** {subject_preview}")
                    
                    # 본문 미리보기
                    preview_text = Template(body_text).render(
                        company_name=sample_key,
                        company_code=sample_key,
                        period=datetime.now().strftime('%Y년 %m월')
                    )
                    
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; 
                                border: 1px solid #dee2e6; margin: 10px 0;">
                        <div style="text-align: center; font-size: 18px; font-weight: bold; 
                                    color: #2c3e50; margin-bottom: 16px;">{header}</div>
                        <div style="white-space: pre-wrap; font-size: 14px; line-height: 1.6;">
{preview_text}
                        </div>
                        <div style="background: #e9ecef; padding: 12px; margin: 16px 0; 
                                    border-radius: 4px; text-align: center;">
                            📊 [정산 테이블 {sample_data['row_count']}행]
                        </div>
                        <div style="font-size: 12px; color: #6c757d; margin-top: 16px; 
                                    border-top: 1px solid #dee2e6; padding-top: 12px;">
                            {footer if footer else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("미리보기 닫기"):
                        st.session_state.show_email_preview = False
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"미리보기 오류: {e}")
    else:
        st.info("미리보기할 데이터가 없습니다", icon="ℹ️")
    
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
    """Step 5: 발송"""
    grouped = st.session_state.grouped_data
    valid_groups = {k: v for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])}
    
    # 발송 요약 (상단)
    with st.container(border=True):
        st.markdown("##### 발송 요약")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("발송 대상", f"{len(valid_groups)}건")
        with col2:
            smtp_status = "준비 완료" if st.session_state.smtp_config else "설정 필요"
            st.metric("SMTP 상태", smtp_status)
        with col3:
            if st.session_state.send_results:
                success = sum(1 for r in st.session_state.send_results if r['상태'] == '성공')
                st.metric("발송 완료", f"{success}건")
    
    if not st.session_state.smtp_config:
        st.warning("사이드바에서 SMTP 연결 테스트를 먼저 완료하세요", icon="⚠")
    
    # 발송 설정 (이전 값 기억)
    with st.expander("발송 설정", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            batch_size = st.number_input(
                "배치 크기", 
                value=st.session_state.get('batch_size', DEFAULT_BATCH_SIZE), 
                min_value=1, 
                max_value=50,
                help="한 번에 발송할 이메일 수"
            )
            st.session_state.batch_size = batch_size
        with col2:
            email_delay_min = st.number_input(
                "딜레이 최소(초)", 
                value=st.session_state.get('email_delay_min', 5), 
                min_value=1, 
                max_value=30,
                help="이메일 간 최소 대기 시간"
            )
            st.session_state.email_delay_min = email_delay_min
        with col3:
            email_delay_max = st.number_input(
                "딜레이 최대(초)", 
                value=st.session_state.get('email_delay_max', 10), 
                min_value=email_delay_min, 
                max_value=60,
                help="이메일 간 최대 대기 시간"
            )
            st.session_state.email_delay_max = email_delay_max
        with col4:
            batch_delay = st.number_input(
                "배치 간격(초)", 
                value=st.session_state.get('batch_delay', DEFAULT_BATCH_DELAY), 
                min_value=5, 
                max_value=120,
                help="배치 완료 후 대기 시간"
            )
            st.session_state.batch_delay = batch_delay
        
        st.caption(f"💡 각 이메일 발송 후 **{email_delay_min}~{email_delay_max}초** 랜덤 대기")
    
    st.divider()
    
    # 발송 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()
    
    with col2:
        test_btn = st.button(
            "테스트 발송",
            use_container_width=True,
            disabled=not st.session_state.smtp_config,
            help="내 이메일로 샘플 1건 발송"
        )
    
    with col3:
        send_btn = st.button(
            "전체 발송",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.smtp_config or len(valid_groups)==0,
            help="모든 대상에게 이메일 발송"
        )
    
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
    
    # 전체 발송
    if send_btn and st.session_state.smtp_config and valid_groups:
        config = st.session_state.smtp_config
        
        # 진행률 표시 영역
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_col1, status_col2 = st.columns([3, 1])
            with status_col1:
                status_text = st.empty()
            with status_col2:
                count_text = st.empty()
        
        results = []
        success_cnt = fail_cnt = 0
        total = len(valid_groups)
        
        server, error = create_smtp_connection(config)
        if not server:
            st.error(f"SMTP 연결 실패: {error}", icon="❌")
        else:
            for i, (gk, gd) in enumerate(valid_groups.items()):
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
                    else:
                        fail_cnt += 1
                        results.append({'그룹': gk, '이메일': gd['recipient_email'], '상태': '실패', '사유': err})
                except Exception as e:
                    fail_cnt += 1
                    results.append({'그룹': gk, '이메일': gd['recipient_email'], '상태': '실패', '사유': str(e)})
                
                # 랜덤 딜레이 적용
                import random
                random_delay = random.uniform(email_delay_min, email_delay_max)
                time.sleep(random_delay)
                if (i+1) % batch_size == 0 and i < total-1:
                    time.sleep(batch_delay)
            
            server.quit()
            st.session_state.send_results = results
            
            status_text.markdown("**완료!**")
            
            if fail_cnt == 0:
                st.success(f"전체 발송 완료! ({success_cnt}건)", icon="🎉")
            else:
                st.warning(f"완료: 성공 {success_cnt}건, 실패 {fail_cnt}건", icon="⚠")
    
    # 결과 리포트
    if st.session_state.send_results:
        st.divider()
        
        with st.container(border=True):
            st.markdown("##### 발송 결과")
            
            results_df = pd.DataFrame(st.session_state.send_results)
            
            # 결과 요약
            success_cnt = len(results_df[results_df['상태'] == '성공'])
            fail_cnt = len(results_df[results_df['상태'] == '실패'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"✓ 성공: **{success_cnt}건**")
            with col2:
                st.markdown(f"✗ 실패: **{fail_cnt}건**")
            
            st.dataframe(
                results_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "상태": st.column_config.TextColumn(
                        "상태",
                        width="small"
                    )
                }
            )
            
            # 다운로드 버튼
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                results_df.to_excel(writer, index=False)
            
            st.download_button(
                "결과 다운로드 (Excel)",
                output.getvalue(),
                f"발송결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


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
    
    render_smtp_sidebar()
    render_step_indicator()
    
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


if __name__ == "__main__":
    main()
