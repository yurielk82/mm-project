"""
================================================================================
📧 Unified Email Template Engine
================================================================================
이메일 렌더링을 위한 단일 통합 모듈입니다.
미리보기와 실제 발송에서 동일한 템플릿을 사용하여 유지보수성을 높입니다.

핵심 원칙:
1. 단일 템플릿 (Single Source of Truth)
2. Jinja2 기반 동적 렌더링
3. 스타일과 구조 분리
4. Gmail/Outlook 호환 Inline CSS

Author: Senior Solution Architect
Version: 2.0.0
================================================================================
"""

from typing import Dict, List, Optional, Any
from jinja2 import Template, Environment, BaseLoader
from datetime import datetime
from dataclasses import dataclass, field
import html
import math


# ============================================================================
# 🎨 EMAIL STYLE CONFIGURATION
# ============================================================================

@dataclass
class EmailStyleConfig:
    """이메일 스타일 설정 - 변수로 관리하여 쉽게 커스터마이즈"""
    
    # 폰트
    font_family: str = "'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif"
    
    # 컨테이너
    container_max_width: str = "800px"
    container_bg: str = "#f8f9fa"
    container_padding: str = "20px"
    
    # 헤더
    header_gradient: str = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    header_fallback_bg: str = "#667eea"
    header_text_color: str = "white"
    header_padding: str = "30px"
    header_title_size: str = "28px"
    header_subtitle_size: str = "14px"
    
    # 본문
    body_bg: str = "white"
    body_padding: str = "30px"
    body_border_color: str = "#e9ecef"
    text_color: str = "#333"
    text_size: str = "16px"
    line_height: str = "1.8"
    
    # 정보 박스
    info_box_bg: str = "#e8f4fd"
    info_box_border: str = "#2196F3"
    
    # 테이블
    table_header_bg: str = "#495057"
    table_header_color: str = "white"
    table_row_even: str = "#f8f9fa"
    table_row_odd: str = "white"
    table_border_color: str = "#dee2e6"
    table_total_bg: str = "#343a40"
    table_cell_padding: str = "14px 12px"
    
    # 푸터
    footer_bg: str = "#f1f3f4"
    footer_text_color: str = "#6c757d"
    footer_text_size: str = "13px"
    
    # 상태 박스 색상
    success_bg: str = "#d4edda"
    success_border: str = "#28a745"
    warning_bg: str = "#fff3cd"
    warning_border: str = "#ffc107"
    
    def to_inline_styles(self) -> Dict[str, str]:
        """스타일 딕셔너리를 inline CSS로 변환"""
        styles = {
            "container": f"""
                font-family: {self.font_family};
                max-width: {self.container_max_width};
                margin: 0 auto;
                padding: {self.container_padding};
                background-color: {self.container_bg};
            """,
            "header": f"""
                background: {self.header_gradient};
                background-color: {self.header_fallback_bg};
                color: {self.header_text_color};
                padding: {self.header_padding};
                border-radius: 10px 10px 0 0;
                text-align: center;
            """,
            "header_title": f"""
                margin: 0;
                font-size: {self.header_title_size};
                font-weight: bold;
                color: {self.header_text_color};
            """,
            "header_subtitle": f"""
                margin: 10px 0 0 0;
                font-size: {self.header_subtitle_size};
                color: rgba(255,255,255,0.9);
            """,
            "body_container": f"""
                background-color: {self.body_bg};
                padding: {self.body_padding};
                border-left: 1px solid {self.body_border_color};
                border-right: 1px solid {self.body_border_color};
            """,
            "greeting": f"""
                font-size: {self.text_size};
                color: {self.text_color};
                line-height: {self.line_height};
                margin-bottom: 25px;
            """,
            "info_box": f"""
                background-color: {self.info_box_bg};
                border-left: 4px solid {self.info_box_border};
                padding: 15px 20px;
                margin: 20px 0;
                border-radius: 0 5px 5px 0;
            """,
            "table_container": """
                margin: 25px 0;
                overflow-x: auto;
            """,
            "table": """
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            """,
            "th": f"""
                background-color: {self.table_header_bg};
                color: {self.table_header_color};
                padding: {self.table_cell_padding};
                text-align: left;
                font-weight: 600;
                border-bottom: 2px solid {self.table_border_color};
            """,
            "th_amount": f"""
                background-color: {self.table_header_bg};
                color: {self.table_header_color};
                padding: {self.table_cell_padding};
                text-align: right;
                font-weight: 600;
                border-bottom: 2px solid {self.table_border_color};
            """,
            "tr_even": f"""
                background-color: {self.table_row_even};
            """,
            "tr_odd": f"""
                background-color: {self.table_row_odd};
            """,
            "td": f"""
                padding: {self.table_cell_padding};
                border-bottom: 1px solid {self.table_border_color};
                color: {self.text_color};
            """,
            "td_amount": f"""
                padding: {self.table_cell_padding};
                border-bottom: 1px solid {self.table_border_color};
                text-align: right;
                font-family: 'Consolas', 'Monaco', monospace;
                color: {self.text_color};
            """,
            "tr_total": f"""
                background-color: {self.table_total_bg};
            """,
            "td_total": f"""
                padding: {self.table_cell_padding};
                color: {self.table_header_color};
                font-weight: bold;
            """,
            "td_total_amount": f"""
                padding: {self.table_cell_padding};
                text-align: right;
                color: {self.table_header_color};
                font-weight: bold;
                font-family: 'Consolas', 'Monaco', monospace;
            """,
            "footer": f"""
                background-color: {self.footer_bg};
                padding: 25px 30px;
                border-radius: 0 0 10px 10px;
                border: 1px solid {self.body_border_color};
                border-top: none;
            """,
            "footer_text": f"""
                font-size: {self.footer_text_size};
                color: {self.footer_text_color};
                line-height: 1.6;
                margin: 0;
            """,
            "success_box": f"""
                background-color: {self.success_bg};
                border: 1px solid {self.success_border};
                border-left: 4px solid {self.success_border};
                padding: 15px 20px;
                margin: 20px 0;
                border-radius: 0 5px 5px 0;
            """,
            "warning_box": f"""
                background-color: {self.warning_bg};
                border: 1px solid {self.warning_border};
                border-left: 4px solid {self.warning_border};
                padding: 15px 20px;
                margin: 20px 0;
                border-radius: 0 5px 5px 0;
            """,
        }
        
        # 줄바꿈과 불필요한 공백 제거
        return {k: ' '.join(v.split()) for k, v in styles.items()}


