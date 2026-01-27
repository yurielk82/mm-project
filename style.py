"""
================================================================================
📧 Enterprise Email Template & Styling Module
================================================================================
Gmail/Outlook 호환 Inline CSS 스타일 및 Jinja2 HTML 템플릿을 제공합니다.

Author: Senior Solution Architect (20 Years Experience)
Version: 1.0.0
================================================================================
"""

from typing import Dict, List, Optional
from jinja2 import Template, Environment, BaseLoader
import html

# ============================================================================
# 🎨 CSS STYLES (Inline for Email Compatibility)
# ============================================================================

# 이메일 클라이언트별 호환성을 위해 모든 스타일은 inline으로 적용됩니다.
EMAIL_STYLES = {
    # 전체 컨테이너
    "container": """
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f8f9fa;
    """,
    
    # 헤더 영역
    "header": """
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-color: #667eea;
        color: white;
        padding: 30px;
        border-radius: 10px 10px 0 0;
        text-align: center;
    """,
    
    # 헤더 타이틀
    "header_title": """
        margin: 0;
        font-size: 28px;
        font-weight: bold;
        color: white;
    """,
    
    # 헤더 서브타이틀
    "header_subtitle": """
        margin: 10px 0 0 0;
        font-size: 14px;
        color: rgba(255,255,255,0.9);
    """,
    
    # 본문 컨테이너
    "body_container": """
        background-color: white;
        padding: 30px;
        border-left: 1px solid #e9ecef;
        border-right: 1px solid #e9ecef;
    """,
    
    # 인사말 영역
    "greeting": """
        font-size: 16px;
        color: #333;
        line-height: 1.8;
        margin-bottom: 25px;
    """,
    
    # 정보 박스
    "info_box": """
        background-color: #e8f4fd;
        border-left: 4px solid #2196F3;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 5px 5px 0;
    """,
    
    # 테이블 컨테이너
    "table_container": """
        margin: 25px 0;
        overflow-x: auto;
    """,
    
    # 메인 데이터 테이블
    "table": """
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    """,
    
    # 테이블 헤더
    "th": """
        background-color: #495057;
        color: white;
        padding: 14px 12px;
        text-align: left;
        font-weight: 600;
        border: 1px solid #495057;
        white-space: nowrap;
    """,
    
    # 테이블 헤더 (금액)
    "th_amount": """
        background-color: #495057;
        color: white;
        padding: 14px 12px;
        text-align: right;
        font-weight: 600;
        border: 1px solid #495057;
        white-space: nowrap;
    """,
    
    # 테이블 데이터 셀 (일반)
    "td": """
        padding: 12px;
        border: 1px solid #dee2e6;
        color: #333;
    """,
    
    # 테이블 데이터 셀 (금액 - 우측 정렬)
    "td_amount": """
        padding: 12px;
        border: 1px solid #dee2e6;
        color: #333;
        text-align: right;
        font-family: 'Consolas', 'Monaco', monospace;
    """,
    
    # 짝수 행 배경 (Striped)
    "tr_even": """
        background-color: #f8f9fa;
    """,
    
    # 홀수 행 배경
    "tr_odd": """
        background-color: white;
    """,
    
    # 합계 행
    "tr_total": """
        background-color: #fff3cd;
        font-weight: bold;
    """,
    
    # 합계 셀
    "td_total": """
        padding: 14px 12px;
        border: 2px solid #ffc107;
        color: #856404;
        font-weight: bold;
    """,
    
    # 합계 금액 셀
    "td_total_amount": """
        padding: 14px 12px;
        border: 2px solid #ffc107;
        color: #856404;
        font-weight: bold;
        text-align: right;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 15px;
    """,
    
    # 푸터 영역
    "footer": """
        background-color: #f1f3f4;
        padding: 25px 30px;
        border-radius: 0 0 10px 10px;
        border: 1px solid #e9ecef;
        border-top: none;
    """,
    
    # 푸터 텍스트
    "footer_text": """
        font-size: 13px;
        color: #6c757d;
        line-height: 1.6;
        margin: 0;
    """,
    
    # 경고 박스
    "warning_box": """
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-left: 4px solid #ffc107;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 5px 5px 0;
        color: #856404;
    """,
    
    # 성공 박스
    "success_box": """
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-left: 4px solid #28a745;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 5px 5px 0;
        color: #155724;
    """,
}


# ============================================================================
# 📝 HTML TEMPLATES
# ============================================================================

