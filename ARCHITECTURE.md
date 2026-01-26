# 🏗️ 지능형 그룹핑 메일머지 시스템 아키텍처

## 📋 시스템 개요

이 시스템은 엑셀 데이터를 특정 Key(업체코드, 이메일 등)를 기준으로 **자동 그룹화**하여,
각 그룹에 해당하는 **정산서 테이블**을 포함한 이메일을 발송하는 엔터프라이즈급 솔루션입니다.

---

## 🔄 데이터 흐름도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW PIPELINE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Excel   │────▶│ Data Loader  │────▶│  Validator   │────▶│   Cleaner    │
  │  Upload  │     │   (Pandas)   │     │  (Pydantic)  │     │   Engine     │
  └──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                     │
                         ┌───────────────────────────────────────────┘
                         ▼
              ┌──────────────────┐     ┌──────────────────┐
              │  Group Aggregator │────▶│  Template Engine │
              │  (Pandas GroupBy) │     │    (Jinja2)      │
              └──────────────────┘     └──────────────────┘
                                                │
                         ┌──────────────────────┘
                         ▼
              ┌──────────────────┐     ┌──────────────────┐     ┌──────────┐
              │  Email Composer  │────▶│  SMTP Dispatcher │────▶│  Report  │
              │  (HTML Builder)  │     │  (Batch Control) │     │ Generator│
              └──────────────────┘     └──────────────────┘     └──────────┘
```

---

## 🧩 핵심 모듈 구성

### 1. **Data Orchestration Layer** (`app.py`)

```python
# 핵심 그룹화 로직
df.groupby(group_key_column)
  .apply(lambda group: {
      'recipient_email': resolve_email(group),  # 이메일 충돌 해결
      'rows': clean_and_format(group),           # 데이터 클린징
      'totals': calculate_totals(group)          # 합계 자동 계산
  })
```

### 2. **Email Conflict Resolution Logic**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EMAIL CONFLICT RESOLVER                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Case 1: 모든 행의 이메일이 동일                                      │
│  ──────────────────────────────────                                 │
│  ✅ 정상 처리 → 해당 이메일로 발송                                    │
│                                                                     │
│  Case 2: 행마다 이메일이 다름                                         │
│  ──────────────────────────────                                     │
│  ⚠️ 경고 표시 + 사용자 선택:                                         │
│     • Option A: 첫 번째 행 이메일 사용                                │
│     • Option B: 가장 많이 등장한 이메일 사용                          │
│     • Option C: 해당 그룹 발송 스킵 (수동 처리 권장)                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. **Data Cleaning Pipeline**

```python
# 처리 순서
1. ID 컬럼 소수점 제거: "12345.0" → "12345"
2. 금액 컬럼 포맷팅: 1250000 → "₩1,250,000"
3. 날짜 컬럼 통일: 다양한 형식 → "YYYY-MM-DD"
4. 공백/결측값 처리: NaN → "-" 또는 사용자 지정 값
```

### 4. **Template Engine (Jinja2)**

```html
<!-- 그룹화된 데이터를 테이블로 렌더링 -->
<table>
  <thead>...</thead>
  <tbody>
    {% for row in rows %}
    <tr>
      {% for col in columns %}
      <td>{{ row[col] }}</td>
      {% endfor %}
    </tr>
    {% endfor %}
    <!-- 자동 합계 행 -->
    <tr class="total-row">
      <td colspan="...">합계</td>
      {% for amount in totals %}
      <td>{{ amount | currency }}</td>
      {% endfor %}
    </tr>
  </tbody>
</table>
```

---

## 📊 5단계 워크플로우 UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1          STEP 2          STEP 3          STEP 4          STEP 5
│  ━━━━━━━         ━━━━━━━         ━━━━━━━         ━━━━━━━         ━━━━━━━
│  📤 Excel       🔑 Column       👁️ Preview      ✉️ Template     📨 Send
│  Upload         Selection       & Edit          Editor          & Report
│                                                                     │
│  • .xlsx 지원    • 그룹핑 Key    • st.data_     • 제목/본문      • Progress
│  • .xls 지원     • 이메일 컬럼     editor         편집            Bar
│  • 인코딩 자동   • 금액 컬럼     • 충돌 경고    • 미리보기       • 성공/실패
│    감지          • 날짜 컬럼     • 데이터 수정  • 변수 자동완성   카운트
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Fail-safe 전송 메커니즘

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BATCH TRANSMISSION CONTROL                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Settings:                                                          │
│  ─────────                                                          │
│  • Batch Size: 10 emails/batch (configurable)                       │
│  • Delay Between Emails: 1-5 seconds (configurable)                 │
│  • Delay Between Batches: 30-60 seconds (configurable)              │
│                                                                     │
│  Session Persistence (st.session_state):                            │
│  ─────────────────────────────────────────                          │
│  • sent_count: 성공 발송 수                                          │
│  • failed_list: 실패 목록 (이메일, 에러 메시지)                       │
│  • current_batch: 현재 배치 번호                                     │
│  • is_paused: 일시정지 상태                                          │
│                                                                     │
│  Recovery:                                                          │
│  ─────────                                                          │
│  • 브라우저 새로고침 시 상태 복원                                     │
│  • "이어서 발송" 기능 제공                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 파일 구조

```
/home/user/webapp/
├── app.py                  # 메인 Streamlit 애플리케이션
├── style.py                # 이메일 템플릿 및 CSS 모듈
├── requirements.txt        # 의존성 목록
├── ARCHITECTURE.md         # 아키텍처 문서 (현재 파일)
└── sample_data/            # 테스트용 샘플 데이터 (선택)
    └── sample_settlement.xlsx
```

---

## 🔒 보안 고려사항

1. **비밀번호 처리**: `st.text_input(type="password")` 사용
2. **환경변수 지원**: `.env` 파일 또는 Streamlit secrets 연동
3. **SMTP TLS/SSL**: 암호화 연결 강제
4. **민감정보 로깅 금지**: 이메일 비밀번호 등 로그에 미포함

---

## 📈 성능 최적화

- **대용량 파일 처리**: Pandas chunked reading 지원
- **메모리 효율**: 그룹 단위 스트리밍 처리
- **비동기 발송 옵션**: 향후 확장 가능 구조

---

*Built with ❤️ by Senior Solution Architect (20 Years Experience)*