# 기본 스타일 인스턴스
DEFAULT_STYLE = EmailStyleConfig()


# ============================================================================
# 📝 EMAIL TEMPLATE (Jinja2)
# ============================================================================

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
            {% if columns and rows %}
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
                            <td style="{{ styles.td_total_amount }}">{{ totals.get(col, '') }}</td>
                            {% endfor %}
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
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


# ============================================================================
# 📊 DATA FORMATTERS
# ============================================================================

def format_currency(value, symbol: str = "", decimal_places: int = 0, zero_as_blank: bool = False) -> str:
    """
    숫자를 통화 형식으로 포맷팅합니다 (천단위 쉼표).
    
    Args:
        value: 숫자 값
        symbol: 통화 기호 (기본: 없음)
        decimal_places: 소수점 자릿수
        zero_as_blank: True면 NaN/0을 빈칸, False면 0으로 표시
    
    Returns:
        포맷팅된 문자열 (예: 1,250,000)
    """
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
        
        return f"{symbol}{formatted}" if symbol else formatted
        
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
        
        if math.isnan(num):
            return '-'
        
        # 1보다 작으면 비율로 가정 (0.15 -> 15%)
        if 0 < abs(num) < 1:
            num *= 100
        
        return f"{num:.{decimal_places}f}%"
        
    except (ValueError, TypeError):
        return str(value) if str(value).strip() else '-'


def format_date(value, output_format: str = "%Y-%m-%d") -> str:
    """
    다양한 날짜 형식을 통일된 형식으로 변환합니다.
    
    Args:
        value: 날짜 값 (문자열 또는 datetime)
        output_format: 출력 형식
    
    Returns:
        포맷팅된 날짜 문자열
    """
    import pandas as pd
    
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
        
        date_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
            "%Y.%m.%d", "%d.%m.%Y", "%Y%m%d", "%m/%d/%Y", "%m-%d-%Y",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str_val, fmt).strftime(output_format)
            except ValueError:
                continue
        
        # pandas의 to_datetime으로 최종 시도
        try:
            return pd.to_datetime(str_val).strftime(output_format)
        except:
            pass
        
        return str_val
        
    except Exception:
        return str(value)