# 메인 이메일 템플릿 (Jinja2)
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8f9fa;">
    <div style="{{ styles.container }}">
        <!-- 헤더 -->
        <div style="{{ styles.header }}">
            <h1 style="{{ styles.header_title }}">{{ header_title }}</h1>
            {% if header_subtitle %}
            <p style="{{ styles.header_subtitle }}">{{ header_subtitle }}</p>
            {% endif %}
        </div>
        
        <!-- 본문 -->
        <div style="{{ styles.body_container }}">
            <!-- 인사말 -->
            <div style="{{ styles.greeting }}">
                {{ greeting | safe }}
            </div>
            
            {% if info_message %}
            <!-- 정보 박스 -->
            <div style="{{ styles.info_box }}">
                {{ info_message | safe }}
            </div>
            {% endif %}
            
            <!-- 데이터 테이블 -->
            <div style="{{ styles.table_container }}">
                <table style="{{ styles.table }}">
                    <thead>
                        <tr>
                            {% for col in columns %}
                            {% if col in amount_columns %}
                            <th style="{{ styles.th_amount }}">{{ col }}</th>
                            {% else %}
                            <th style="{{ styles.th }}">{{ col }}</th>
                            {% endif %}
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in rows %}
                        <tr style="{{ styles.tr_even if loop.index is even else styles.tr_odd }}">
                            {% for col in columns %}
                            {% if col in amount_columns %}
                            <td style="{{ styles.td_amount }}">{{ row[col] }}</td>
                            {% else %}
                            <td style="{{ styles.td }}">{{ row[col] }}</td>
                            {% endif %}
                            {% endfor %}
                        </tr>
                        {% endfor %}
                        
                        <!-- 합계 행 -->
                        {% if totals %}
                        <tr style="{{ styles.tr_total }}">
                            <td style="{{ styles.td_total }}" colspan="{{ non_amount_count }}">합계 (Total)</td>
                            {% for col in amount_columns %}
                            <td style="{{ styles.td_total_amount }}">{{ totals[col] }}</td>
                            {% endfor %}
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
            
            {% if additional_message %}
            <!-- 추가 메시지 -->
            <div style="{{ styles.greeting }}">
                {{ additional_message | safe }}
            </div>
            {% endif %}
        </div>
        
        <!-- 푸터 -->
        <div style="{{ styles.footer }}">
            <p style="{{ styles.footer_text }}">
                {{ footer_text | safe }}
            </p>
        </div>
    </div>
</body>
</html>
"""


# 미리보기용 간소화된 템플릿
PREVIEW_TEMPLATE = """
<div style="font-family: 'Malgun Gothic', Arial, sans-serif; padding: 20px; background: #f5f5f5; border-radius: 8px;">
    <h3 style="color: #333; margin-top: 0;">📧 이메일 미리보기</h3>
    <hr style="border: none; border-top: 1px solid #ddd;">
    <p><strong>수신자:</strong> {{ recipient_email }}</p>
    <p><strong>제목:</strong> {{ subject }}</p>
    <hr style="border: none; border-top: 1px solid #ddd;">
    <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
        {{ content | safe }}
    </div>
