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
    render_email, render_preview, format_currency, clean_id_column, format_date,
    get_styles, STREAMLIT_CUSTOM_CSS,
    DEFAULT_HEADER_TITLE, DEFAULT_HEADER_SUBTITLE, DEFAULT_GREETING,
    DEFAULT_INFO_MESSAGE, DEFAULT_ADDITIONAL_MESSAGE, DEFAULT_FOOTER_TEXT,
    DEFAULT_SUBJECT_TEMPLATE
)


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

APP_TITLE = "그룹핑 메일머지"
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
    /* 전체 폰트 및 배경 */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* 메트릭 카드 스타일 */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    [data-testid="stMetric"] label {
        color: rgba(255,255,255,0.8) !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 1.8rem !important;
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
    
    /* Primary 버튼 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* 데이터프레임 스타일 */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Expander 스타일 */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1e3c72;
    }
    
    /* 섹션 제목 */
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3c72;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e9ecef;
    }
    
    /* 카드 컨테이너 */
    .card-container {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    /* 상태 배지 */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .status-success { background: #d4edda; color: #155724; }
    .status-warning { background: #fff3cd; color: #856404; }
    .status-error { background: #f8d7da; color: #721c24; }
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
        'date_cols': [],
        'id_cols': [],
        'display_cols': [],
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
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
    """시트 로드"""
    try:
        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        return df if not df.empty else (None, "시트에 데이터가 없습니다.")
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


def clean_dataframe(df, amount_cols, date_cols, id_cols):
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
    return df_cleaned


def group_data_with_wildcard(df, group_key_col, email_col, amount_cols, display_cols,
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
        
        unique_emails = [str(e).strip() for e in group_df[email_col].dropna().unique()
                        if str(e).strip() and str(e).strip().lower() not in ['nan', 'none', '']]
        
        has_conflict = len(unique_emails) > 1
        if len(unique_emails) == 0:
            recipient_email = None
        elif len(unique_emails) == 1:
            recipient_email = unique_emails[0]
        else:
            if conflict_resolution == 'first':
                recipient_email = unique_emails[0]
            elif conflict_resolution == 'most_common':
                recipient_email = str(group_df[email_col].value_counts().index[0])
            else:
                recipient_email = None
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
                    row_dict[col] = format_currency(value) if col in amount_cols else (str(value) if pd.notna(value) else '-')
                else:
                    row_dict[col] = '-'
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
    """SMTP 연결 생성 (SSL Handshake 최적화 + 재시도 로직)"""
    import ssl
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if config['port'] == 465:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.set_ciphers('DEFAULT@SECLEVEL=1')
                
                server = smtplib.SMTP_SSL(
                    config['server'], 
                    config['port'], 
                    context=context,
                    timeout=30
                )
            else:
                server = smtplib.SMTP(config['server'], config['port'], timeout=30)
                server.ehlo()
                if config.get('use_tls', True):
                    server.starttls()
                    server.ehlo()
            
            server.login(config['username'], config['password'])
            return server, None
            
        except smtplib.SMTPAuthenticationError as e:
            error_str = str(e)
            if '454' in error_str or 'Temporary' in error_str:
                last_error = f"서버 임시 오류 (시도 {attempt+1}/{max_retries})"
                time.sleep(2)
                continue
            if '535' in error_str:
                return None, "인증 거부: 이메일/비밀번호 또는 SMTP 설정을 확인하세요."
            return None, f"인증 실패: {error_str[:100]}"
            
        except Exception as e:
            error_str = str(e)
            if 'handshake' in error_str.lower() or 'ssl' in error_str.lower():
                last_error = f"SSL 연결 오류 (시도 {attempt+1}/{max_retries})"
                time.sleep(2)
                continue
            return None, f"연결 오류: {error_str[:100]}"
    
    return None, f"연결 실패: {last_error} - 잠시 후 다시 시도하세요."


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
        greeting = Template(templates['greeting']).render(**template_vars)
        info_message = Template(templates['info']).render(**template_vars)
        additional = Template(templates['additional']).render(**template_vars)
        footer = Template(templates['footer']).render(**template_vars)
    except:
        greeting, info_message = templates['greeting'], templates['info']
        additional, footer = templates['additional'], templates['footer']
    
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
    """단계 표시기 - 깔끔한 프로그레스"""
    current = st.session_state.current_step
    
    cols = st.columns(len(STEPS))
    for i, (col, step_name) in enumerate(zip(cols, STEPS), 1):
        with col:
            if i < current:
                # 완료
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: #28a745; color: white;
                                display: inline-flex; align-items: center; justify-content: center; font-weight: bold;">
                        ✓
                    </div>
                    <p style="margin: 8px 0 0 0; font-size: 0.8rem; color: #28a745; font-weight: 500;">{step_name}</p>
                </div>
                """, unsafe_allow_html=True)
            elif i == current:
                # 현재
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: #1e3c72; color: white;
                                display: inline-flex; align-items: center; justify-content: center; font-weight: bold;">
                        {i}
                    </div>
                    <p style="margin: 8px 0 0 0; font-size: 0.8rem; color: #1e3c72; font-weight: 600;">{step_name}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 대기
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: #e9ecef; color: #adb5bd;
                                display: inline-flex; align-items: center; justify-content: center; font-weight: bold;">
                        {i}
                    </div>
                    <p style="margin: 8px 0 0 0; font-size: 0.8rem; color: #adb5bd;">{step_name}</p>
                </div>
                """, unsafe_allow_html=True)
    
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


def render_smtp_sidebar():
    """사이드바 SMTP 설정"""
    with st.sidebar:
        st.markdown("#### SMTP 설정")
        
        smtp_defaults = get_smtp_config()
        from_secrets = smtp_defaults['from_secrets']
        
        if from_secrets:
            st.success("Secrets 자동 로드", icon="🔐")
        
        provider_list = list(SMTP_PROVIDERS.keys())
        default_provider_idx = 0
        if smtp_defaults['provider'] in provider_list:
            default_provider_idx = provider_list.index(smtp_defaults['provider'])
        
        provider = st.selectbox(
            "메일 서비스", 
            provider_list, 
            index=default_provider_idx, 
            key="smtp_provider",
            help="사용할 SMTP 서버를 선택하세요"
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
            key="smtp_pass",
            help="2차 인증용 앱 비밀번호를 입력하세요"
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
                        st.success("연결 성공!", icon="✓")
                        server.quit()
                        st.session_state.smtp_config = config
                        if not from_secrets:
                            save_to_session(provider, final_username, final_password)
                    else:
                        st.error(f"{error}", icon="✗")
            else:
                st.warning("이메일과 비밀번호를 입력하세요", icon="⚠")
        
        if st.session_state.smtp_config:
            st.success("SMTP 준비 완료", icon="✓")
        
        st.divider()
        
        # 현재 상태 요약
        st.markdown("#### 현재 상태")
        
        if st.session_state.df is not None:
            st.metric("데이터 행", f"{len(st.session_state.df):,}")
        
        if st.session_state.grouped_data:
            valid = sum(1 for g in st.session_state.grouped_data.values() 
                       if g['recipient_email'] and validate_email(g['recipient_email']))
            total = len(st.session_state.grouped_data)
            st.metric("발송 가능", f"{valid}/{total}")
        
        st.divider()
        
        if st.button("처음부터 다시", use_container_width=True):
            reset_workflow()
            st.rerun()
        
        with st.expander("설정 가이드"):
            st.markdown("""
            **secrets.toml 설정**
            ```toml
            SMTP_ID = "email@company.com"
            SMTP_PW = "app_password"
            ```
            
            **보안 주의**  
            `.gitignore`에 추가하세요
            """)


def render_step1():
    """Step 1: 파일 업로드"""
    with st.container(border=True):
        st.markdown("##### 엑셀 파일 업로드")
        st.caption("정산서 데이터가 포함된 Excel 파일을 선택하세요")
        
        uploaded_file = st.file_uploader(
            "파일 선택", 
            type=['xlsx', 'xls', 'csv'],
            label_visibility="collapsed",
            help="xlsx, xls, csv 형식 지원"
        )
    
    if uploaded_file:
        xlsx, sheet_names, error = load_excel_file(uploaded_file)
        if error:
            st.error(error, icon="✗")
            return
        
        st.session_state.excel_file = xlsx
        st.session_state.sheet_names = sheet_names
        
        with st.container(border=True):
            st.markdown("##### 시트 선택")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**정산 데이터 시트**")
                data_sheet = st.selectbox(
                    "데이터 시트", 
                    sheet_names,
                    index=sheet_names.index('정산서') if '정산서' in sheet_names else 0,
                    label_visibility="collapsed",
                    help="정산 데이터가 있는 시트를 선택하세요"
                )
                st.session_state.selected_data_sheet = data_sheet
            
            with col2:
                st.markdown("**이메일 정보 시트**")
                use_separate = st.checkbox(
                    "별도 시트에 있음",
                    value=any('사업자' in s for s in sheet_names),
                    help="이메일 주소가 다른 시트에 있는 경우 체크"
                )
                st.session_state.use_separate_email_sheet = use_separate
                
                if use_separate:
                    email_sheets = [s for s in sheet_names if s != data_sheet]
                    if email_sheets:
                        default_idx = next((i for i, s in enumerate(email_sheets) if '사업자' in s), 0)
                        email_sheet = st.selectbox(
                            "이메일 시트", 
                            email_sheets, 
                            index=default_idx,
                            label_visibility="collapsed"
                        )
                        st.session_state.selected_email_sheet = email_sheet
        
        # 데이터 로드 및 미리보기
        if xlsx and data_sheet:
            df_data, err = load_sheet(xlsx, data_sheet)
            if not err and df_data is not None:
                st.session_state.df = df_data
                st.session_state.df_original = df_data.copy()
                
                with st.expander(f"데이터 미리보기 ({len(df_data):,}행)", expanded=False):
                    st.dataframe(df_data.head(10), use_container_width=True, hide_index=True)
        
        if use_separate and st.session_state.get('selected_email_sheet'):
            df_email, err = load_sheet(xlsx, st.session_state.selected_email_sheet)
            if not err and df_email is not None:
                st.session_state.df_email = df_email
                email_col_candidates = [c for c in df_email.columns if '이메일' in c or 'mail' in c.lower()]
                if email_col_candidates:
                    cnt = df_email[email_col_candidates[0]].notna().sum()
                    st.info(f"이메일 보유: {cnt}개 / 전체 {len(df_email)}개 업체", icon="📧")
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("다음 단계 →", type="primary", use_container_width=True):
                if st.session_state.df is not None:
                    st.session_state.current_step = 2
                    st.rerun()


def render_step2():
    """Step 2: 컬럼 설정"""
    df = st.session_state.df
    if df is None:
        st.warning("먼저 파일을 업로드하세요", icon="⚠")
        return
    
    columns = df.columns.tolist()
    df_email = st.session_state.df_email
    use_separate = st.session_state.use_separate_email_sheet
    
    # 데이터 병합 설정
    if use_separate and df_email is not None:
        with st.container(border=True):
            st.markdown("##### 데이터 병합 설정")
            st.caption("정산서와 이메일 시트를 연결할 컬럼을 선택하세요")
            
            email_columns = df_email.columns.tolist()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                join_data = [c for c in columns if any(k in c for k in ['CSO', '관리업체'])]
                join_col_data = st.selectbox(
                    "정산서 매칭 컬럼", 
                    columns,
                    index=columns.index(join_data[0]) if join_data else 0,
                    help="정산서에서 업체를 식별하는 컬럼"
                )
                st.session_state.join_col_data = join_col_data
            
            with col2:
                join_email = [c for c in email_columns if '거래처' in c]
                join_col_email = st.selectbox(
                    "이메일시트 매칭 컬럼", 
                    email_columns,
                    index=email_columns.index(join_email[0]) if join_email else 0,
                    help="이메일 시트에서 업체를 식별하는 컬럼"
                )
                st.session_state.join_col_email = join_col_email
            
            with col3:
                email_cols = [c for c in email_columns if '이메일' in c or 'mail' in c.lower()]
                email_col = st.selectbox(
                    "이메일 주소 컬럼", 
                    email_columns,
                    index=email_columns.index(email_cols[0]) if email_cols else 0,
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
            group_key_col = st.selectbox(
                "그룹화 기준 컬럼", 
                columns,
                index=columns.index(group_candidates[0]) if group_candidates else 0,
                help="이 컬럼 값이 같은 행들이 하나의 그룹이 됩니다"
            )
            st.session_state.group_key_col = group_key_col
        
        with col2:
            use_wildcard = st.checkbox(
                "와일드카드 그룹핑", 
                value=True,
                help="'에스투비'와 '에스투비 합계'를 같은 그룹으로 묶습니다"
            )
            st.session_state.use_wildcard_grouping = use_wildcard
        
        if use_wildcard:
            col1, col2 = st.columns(2)
            with col1:
                suffixes = st.text_input(
                    "접미사 패턴", 
                    " 합계, 합계",
                    help="쉼표로 구분하여 여러 패턴 입력 가능"
                )
                st.session_state.wildcard_suffixes = [s.strip() for s in suffixes.split(',') if s.strip()]
            with col2:
                calc_auto = st.checkbox(
                    "합계 자동 계산", 
                    value=False,
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
    
    # 데이터 타입 설정
    with st.container(border=True):
        st.markdown("##### 컬럼 타입 설정")
        st.caption("금액, 날짜, ID 컬럼을 지정하면 자동 포맷팅됩니다")
        
        col1, col2 = st.columns(2)
        
        with col1:
            amount_default = [c for c in columns if any(k in c for k in ['금액', '처방', '수수료'])]
            amount_cols = st.multiselect(
                "금액 컬럼", 
                columns, 
                default=amount_default,
                help="천단위 쉼표와 ₩ 기호가 적용됩니다"
            )
            st.session_state.amount_cols = amount_cols
        
        with col2:
            date_default = [c for c in columns if '월' in c or 'date' in c.lower()]
            date_cols = st.multiselect(
                "날짜 컬럼", 
                columns, 
                default=date_default,
                help="YYYY-MM-DD 형식으로 통일됩니다"
            )
            st.session_state.date_cols = date_cols
        
        id_default = [c for c in columns if '코드' in c or '번호' in c]
        id_cols = st.multiselect(
            "ID 컬럼", 
            columns, 
            default=id_default,
            help="숫자 끝의 .0이 제거됩니다"
        )
        st.session_state.id_cols = id_cols
    
    # 표시 컬럼 선택
    with st.container(border=True):
        st.markdown("##### 이메일 표시 컬럼")
        st.caption("이메일 본문 테이블에 표시할 컬럼을 순서대로 선택하세요")
        
        exclude = [group_key_col]
        default_display = [c for c in columns if c not in exclude][:8]
        display_cols = st.multiselect(
            "컬럼 선택", 
            columns, 
            default=default_display,
            label_visibility="collapsed"
        )
        st.session_state.display_cols = display_cols
    
    # 충돌 해결
    with st.container(border=True):
        st.markdown("##### 이메일 충돌 처리")
        st.caption("한 그룹에 여러 이메일이 있을 때 처리 방법")
        
        conflict_resolution = st.radio(
            "충돌 해결 방식",
            ['first', 'most_common', 'skip'],
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
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        if st.button("다음 단계 →", type="primary", use_container_width=True):
            if not display_cols:
                st.error("표시할 컬럼을 1개 이상 선택하세요", icon="✗")
            else:
                with st.spinner("데이터 처리 중..."):
                    df_work = df.copy()
                    
                    if use_separate and df_email is not None:
                        df_work = merge_email_data(df_work, df_email,
                            st.session_state.join_col_data,
                            st.session_state.join_col_email,
                            st.session_state.email_col)
                    
                    df_cleaned = clean_dataframe(df_work, amount_cols, date_cols, id_cols)
                    st.session_state.df = df_cleaned
                    
                    grouped, conflicts = group_data_with_wildcard(
                        df_cleaned, group_key_col, st.session_state.email_col,
                        amount_cols, display_cols, conflict_resolution,
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
    
    # 발송 대상 목록
    with st.container(border=True):
        st.markdown("##### 발송 대상 목록")
        
        valid_list = [(k, v) for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])]
        
        if valid_list:
            preview_df = pd.DataFrame([
                {'업체명': k, '이메일': v['recipient_email'], '데이터 행수': v['row_count']}
                for k, v in valid_list
            ])
            
            # 스타일링된 데이터프레임
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
    
    # 상세 검토
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
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**수신자:** `{g['recipient_email'] or '없음'}`")
            with col2:
                if g['has_conflict']:
                    st.warning(f"이메일 충돌: {', '.join(g['conflict_emails'])}", icon="⚠")
            
            st.dataframe(
                pd.DataFrame(g['rows']), 
                use_container_width=True, 
                hide_index=True,
                height=250
            )
    
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
    """Step 4: 템플릿 편집"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown("##### 템플릿 편집")
            st.caption("Jinja2 문법 사용 가능: {{ company_name }}, {{ period }}")
            
            subject = st.text_input(
                "이메일 제목", 
                st.session_state.subject_template,
                help="예: [한국유니온제약] {{ period }} 정산서"
            )
            st.session_state.subject_template = subject
            
            header = st.text_input(
                "헤더 타이틀", 
                st.session_state.header_title
            )
            st.session_state.header_title = header
            
            greeting = st.text_area(
                "인사말", 
                st.session_state.greeting_template, 
                height=80
            )
            st.session_state.greeting_template = greeting
            
            info = st.text_area(
                "정보 박스", 
                st.session_state.info_template, 
                height=60
            )
            st.session_state.info_template = info
            
            additional = st.text_area(
                "추가 메시지", 
                st.session_state.additional_template, 
                height=60
            )
            st.session_state.additional_template = additional
    
    with col2:
        with st.container(border=True):
            st.markdown("##### 미리보기")
            
            grouped = st.session_state.grouped_data
            valid_list = [(k, v) for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])]
            
            if valid_list:
                sample_key, sample_data = valid_list[0]
                templates = {
                    'subject': subject, 'header_title': header, 'greeting': greeting,
                    'info': info, 'additional': additional, 'footer': st.session_state.footer_template
                }
                try:
                    html = render_email_content(sample_key, sample_data,
                        st.session_state.display_cols, st.session_state.amount_cols, templates)
                    st.components.v1.html(html, height=400, scrolling=True)
                except Exception as e:
                    st.error(f"미리보기 오류: {e}", icon="✗")
            else:
                st.info("미리보기할 데이터가 없습니다", icon="ℹ")
    
    # 네비게이션
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    with col2:
        if st.button("다음 단계 →", type="primary", use_container_width=True):
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
    
    # 발송 설정
    with st.expander("발송 설정", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            batch_size = st.number_input(
                "배치 크기", 
                value=10, 
                min_value=1, 
                max_value=50,
                help="한 번에 발송할 이메일 수"
            )
        with col2:
            email_delay = st.number_input(
                "이메일 간격(초)", 
                value=2, 
                min_value=1, 
                max_value=10,
                help="각 이메일 사이 대기 시간"
            )
        with col3:
            batch_delay = st.number_input(
                "배치 간격(초)", 
                value=30, 
                min_value=5, 
                max_value=120,
                help="배치 완료 후 대기 시간"
            )
    
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
                    st.success(f"테스트 메일 발송 완료 → {config['username']}", icon="✓")
                else:
                    st.error(f"발송 실패: {err}", icon="✗")
            else:
                st.error(f"SMTP 연결 실패: {error}", icon="✗")
    
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
            st.error(f"SMTP 연결 실패: {error}", icon="✗")
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
                
                time.sleep(email_delay)
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
    render_header()
    render_step_indicator()
    render_smtp_sidebar()
    
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
