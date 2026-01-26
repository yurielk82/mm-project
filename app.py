"""
================================================================================
지능형 그룹핑 메일머지 시스템 (Intelligent Grouped Mail Merge System)
================================================================================
엑셀 데이터를 특정 Key를 기준으로 자동 그룹화하여,
각 그룹에 맞춤형 정산서 테이블을 포함한 이메일을 발송하는 엔터프라이즈 솔루션

Author: Senior Solution Architect (20 Years Experience)
Version: 2.3.0 - Secrets First + Session State Persistence
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
VERSION = "2.3.0"

# SMTP 설정 우선순위: st.secrets > session_state > 수동 입력

STEPS = ["파일 업로드", "컬럼 설정", "데이터 검토", "템플릿 편집", "발송"]

# SMTP 기본 설정
SMTP_PROVIDERS = {
    "Gmail": {"server": "smtp.gmail.com", "port": 587},
    "Naver": {"server": "smtp.naver.com", "port": 587},
    "Daum/Kakao": {"server": "smtp.daum.net", "port": 465},
    "Outlook": {"server": "smtp-mail.outlook.com", "port": 587},
    "Hiworks (하이웍스)": {"server": "smtps.hiworks.com", "port": 465},
    "직접 입력": {"server": "", "port": 587},
}

DEFAULT_BATCH_SIZE = 10
DEFAULT_EMAIL_DELAY = 2
DEFAULT_BATCH_DELAY = 30


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
        
        # 이메일 처리
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
        
        # 행 정렬 (합계 행이 마지막으로)
        def sort_key(row_val):
            return 1 if any(str(row_val).endswith(s) for s in wildcard_suffixes) else 0
        
        if use_wildcard:
            sorted_indices = group_df[group_key_col].apply(sort_key).sort_values().index
            group_df = group_df.loc[sorted_indices]
        
        # 행 데이터 준비
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
        
        # 합계 계산
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


def create_smtp_connection(config):
    try:
        if config['port'] == 465:
            server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=30)
        else:
            server = smtplib.SMTP(config['server'], config['port'], timeout=30)
            server.ehlo()
            if config.get('use_tls', True):
                server.starttls()
                server.ehlo()
        server.login(config['username'], config['password'])
        return server, None
    except smtplib.SMTPAuthenticationError:
        return None, "인증 실패: 이메일/비밀번호를 확인하세요."
    except Exception as e:
        return None, f"연결 오류: {str(e)}"


def send_email(server, sender, recipient, subject, html_content):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        server.sendmail(sender, recipient, msg.as_string())
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
# UI COMPONENTS
# ============================================================================

def render_header():
    """헤더"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                padding: 1.5rem 2rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
        <h2 style="margin: 0;">📨 {APP_TITLE}</h2>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">{APP_SUBTITLE}</p>
    </div>
    """, unsafe_allow_html=True)


def render_step_indicator():
    """단계 표시기"""
    current = st.session_state.current_step
    
    step_html = '<div style="display: flex; align-items: center; margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">'
    
    for i, step_name in enumerate(STEPS, 1):
        if i < current:
            color, bg = "#fff", "#28a745"
            icon = "✓"
        elif i == current:
            color, bg = "#fff", "#1e3c72"
            icon = str(i)
        else:
            color, bg = "#6c757d", "#e9ecef"
            icon = str(i)
        
        step_html += f'''
        <div style="display: flex; align-items: center; flex: 1;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: {bg}; color: {color};
                        display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px;">
                {icon}
            </div>
            <span style="margin-left: 8px; font-size: 13px; color: {'#1e3c72' if i == current else '#6c757d'}; font-weight: {'600' if i == current else '400'};">
                {step_name}
            </span>
        </div>
        '''
        if i < len(STEPS):
            step_html += '<div style="flex: 0.3; height: 2px; background: #dee2e6; margin: 0 10px;"></div>'
    
    step_html += '</div>'
    st.markdown(step_html, unsafe_allow_html=True)


def get_smtp_config() -> dict:
    """
    SMTP 설정을 가져오는 함수 (Secrets First 로직)
    
    우선순위:
    1. st.secrets (secrets.toml 또는 Streamlit Cloud Secrets)
    2. st.session_state (사용자가 수동 입력한 값)
    3. 빈 값 (사용자 입력 대기)
    
    Returns:
        dict: {'username': str, 'password': str, 'provider': str, 'from_secrets': bool}
    """
    config = {
        'username': '',
        'password': '',
        'provider': 'Hiworks (하이웍스)',
        'from_secrets': False
    }
    
    # 1. st.secrets에서 먼저 확인 (Secrets First)
    try:
        if 'SMTP_ID' in st.secrets and 'SMTP_PW' in st.secrets:
            config['username'] = st.secrets['SMTP_ID']
            config['password'] = st.secrets['SMTP_PW']
            config['from_secrets'] = True
            # 프로바이더도 secrets에 있으면 사용
            if 'SMTP_PROVIDER' in st.secrets:
                config['provider'] = st.secrets['SMTP_PROVIDER']
            return config
    except Exception:
        pass  # secrets 파일이 없으면 무시
    
    # 2. session_state에서 확인 (사용자 수동 입력값)
    if st.session_state.get('saved_smtp_user'):
        config['username'] = st.session_state.saved_smtp_user
        config['password'] = st.session_state.get('saved_smtp_pass', '')
        config['provider'] = st.session_state.get('saved_smtp_provider', 'Hiworks (하이웍스)')
    
    return config


def save_to_session(provider: str, username: str, password: str):
    """
    SMTP 자격증명을 session_state에 저장
    (앱 리프레시되어도 발송 전까지 유지)
    """
    st.session_state.saved_smtp_provider = provider
    st.session_state.saved_smtp_user = username
    st.session_state.saved_smtp_pass = password


def clear_session_credentials():
    """session_state에 저장된 자격증명 삭제"""
    for key in ['saved_smtp_provider', 'saved_smtp_user', 'saved_smtp_pass']:
        if key in st.session_state:
            del st.session_state[key]


def render_smtp_sidebar():
    """
    사이드바 SMTP 설정 (Secrets First + Session State)
    
    - st.secrets에 SMTP_ID, SMTP_PW가 있으면 자동으로 기본값 세팅
    - 없으면 사용자가 직접 입력 가능
    - 입력값은 session_state에 저장되어 리프레시 후에도 유지
    """
    with st.sidebar:
        st.markdown("### ⚙️ SMTP 설정")
        
        # Secrets First: 설정 로드
        smtp_defaults = get_smtp_config()
        from_secrets = smtp_defaults['from_secrets']
        
        # secrets에서 로드되었으면 표시
        if from_secrets:
            st.success("🔐 Secrets에서 자동 로드됨")
        
        # 프로바이더 선택
        provider_list = list(SMTP_PROVIDERS.keys())
        default_provider_idx = 0
        if smtp_defaults['provider'] in provider_list:
            default_provider_idx = provider_list.index(smtp_defaults['provider'])
        
        provider = st.selectbox("메일 서비스", provider_list, 
                               index=default_provider_idx, key="smtp_provider")
        
        # SMTP 서버/포트 설정
        if provider == "직접 입력":
            smtp_server = st.text_input("SMTP 서버", key="smtp_server_input")
            smtp_port = st.number_input("포트", value=587, key="smtp_port_input")
        else:
            smtp_server = SMTP_PROVIDERS[provider]["server"]
            smtp_port = SMTP_PROVIDERS[provider]["port"]
            st.caption(f"서버: {smtp_server}:{smtp_port}")
        
        # 이메일 입력 (secrets 또는 session_state 기본값)
        smtp_username = st.text_input(
            "이메일 (발신자)", 
            value=smtp_defaults['username'],
            key="smtp_user",
            disabled=from_secrets,  # secrets에서 로드되면 수정 불가
            help="secrets.toml에 SMTP_ID로 설정 가능"
        )
        
        # 비밀번호 입력 (type="password" 적용)
        smtp_password = st.text_input(
            "앱 비밀번호", 
            type="password",  # 글자 노출 방지
            value=smtp_defaults['password'],
            key="smtp_pass",
            disabled=from_secrets,  # secrets에서 로드되면 수정 불가
            help="2차 인증용 앱 비밀번호. secrets.toml에 SMTP_PW로 설정 가능"
        )
        
        # 연결 테스트 버튼
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("연결 테스트", use_container_width=True):
                # 실제 사용할 값 결정 (secrets 우선, 아니면 입력값)
                final_username = smtp_defaults['username'] if from_secrets else smtp_username
                final_password = smtp_defaults['password'] if from_secrets else smtp_password
                
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
                            st.success("✓ 연결 성공!")
                            server.quit()
                            st.session_state.smtp_config = config
                            # 연결 성공 시 session_state에 저장 (리프레시 후에도 유지)
                            if not from_secrets:
                                save_to_session(provider, final_username, final_password)
                        else:
                            st.error(f"연결 실패: {error}")
                else:
                    st.warning("이메일과 비밀번호를 입력하세요.")
        
        with col2:
            # secrets가 아닌 경우에만 저장 삭제 버튼 표시
            if not from_secrets and st.session_state.get('saved_smtp_user'):
                if st.button("저장 삭제", use_container_width=True, type="secondary"):
                    clear_session_credentials()
                    st.toast("저장된 정보가 삭제되었습니다.")
                    st.rerun()
        
        # SMTP 설정 완료 상태 표시
        if st.session_state.smtp_config:
            st.success("✓ SMTP 설정 완료")
        
        # 저장 상태 표시
        if not from_secrets and st.session_state.get('saved_smtp_user'):
            display_user = st.session_state.saved_smtp_user
            if len(display_user) > 20:
                display_user = display_user[:20] + '...'
            st.caption(f"💾 세션 저장: {display_user}")
        
        st.markdown("---")
        
        # 처음부터 다시 버튼
        if st.button("🔄 처음부터 다시", use_container_width=True):
            reset_workflow()
            st.rerun()
        
        st.markdown("---")
        
        # 현재 상태 표시
        st.markdown("### 📊 현재 상태")
        if st.session_state.df is not None:
            st.caption(f"📁 데이터: {len(st.session_state.df):,}행")
        if st.session_state.grouped_data:
            valid = sum(1 for g in st.session_state.grouped_data.values() 
                       if g['recipient_email'] and validate_email(g['recipient_email']))
            st.caption(f"📧 발송 가능: {valid}개 그룹")
        
        st.markdown("---")
        
        # 사용자 가이드 (secrets 설정 방법 안내)
        with st.expander("💡 SMTP 설정 가이드"):
            st.markdown("""
            **로컬 환경 (개발용)**
            
            `.streamlit/secrets.toml` 파일 생성:
            ```toml
            SMTP_ID = "your_email@example.com"
            SMTP_PW = "your_app_password"
            SMTP_PROVIDER = "Hiworks (하이웍스)"
            ```
            
            **Streamlit Cloud 배포 시**
            
            1. 앱 설정 → Secrets 메뉴
            2. 위와 동일한 형식으로 입력
            
            **지원 메일 서비스**
            - Gmail (앱 비밀번호 필요)
            - Naver
            - Daum/Kakao
            - Outlook
            - Hiworks (하이웍스)
            
            ⚠️ **보안 주의**: secrets.toml은 .gitignore에 추가하세요!
            """)


def render_step1():
    """Step 1: 파일 업로드"""
    st.markdown("### Step 1. 파일 업로드")
    
    uploaded_file = st.file_uploader("엑셀 파일 선택", type=['xlsx', 'xls', 'csv'],
                                     label_visibility="collapsed")
    
    if uploaded_file:
        xlsx, sheet_names, error = load_excel_file(uploaded_file)
        if error:
            st.error(error)
            return
        
        st.session_state.excel_file = xlsx
        st.session_state.sheet_names = sheet_names
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**정산 데이터 시트**")
            data_sheet = st.selectbox(
                "데이터 시트", sheet_names,
                index=sheet_names.index('정산서') if '정산서' in sheet_names else 0,
                label_visibility="collapsed"
            )
            st.session_state.selected_data_sheet = data_sheet
        
        with col2:
            st.markdown("**이메일 시트 (별도)**")
            use_separate = st.checkbox("이메일이 다른 시트에 있음",
                value=any('사업자' in s for s in sheet_names))
            st.session_state.use_separate_email_sheet = use_separate
            
            if use_separate:
                email_sheets = [s for s in sheet_names if s != data_sheet]
                if email_sheets:
                    default_idx = next((i for i, s in enumerate(email_sheets) if '사업자' in s), 0)
                    email_sheet = st.selectbox("이메일 시트", email_sheets, index=default_idx,
                                              label_visibility="collapsed")
                    st.session_state.selected_email_sheet = email_sheet
        
        # 시트 로드
        if xlsx and data_sheet:
            df_data, err = load_sheet(xlsx, data_sheet)
            if not err and df_data is not None:
                st.session_state.df = df_data
                st.session_state.df_original = df_data.copy()
                
                with st.expander(f"미리보기: {data_sheet} ({len(df_data):,}행)", expanded=False):
                    st.dataframe(df_data.head(10), use_container_width=True)
        
        if use_separate and st.session_state.get('selected_email_sheet'):
            df_email, err = load_sheet(xlsx, st.session_state.selected_email_sheet)
            if not err and df_email is not None:
                st.session_state.df_email = df_email
                email_col_candidates = [c for c in df_email.columns if '이메일' in c or 'mail' in c.lower()]
                if email_col_candidates:
                    cnt = df_email[email_col_candidates[0]].notna().sum()
                    st.info(f"이메일 보유 업체: {cnt}개 / {len(df_email)}개")
        
        st.markdown("---")
        if st.button("다음 →", type="primary", use_container_width=True):
            if st.session_state.df is not None:
                st.session_state.current_step = 2
                st.rerun()


def render_step2():
    """Step 2: 컬럼 설정"""
    st.markdown("### Step 2. 컬럼 설정")
    
    df = st.session_state.df
    if df is None:
        st.warning("먼저 파일을 업로드하세요.")
        return
    
    columns = df.columns.tolist()
    df_email = st.session_state.df_email
    use_separate = st.session_state.use_separate_email_sheet
    
    # 데이터 병합 설정
    if use_separate and df_email is not None:
        st.markdown("**데이터 병합 설정**")
        col1, col2, col3 = st.columns(3)
        email_columns = df_email.columns.tolist()
        
        with col1:
            join_data = [c for c in columns if any(k in c for k in ['CSO', '관리업체'])]
            join_col_data = st.selectbox("정산서 매칭 컬럼", columns,
                index=columns.index(join_data[0]) if join_data else 0)
            st.session_state.join_col_data = join_col_data
        
        with col2:
            join_email = [c for c in email_columns if '거래처' in c]
            join_col_email = st.selectbox("이메일시트 매칭 컬럼", email_columns,
                index=email_columns.index(join_email[0]) if join_email else 0)
            st.session_state.join_col_email = join_col_email
        
        with col3:
            email_cols = [c for c in email_columns if '이메일' in c or 'mail' in c.lower()]
            email_col = st.selectbox("이메일 컬럼", email_columns,
                index=email_columns.index(email_cols[0]) if email_cols else 0)
            st.session_state.email_col = email_col
        
        st.markdown("---")
    
    # 그룹화 설정
    st.markdown("**그룹화 설정**")
    col1, col2 = st.columns(2)
    
    with col1:
        group_candidates = [c for c in columns if 'CSO' in c or '관리업체' in c]
        group_key_col = st.selectbox("그룹화 기준 컬럼", columns,
            index=columns.index(group_candidates[0]) if group_candidates else 0)
        st.session_state.group_key_col = group_key_col
    
    with col2:
        use_wildcard = st.checkbox("와일드카드 그룹핑", value=True,
            help="'에스투비'와 '에스투비 합계'를 같은 그룹으로")
        st.session_state.use_wildcard_grouping = use_wildcard
    
    if use_wildcard:
        col1, col2 = st.columns(2)
        with col1:
            suffixes = st.text_input("접미사 패턴 (쉼표 구분)", " 합계, 합계")
            st.session_state.wildcard_suffixes = [s.strip() for s in suffixes.split(',') if s.strip()]
        with col2:
            calc_auto = st.checkbox("합계 자동 계산", value=False,
                help="체크 해제 시 기존 합계 행 값 사용")
            st.session_state.calculate_totals_auto = calc_auto
        
        # 그룹 미리보기
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
            st.success(f"예상 그룹 수: **{len(base_keys)}개**")
    
    st.markdown("---")
    
    # 데이터 타입 설정
    st.markdown("**데이터 타입**")
    col1, col2 = st.columns(2)
    
    with col1:
        amount_default = [c for c in columns if any(k in c for k in ['금액', '처방', '수수료'])]
        amount_cols = st.multiselect("금액 컬럼", columns, default=amount_default)
        st.session_state.amount_cols = amount_cols
    
    with col2:
        date_default = [c for c in columns if '월' in c or 'date' in c.lower()]
        date_cols = st.multiselect("날짜 컬럼", columns, default=date_default)
        st.session_state.date_cols = date_cols
    
    id_default = [c for c in columns if '코드' in c or '번호' in c]
    id_cols = st.multiselect("ID 컬럼 (소수점 제거)", columns, default=id_default)
    st.session_state.id_cols = id_cols
    
    st.markdown("---")
    
    # 표시 컬럼
    st.markdown("**이메일에 표시할 컬럼**")
    exclude = [group_key_col]
    default_display = [c for c in columns if c not in exclude][:8]
    display_cols = st.multiselect("컬럼 선택 (순서대로)", columns, default=default_display)
    st.session_state.display_cols = display_cols
    
    st.markdown("---")
    
    # 이메일 충돌
    conflict_resolution = st.radio("이메일 충돌 시", ['first', 'most_common', 'skip'],
        format_func=lambda x: {'first': '첫 번째 사용', 'most_common': '최다 사용', 'skip': '스킵'}[x],
        horizontal=True)
    st.session_state.conflict_resolution = conflict_resolution
    
    # 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        if st.button("다음 →", type="primary", use_container_width=True):
            if not display_cols:
                st.error("표시할 컬럼을 선택하세요.")
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
    st.markdown("### Step 3. 데이터 검토")
    
    grouped = st.session_state.grouped_data
    if not grouped:
        st.warning("그룹 데이터가 없습니다.")
        return
    
    # 통계
    total = len(grouped)
    valid = sum(1 for g in grouped.values() if g['recipient_email'] and validate_email(g['recipient_email']))
    no_email = total - valid
    
    col1, col2, col3 = st.columns(3)
    col1.metric("전체 그룹", total)
    col2.metric("발송 가능", valid)
    col3.metric("이메일 없음", no_email)
    
    # 발송 가능 목록
    st.markdown("**발송 대상**")
    valid_list = [(k, v) for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])]
    
    if valid_list:
        preview_df = pd.DataFrame([
            {'업체': k, '이메일': v['recipient_email'], '행수': v['row_count']}
            for k, v in valid_list[:30]
        ])
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
        if len(valid_list) > 30:
            st.caption(f"외 {len(valid_list)-30}개...")
    
    # 상세 검토
    st.markdown("---")
    st.markdown("**상세 검토**")
    selected = st.selectbox("그룹 선택", list(grouped.keys()),
        format_func=lambda x: f"{x} ({grouped[x]['row_count']}행)")
    
    if selected:
        g = grouped[selected]
        st.markdown(f"수신자: **{g['recipient_email'] or '없음'}**")
        st.dataframe(pd.DataFrame(g['rows']), use_container_width=True, hide_index=True)
    
    # 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    with col2:
        if st.button("다음 →", type="primary", use_container_width=True, disabled=valid==0):
            st.session_state.current_step = 4
            st.rerun()


def render_step4():
    """Step 4: 템플릿"""
    st.markdown("### Step 4. 이메일 템플릿")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**템플릿 편집**")
        subject = st.text_input("제목", st.session_state.subject_template)
        st.session_state.subject_template = subject
        
        header = st.text_input("헤더", st.session_state.header_title)
        st.session_state.header_title = header
        
        greeting = st.text_area("인사말", st.session_state.greeting_template, height=100)
        st.session_state.greeting_template = greeting
        
        info = st.text_area("정보 박스", st.session_state.info_template, height=80)
        st.session_state.info_template = info
        
        additional = st.text_area("추가 메시지", st.session_state.additional_template, height=60)
        st.session_state.additional_template = additional
    
    with col2:
        st.markdown("**미리보기**")
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
                st.components.v1.html(html, height=500, scrolling=True)
            except Exception as e:
                st.error(f"미리보기 오류: {e}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    with col2:
        if st.button("다음 →", type="primary", use_container_width=True):
            st.session_state.current_step = 5
            st.rerun()


def render_step5():
    """Step 5: 발송"""
    st.markdown("### Step 5. 이메일 발송")
    
    grouped = st.session_state.grouped_data
    valid_groups = {k: v for k, v in grouped.items() if v['recipient_email'] and validate_email(v['recipient_email'])}
    
    col1, col2 = st.columns(2)
    col1.metric("발송 대상", f"{len(valid_groups)}건")
    
    if not st.session_state.smtp_config:
        st.warning("사이드바에서 SMTP 설정을 먼저 완료하세요.")
    
    # 발송 설정
    with st.expander("발송 설정"):
        c1, c2, c3 = st.columns(3)
        batch_size = c1.number_input("배치 크기", value=10, min_value=1)
        email_delay = c2.number_input("이메일 간격(초)", value=2, min_value=1)
        batch_delay = c3.number_input("배치 간격(초)", value=30, min_value=5)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()
    
    with col2:
        test_btn = st.button("테스트 발송", use_container_width=True,
                            disabled=not st.session_state.smtp_config)
    
    with col3:
        send_btn = st.button("전체 발송", type="primary", use_container_width=True,
                            disabled=not st.session_state.smtp_config or len(valid_groups)==0)
    
    templates = {
        'subject': st.session_state.subject_template,
        'header_title': st.session_state.header_title,
        'greeting': st.session_state.greeting_template,
        'info': st.session_state.info_template,
        'additional': st.session_state.additional_template,
        'footer': st.session_state.footer_template
    }
    
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
                    st.success(f"✓ 테스트 메일 발송 완료 → {config['username']}")
                else:
                    st.error(f"발송 실패: {err}")
            else:
                st.error(error)
    
    if send_btn and st.session_state.smtp_config and valid_groups:
        config = st.session_state.smtp_config
        
        progress = st.progress(0)
        status = st.empty()
        
        results = []
        success_cnt = fail_cnt = 0
        total = len(valid_groups)
        
        server, error = create_smtp_connection(config)
        if not server:
            st.error(error)
        else:
            for i, (gk, gd) in enumerate(valid_groups.items()):
                progress.progress((i+1)/total)
                status.text(f"발송 중... {i+1}/{total}")
                
                try:
                    html = render_email_content(gk, gd, st.session_state.display_cols,
                        st.session_state.amount_cols, templates)
                    subject = Template(templates['subject']).render(company_name=gk,
                        period=datetime.now().strftime('%Y년 %m월'))
                    
                    ok, err = send_email(server, config['username'], gd['recipient_email'], subject, html)
                    
                    if ok:
                        success_cnt += 1
                        results.append({'그룹': gk, '이메일': gd['recipient_email'], '상태': '성공'})
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
            
            status.text("발송 완료!")
            if fail_cnt == 0:
                st.success(f"🎉 전체 발송 완료! ({success_cnt}건)")
            else:
                st.warning(f"완료: 성공 {success_cnt}, 실패 {fail_cnt}")
    
    # 결과 리포트
    if st.session_state.send_results:
        st.markdown("---")
        st.markdown("**발송 결과**")
        results_df = pd.DataFrame(st.session_state.send_results)
        st.dataframe(results_df, use_container_width=True, hide_index=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            results_df.to_excel(writer, index=False)
        
        st.download_button("결과 다운로드", output.getvalue(),
            f"발송결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📨", layout="wide")
    
    init_session_state()
    render_header()
    render_step_indicator()
    render_smtp_sidebar()
    
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