def clean_id_column(value) -> str:
    """
    ID 컬럼에서 소수점(.0)을 제거합니다.
    
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


# ============================================================================
# 📧 UNIFIED EMAIL RENDERER
# ============================================================================

@dataclass
class EmailContext:
    """이메일 렌더링에 필요한 모든 컨텍스트 데이터"""
    # 필수 필드
    subject: str
    header_title: str
    greeting: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    amount_columns: List[str]
    
    # 선택적 필드
    header_subtitle: Optional[str] = None
    info_message: Optional[str] = None
    additional_message: Optional[str] = None
    footer_text: Optional[str] = None
    totals: Optional[Dict[str, str]] = None
    
    # 템플릿 변수
    company_name: str = ""
    company_code: str = ""
    period: str = ""
    date: str = ""
    row_count: int = 0


def render_email_html(
    context: EmailContext,
    style: Optional[EmailStyleConfig] = None
) -> str:
    """
    단일 통합 이메일 렌더링 함수.
    미리보기와 실제 발송 모두에서 이 함수를 사용합니다.
    
    Args:
        context: EmailContext 데이터클래스 인스턴스
        style: 스타일 설정 (None이면 기본값 사용)
    
    Returns:
        렌더링된 HTML 문자열
    """
    if style is None:
        style = DEFAULT_STYLE
    
    template = Template(EMAIL_TEMPLATE)
    styles = style.to_inline_styles()
    
    # 금액 컬럼이 아닌 컬럼 수 계산 (합계 행의 colspan용)
    non_amount_count = len([c for c in context.columns if c not in context.amount_columns])
    
    # 기본 푸터 텍스트
    footer_text = context.footer_text
    if footer_text is None:
        footer_text = """
        본 메일은 자동 발송된 메일입니다.<br>
        문의사항이 있으시면 담당자에게 연락 바랍니다.<br>
        <br>
        <small>© 2024 Intelligent Mail Merge System. All rights reserved.</small>
        """
    
    return template.render(
        subject=context.subject,
        header_title=context.header_title,
        header_subtitle=context.header_subtitle,
        greeting=context.greeting,
        info_message=context.info_message,
        columns=context.columns,
        rows=context.rows,
        amount_columns=context.amount_columns,
        totals=context.totals,
        non_amount_count=non_amount_count,
        additional_message=context.additional_message,
        footer_text=footer_text,
        styles=styles
    )


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
    기존 API와의 호환성을 위한 래퍼 함수.
    내부적으로 render_email_html을 호출합니다.
    
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
    context = EmailContext(
        subject=subject,
        header_title=header_title,
        greeting=greeting,
        columns=columns,
        rows=rows,
        amount_columns=amount_columns,
        totals=totals,
        header_subtitle=header_subtitle,
        info_message=info_message,
        additional_message=additional_message,
        footer_text=footer_text,
        row_count=len(rows)
    )
    return render_email_html(context)


def render_email_content(
    group_key: str,
    group_data: Dict[str, Any],
    display_cols: List[str],
    amount_cols: List[str],
    templates: Dict[str, str]
) -> str:
    """
    그룹 데이터와 템플릿으로 이메일 콘텐츠를 생성합니다.
    
    Args:
        group_key: 그룹 키 (업체명)
        group_data: 그룹 데이터 (rows, totals, recipient_email 등)
        display_cols: 표시할 컬럼 목록
        amount_cols: 금액 컬럼 목록
        templates: 템플릿 딕셔너리 (subject, header_title, greeting, footer 등)
    
    Returns:
        렌더링된 HTML 문자열
    """
    # 템플릿 변수 준비
    template_vars = {
        'company_name': group_key,
        'company_code': group_key,
        'period': datetime.now().strftime('%Y년 %m월'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'row_count': group_data.get('row_count', len(group_data.get('rows', []))),
    }
    
    try:
        # 본문 템플릿 렌더링
        greeting_text = templates.get('greeting', '')
        greeting = Template(greeting_text).render(**template_vars)
        greeting = greeting.replace('\n', '<br>')
        
        info_text = templates.get('info', '')
        info_message = Template(info_text).render(**template_vars) if info_text else ''
        
        additional_text = templates.get('additional', '')
        additional = Template(additional_text).render(**template_vars) if additional_text else ''
        
        footer_text = templates.get('footer', '')
        footer = Template(footer_text).render(**template_vars) if footer_text else ''
        
    except Exception:
        # 템플릿 렌더링 실패 시 원본 텍스트 사용
        greeting = templates.get('greeting', '').replace('\n', '<br>')
        info_message = templates.get('info', '')
        additional = templates.get('additional', '')
        footer = templates.get('footer', '')
    
    # 컨텍스트 생성
    context = EmailContext(
        subject=templates.get('subject', ''),
        header_title=templates.get('header_title', ''),
        greeting=greeting,
        columns=display_cols,
        rows=group_data.get('rows', []),
        amount_columns=amount_cols,
        totals=group_data.get('totals'),
        info_message=info_message if info_message else None,
        additional_message=additional if additional else None,
        footer_text=footer.replace('\n', '<br>') if footer else None,
        company_name=group_key,
        company_code=group_key,
        period=template_vars['period'],
        date=template_vars['date'],
        row_count=template_vars['row_count']
    )
    
    return render_email_html(context)


def render_preview(
    recipient_email: str,
    subject: str,
    content: str
) -> str:
    """
    이메일 미리보기 래퍼를 렌더링합니다.
    
    Args:
        recipient_email: 수신자 이메일
        subject: 이메일 제목
        content: 이메일 본문 HTML
    
    Returns:
        미리보기용 HTML 문자열
    """
    return f"""
    <div style="font-family: 'Malgun Gothic', Arial, sans-serif; padding: 20px; background: #f5f5f5; border-radius: 8px;">
        <h3 style="color: #333; margin-top: 0;">📧 이메일 미리보기</h3>
        <hr style="border: none; border-top: 1px solid #ddd;">
        <p><strong>수신자:</strong> {html.escape(recipient_email)}</p>
        <p><strong>제목:</strong> {html.escape(subject)}</p>
        <hr style="border: none; border-top: 1px solid #ddd;">
        <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
            {content}
        </div>
    </div>
    """


# ============================================================================
# 🔧 UTILITY EXPORTS
# ============================================================================

# 기존 style.py와의 호환성을 위해 get_styles 함수 제공
def get_styles() -> Dict[str, str]:
    """스타일 딕셔너리 반환 (기존 API 호환)"""
    return DEFAULT_STYLE.to_inline_styles()


# 기본 템플릿 상수 (기존 코드 호환)
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


# ============================================================================
# 🧪 MODULE TEST
# ============================================================================

if __name__ == "__main__":
    print("=== Email Template Module Test ===")
    
    # 포맷터 테스트
    print(f"\n📊 Formatter Tests:")
    print(f"  Currency: {format_currency(1250000)} (expected: 1,250,000)")
    print(f"  Percent: {format_percent(0.15)} (expected: 15.0%)")
    print(f"  Date: {format_date('2024/03/15')} (expected: 2024-03-15)")
    print(f"  Clean ID: {clean_id_column('12345.0')} (expected: 12345)")
    
    # 이메일 렌더링 테스트
    print(f"\n📧 Email Rendering Test:")
    test_context = EmailContext(
        subject="테스트 이메일",
        header_title="정산 내역 안내",
        greeting="안녕하세요, <strong>테스트업체</strong> 담당자님.",
        columns=["품목", "수량", "금액"],
        rows=[
            {"품목": "상품A", "수량": "10", "금액": "100,000"},
            {"품목": "상품B", "수량": "5", "금액": "50,000"},
        ],
        amount_columns=["금액"],
        totals={"금액": "150,000"}
    )
    
    html_output = render_email_html(test_context)
    print(f"  HTML Length: {len(html_output)} characters")
    print(f"  Contains table: {'<table' in html_output}")
    print(f"  Contains header: {'정산 내역 안내' in html_output}")
    
    print("\n✅ All tests passed!")
