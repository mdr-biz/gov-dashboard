# 만다린 정부지원사업 MCP — 설치·사용 가이드

Claude에게 "이번 주 로봇 공고 중 우리가 지원 가능한 것 골라줘"라고 말하면
대시보드 데이터를 직접 조회하고, 공고 원문을 읽고, 회사 프로필과 대조해 답하도록 연결합니다.

```
[GitHub Actions] 매일 08시 수집 → archive.json (기존 그대로)
        ↓ 읽기
[이 MCP 서버] 내 PC에서 실행 ── 회사 프로필 · 관심공고 (내 PC에만 저장)
        ↓
[Claude Desktop] 대화로 질문
```

## 제공 기능 (도구 5개)

| 도구 | 하는 일 |
|---|---|
| `search_notices` | 키워드·Tier·기관·기간·분류로 공고 검색 |
| `recent_notices` | 최근 N일 새 공고 + Tier별 건수 |
| `get_notice_detail` | 공고 원문을 읽어 자격·지원금·마감·제출서류 파악 |
| `get_company_profile` | 회사 프로필 불러오기 (적합도 판단용) |
| `manage_watchlist` | 관심공고 저장, 상태(검토중/지원예정/지원완료/제외)·마감일 관리, 7일 내 마감 조회 |

---

## 설치 (최초 1회, 약 10분)

### 1단계. Python 확인
터미널(Windows: PowerShell)에서 `python --version` 입력 → **3.10 이상**이면 됩니다.
없으면 python.org에서 설치(Windows는 설치 화면에서 "Add to PATH" 체크).

### 2단계. 파일 내려받기·패키지 설치
```bash
git clone https://github.com/mdr-biz/gov-dashboard.git
cd gov-dashboard/mcp_server
pip install -r requirements.txt
```

### 3단계. 회사 프로필 작성
`company_profile.example.yaml`을 복사해 아래 위치에 `company_profile.yaml`로 저장하고 값을 채웁니다.
- Windows: `C:\Users\<사용자명>\.mandarin-gov\company_profile.yaml`
- Mac: `/Users/<사용자명>/.mandarin-gov/company_profile.yaml`

> 이 파일은 저장소에 커밋하지 마십시오. 저장소가 공개 상태입니다.

### 4단계. Claude Desktop에 등록
Claude Desktop → 설정 → 개발자(Developer) → **구성 편집(Edit Config)** 을 누르면
`claude_desktop_config.json` 파일이 열립니다. 아래 내용을 넣고 저장합니다.

**Windows**
```json
{
  "mcpServers": {
    "mandarin-gov": {
      "command": "python",
      "args": ["C:\\Users\\<사용자명>\\gov-dashboard\\mcp_server\\server.py"]
    }
  }
}
```

**Mac**
```json
{
  "mcpServers": {
    "mandarin-gov": {
      "command": "python3",
      "args": ["/Users/<사용자명>/gov-dashboard/mcp_server/server.py"]
    }
  }
}
```
- 경로는 2단계에서 내려받은 실제 위치로 바꾸세요.
- 이미 다른 `mcpServers` 항목이 있으면 그 안에 `"mandarin-gov": {...}` 만 추가합니다.

### 5단계. Claude Desktop 완전 종료 후 재실행
입력창 아래 도구(🔨) 아이콘에 `mandarin-gov` 도구 5개가 보이면 완료입니다.

---

## 이렇게 말해 보세요

| 상황 | 예시 |
|---|---|
| 아침 점검 | "최근 3일 새 공고 중 Tier 2·3만 요약해줘" |
| 탐색 | "로봇 실증 관련 공고 찾아줘" / "외식 프랜차이즈 지원사업 있어?" |
| 적합도 판단 | "최근 1주일 공고 중 우리 회사가 지원 가능한 것만 골라서 이유와 함께 알려줘" |
| 상세 분석 | "이 공고 지원자격·지원금·마감일·제출서류 표로 정리해줘" |
| 관리 | "이 공고 지원예정으로 저장, 마감 11월 15일" / "이번 주 마감 공고 알려줘" |
| 연계 | "지원예정 공고 마감일을 캘린더에 넣어줘" (Google Calendar 커넥터 연결 시) |

## 자주 묻는 문제

- **도구가 안 보임**: 설정 파일 경로 오타(Windows는 `\\` 두 번), 또는 Claude Desktop을 트레이까지 완전 종료하지 않은 경우가 대부분입니다.
- **`python`을 찾을 수 없음**: `"command"`에 Python 전체 경로를 넣으세요 (터미널에서 `where python` / `which python3` 로 확인).
- **공고 상세가 목록 페이지만 나옴**: 일부 기관(로봇산업진흥원 등)은 수집 단계에서 개별 공고 주소가 아닌 게시판 주소가 저장됩니다. 해당 소스 크롤러 개선이 필요합니다.

## 보안 설계

- **읽기 위주**: 신청서 제출·메일 발송 기능이 없습니다.
- **접속 제한**: 공고 원문 조회는 등록된 기관 도메인만 허용합니다(`ALLOWED_DOMAINS`).
- **로컬 보관**: 회사 프로필·관심공고는 내 PC(`~/.mandarin-gov/`)에만 저장되며 외부로 전송되지 않습니다.
- **프롬프트 인젝션 대비**: 공고 본문은 "데이터"로 표시해 전달하며, 본문 속 지시문을 따르지 않도록 안내합니다.
- API 키(DATAGO_KEY, BIZINFO_KEY)는 기존대로 GitHub Secrets에만 있으며 MCP 서버는 사용하지 않습니다.

## 설정 변경 (선택, 환경변수)

| 변수 | 기본값 | 용도 |
|---|---|---|
| `MANDARIN_GOV_DIR` | `~/.mandarin-gov` | 프로필·관심공고 저장 폴더 |
| `GOV_ARCHIVE_PATH` | (없음) | 원격 대신 로컬 archive.json 사용 |
| `GOV_ARCHIVE_URL` | GitHub raw 주소 | 저장소를 옮긴 경우 |