</div>
"""


# ============================================================================
# 🔧 TEMPLATE FUNCTIONS
# ============================================================================

def get_styles() -> Dict[str, str]:
    """
    이메일 스타일 딕셔너리를 반환합니다.
    Jinja2 템플릿에서 {{ styles.xxx }} 형태로 사용됩니다.
    """
    # 줄바꿈과 불필요한 공백 제거 (inline style로 사용하기 위함)
    cleaned_styles = {}
    for key, value in EMAIL_STYLES.items():
        # 멀티라인 스타일을 한 줄로 정리
        cleaned = ' '.join(value.split())
        cleaned_styles[key] = cleaned
    return cleaned_styles


def render_email(
    subject: str,
    header_title: str,
    greeting: str,
    columns: List[str],
    rows: List[Dict],
    amount_columns: List[str],
    totals: Optional[Dict[str, str]] = None,
    header_subtitle: Optional[str] = None,
    info_message: Optional[str] = None,
    additional_message: Optional[str] = None,
    footer_text: Optional[str] = None
) -> str:
    """
    이메일 HTML을 렌더링합니다.
    
    Args:
        subject: 이메일 제목
        header_title: 헤더에 표시될 제목
        greeting: 인사말 (HTML 허용)
        columns: 테이블 컬럼 목록
        rows: 테이블 데이터 (딕셔너리 리스트)
        amount_columns: 금액 컬럼 목록 (우측 정렬됨)
        totals: 합계 데이터 (금액 컬럼별)
        header_subtitle: 헤더 부제목
        info_message: 정보 박스 메시지
        additional_message: 테이블 아래 추가 메시지
        footer_text: 푸터 텍스트
    
    Returns:
        렌더링된 HTML 문자열
    """
    template = Template(EMAIL_TEMPLATE)
    
    # 금액 컬럼이 아닌 컬럼 수 계산 (합계 행의 colspan용)
    non_amount_count = len([c for c in columns if c not in amount_columns])
    
    # 기본 푸터 텍스트
    if footer_text is None:
        footer_text = """
        본 메일은 자동 발송된 메일입니다.<br>
        문의사항이 있으시면 담당자에게 연락 바랍니다.<br>
        <br>
        <small>© 2024 Intelligent Mail Merge System. All rights reserved.</small>
        """
    
    return template.render(
        subject=subject,
        header_title=header_title,
        header_subtitle=header_subtitle,
        greeting=greeting,
        info_message=info_message,
        columns=columns,
        rows=rows,
        amount_columns=amount_columns,
        totals=totals,
        non_amount_count=non_amount_count,
        additional_message=additional_message,
        footer_text=footer_text,
        styles=get_styles()
    )


def render_preview(
    recipient_email: str,
    subject: str,
    content: str
) -> str:
    """
    이메일 미리보기 HTML을 렌더링합니다.
    
    Args:
        recipient_email: 수신자 이메일
        subject: 이메일 제목
        content: 이메일 본문 HTML
    
    Returns:
        미리보기용 HTML 문자열
    """
    template = Template(PREVIEW_TEMPLATE)
    return template.render(
        recipient_email=recipient_email,
        subject=subject,
        content=content
    )


def format_currency(value, symbol: str = "", decimal_places: int = 0, zero_as_blank: bool = False) -> str:
    """
    숫자를 통화 형식으로 포맷팅합니다 (천단위 쉼표, 기호 없음).
    
    Args:
        value: 숫자 값
        symbol: 통화 기호 (기본: 없음)
        decimal_places: 소수점 자릿수
        zero_as_blank: True면 NaN/0을 빈칸으로, False면 0으로 표시
    
    Returns:
        포맷팅된 문자열 (예: 1,250,000)
    """
    import math
    
    try:
        # None, 빈 문자열, NaN 체크
        if value is None or value == '' or str(value).strip() == '':
            return '' if zero_as_blank else '0'
        
        # 문자열 'nan', 'NaN' 등 체크
        str_val = str(value).strip().lower()
        if str_val in ['nan', 'none', 'nat', '']:
            return '' if zero_as_blank else '0'
        
        num = float(str(value).replace(',', '').replace('₩', '').strip())
        
        # NaN 체크 (float형 NaN)
        if math.isnan(num):
            return '' if zero_as_blank else '0'
        
        # 0 체크
        if num == 0:
            return '' if zero_as_blank else '0'
        
        if decimal_places > 0:
            formatted = f"{num:,.{decimal_places}f}"
        else:
            formatted = f"{int(num):,}"
        
        if symbol:
            return f"{symbol}{formatted}"
        return formatted
    except (ValueError, TypeError):
        return str(value) if str(value).strip() else ('' if zero_as_blank else '0')


def format_percent(value, decimal_places: int = 1) -> str:
    """
    숫자를 퍼센트 형식으로 포맷팅합니다.
    
    Args:
        value: 숫자 값 (0.15 -> 15%, 15 -> 15%)
        decimal_places: 소수점 자릿수
    
    Returns:
        포맷팅된 문자열 (예: 15.0%)
    """
    try:
        if value is None or value == '' or str(value).strip() == '':
            return '-'
        
        num = float(str(value).replace(',', '').replace('%', '').strip())
        
        # 이미 퍼센트 값인지 확인 (1 이상이면 그대로, 미만이면 *100)
        # 예: 0.15 -> 15%, 15 -> 15%
        if -1 < num < 1 and num != 0:
            num = num * 100
        
        return f"{num:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return str(value)


def clean_id_column(value) -> str:
    """
    ID 컬럼에서 소수점(.0)을 제거합니다.
    Excel에서 숫자로 저장된 코드값의 .0을 제거합니다.
    
    Args:
        value: 원본 값
    
    Returns:
        정리된 문자열
    """
    try:
        if value is None:
            return ''
        
        str_val = str(value).strip()
        
        # .0으로 끝나는 경우 제거
        if str_val.endswith('.0'):
            str_val = str_val[:-2]
        
        return str_val
    except:
        return str(value)


def format_date(value, output_format: str = "%Y-%m-%d") -> str:
    """
    다양한 날짜 형식을 YYYY-MM-DD로 통일합니다.
    
    Args:
        value: 날짜 값 (문자열 또는 datetime)
        output_format: 출력 형식
    
    Returns:
        포맷팅된 날짜 문자열
    """
    import pandas as pd
    from datetime import datetime
    
    try:
        if value is None or str(value).strip() == '' or pd.isna(value):
            return '-'
        
        # 이미 datetime 객체인 경우
        if isinstance(value, datetime):
            return value.strftime(output_format)
        
        # pandas Timestamp인 경우
        if isinstance(value, pd.Timestamp):
            return value.strftime(output_format)
        
        # 문자열인 경우 파싱 시도
        str_val = str(value).strip()
        
        # 다양한 날짜 형식 시도
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y.%m.%d",
            "%d.%m.%Y",
            "%Y%m%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(str_val, fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue
        
        # pandas의 to_datetime으로 최종 시도
        try:
            dt = pd.to_datetime(str_val)
            return dt.strftime(output_format)
        except:
            pass
        
        return str_val
        
    except Exception:
        return str(value)


# ============================================================================
# 🎨 STREAMLIT UI STYLES
# ============================================================================

STREAMLIT_CUSTOM_CSS = """
<style>
    /* 메인 헤더 스타일 */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* 단계 표시기 */
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
    
    .step {
        flex: 1;
        text-align: center;
        padding: 1rem;
        position: relative;
    }
    
    .step.active {
        background: #667eea;
        color: white;
        border-radius: 8px;
    }
    
    .step.completed {
        background: #28a745;
        color: white;
        border-radius: 8px;
    }
    
    /* 카드 스타일 */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* 상태 배지 */
    .badge-success {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    
    .badge-warning {
        background: #ffc107;
        color: #333;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    
    .badge-danger {
        background: #dc3545;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    
    /* 통계 카드 */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    .stat-label {
        opacity: 0.9;
        font-size: 0.9rem;
    }
    
    /* 경고 박스 */
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0 5px 5px 0;
        margin: 1rem 0;
    }
    
    /* 성공 박스 */
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0 5px 5px 0;
        margin: 1rem 0;
    }
    
    /* 테이블 개선 */
    .dataframe {
        font-size: 0.9rem !important;
    }
    
    /* 버튼 스타일 개선 */
    .stButton > button {
        width: 100%;
    }
</style>
"""


def get_step_indicator_html(current_step: int, steps: List[str]) -> str:
    """
    단계 표시기 HTML을 생성합니다.
    
    Args:
        current_step: 현재 단계 (1부터 시작)
        steps: 단계 이름 목록
    
    Returns:
        단계 표시기 HTML
    """
    html_parts = ['<div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">']
    
    for i, step_name in enumerate(steps, 1):
        if i < current_step:
            status = "completed"
            bg_color = "#28a745"
            icon = "✓"
        elif i == current_step:
            status = "active"
            bg_color = "#667eea"
            icon = str(i)
        else:
            status = "pending"
            bg_color = "#e9ecef"
            icon = str(i)
        
        text_color = "white" if status in ["completed", "active"] else "#6c757d"
        
        html_parts.append(f'''
            <div style="flex: 1; text-align: center; margin: 0 5px;">
                <div style="
                    background: {bg_color};
                    color: {text_color};
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                ">{icon}</div>
                <div style="font-size: 0.85rem; color: {'#333' if status == 'active' else '#6c757d'};">
                    {step_name}
                </div>
            </div>
        ''')
    
    html_parts.append('</div>')
    return ''.join(html_parts)


# ============================================================================
# 📧 DEFAULT TEMPLATE CONTENT
# ============================================================================

DEFAULT_HEADER_TITLE = "정산 내역 안내"
DEFAULT_HEADER_SUBTITLE = "Settlement Statement"

DEFAULT_GREETING = """
안녕하세요, <strong>{{ company_name }}</strong> 담당자님.

아래와 같이 정산 내역을 안내드립니다.
자세한 내용은 아래 표를 확인해 주시기 바랍니다.
"""

DEFAULT_INFO_MESSAGE = """
<strong>📅 정산 기간:</strong> {{ period }}<br>
<strong>🏢 업체코드:</strong> {{ company_code }}
"""

DEFAULT_ADDITIONAL_MESSAGE = """
위 내용에 이상이 있으시면 회신 부탁드립니다.<br>
감사합니다.
"""

DEFAULT_FOOTER_TEXT = """
본 메일은 자동 발송된 메일입니다.<br>
문의사항이 있으시면 담당자에게 연락 바랍니다.<br>
<br>
<small>© 2024 Intelligent Mail Merge System. All rights reserved.</small>
"""

DEFAULT_SUBJECT_TEMPLATE = "[정산안내] {{ company_name }} {{ period }} 정산 내역"


if __name__ == "__main__":
    # 테스트 코드
    print("=== Email Template Module Test ===")
    print(f"Styles loaded: {len(EMAIL_STYLES)} items")
    print(f"Format currency test: {format_currency(1250000)}")
    print(f"Clean ID test: {clean_id_column('12345.0')}")
    print(f"Format date test: {format_date('2024/03/15')}")
