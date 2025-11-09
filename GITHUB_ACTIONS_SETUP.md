# 🚀 GitHub Actions 설정 가이드

완전 무료로 클라우드에서 24시간 자동 모니터링하는 방법

---

## 📖 목차

1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [설정 단계](#설정-단계)
4. [GitHub Secrets 설정](#github-secrets-설정)
5. [첫 실행 테스트](#첫-실행-테스트)
6. [모니터링 방법](#모니터링-방법)
7. [스케줄 커스터마이징](#스케줄-커스터마이징)
8. [트러블슈팅](#트러블슈팅)
9. [비용 및 제한](#비용-및-제한)
10. [FAQ](#faq)

---

## 개요

### GitHub Actions란?

GitHub Actions는 GitHub에서 제공하는 **무료 클라우드 CI/CD 서비스**입니다.

**이 프로젝트에서의 활용**:
- ✅ **완전 무료** (public repository)
- ✅ **서버 불필요** - GitHub 클라우드에서 자동 실행
- ✅ **PC 끄기 가능** - 언제든지 작동
- ✅ **자동 스케줄** - 설정한 시간에 자동 실행
- ✅ **이메일 알림** - 새 기사 발견 시 자동 발송

### 비용

| Repository 타입 | 월 실행 시간 | 비용 |
|----------------|-------------|------|
| **Public** | **무제한** | **$0** ⭐ 추천 |
| Private | 2,000분 | $0 (무료) |
| Private (초과) | 추가 분 | $0.008/분 |

**예상 사용량 (3시간마다 실행)**:
- 1회 실행: ~5분
- 하루: 8회 × 5분 = 40분
- 한 달: 40분 × 30일 = **1,200분**

**💡 결론**: Public repository 사용 시 **완전 무료**!

---

## 사전 준비

### 1. GitHub 계정

아직 없다면:
1. https://github.com 접속
2. **Sign up** 클릭
3. 이메일 인증 완료

### 2. 로컬 환경 확인

**이미 완료된 항목** (✓ 체크리스트):
- [x] Python 설치
- [x] 의존성 패키지 설치 (`pip install -r requirements.txt`)
- [x] `.env` 파일 설정
- [x] Gmail App Password 생성
- [x] 로컬 테스트 성공 (`python main.py --test-email`)

### 3. Git 설치 확인

```powershell
git --version
```

**없다면**:
- https://git-scm.com/download/win 에서 다운로드

---

## 설정 단계

### Step 1: GitHub Repository 생성

#### 1-1. 새 Repository 만들기

1. GitHub 로그인
2. 우측 상단 **+** 클릭 → **New repository**
3. 다음 정보 입력:

   ```
   Repository name: gomu-news-monitor
   Description: 고무 업계 뉴스 자동 모니터링 시스템
   Visibility: ⭕ Public (무료 무제한)
   ```

4. ❌ **Initialize this repository with** 체크 해제
5. **Create repository** 클릭

#### 1-2. Repository URL 복사

생성 후 나타나는 URL 복사:
```
https://github.com/YOUR_USERNAME/gomu-news-monitor.git
```

---

### Step 2: 코드 업로드

#### 2-1. Git 초기화

**PowerShell에서 실행**:

```powershell
# 프로젝트 디렉토리로 이동
cd C:\Users\hyeon\Desktop\projrct\gomuhouchi

# Git 초기화
git init
git branch -M main
```

#### 2-2. .env 파일 제외 확인 ⚠️ 중요!

```powershell
# .env가 추적되지 않는지 확인
git status
```

**출력 예시**:
```
Untracked files:
  .github/
  src/
  config.yaml
  main.py
  README.md
```

**⚠️ 주의**: `.env` 파일이 **빨간색으로 나오면 안 됩니다**!

만약 나온다면:
```powershell
# .gitignore 확인
cat .gitignore | Select-String ".env"

# 강제 제거
git rm --cached .env
```

#### 2-3. 코드 커밋

```powershell
# 모든 파일 추가
git add .

# 커밋 메시지와 함께 저장
git commit -m "Initial commit: Gomu News Monitor with GitHub Actions"
```

#### 2-4. GitHub에 업로드

```powershell
# Remote 추가 (YOUR_USERNAME을 실제 GitHub 아이디로 변경!)
git remote add origin https://github.com/YOUR_USERNAME/gomu-news-monitor.git

# 업로드
git push -u origin main
```

**처음 푸시 시 로그인 창**이 나타나면 GitHub 계정으로 로그인하세요.

#### 2-5. 업로드 확인

1. GitHub Repository 페이지 새로고침
2. 파일들이 표시되는지 확인
3. ❌ `.env` 파일이 **보이지 않아야** 합니다!

---

## GitHub Secrets 설정

### 📍 위치

Repository → **Settings** 탭 → 왼쪽 **Secrets and variables** → **Actions**

![GitHub Secrets 위치](https://docs.github.com/assets/cb-66134/images/help/repository/actions-secrets-settings.png)

### 🔐 추가할 Secrets (7개)

**New repository secret** 버튼을 클릭하여 다음 7개를 하나씩 추가하세요.

---

#### 1. LOGIN_EMAIL

**Name**: `LOGIN_EMAIL`

**Secret** (Value):
```
your_gomuhouchi_email@example.com
```

**설명**: gomuhouchi.com 로그인 이메일 또는 사용자명

---

#### 2. LOGIN_PASSWORD

**Name**: `LOGIN_PASSWORD`

**Secret**:
```
your_gomuhouchi_password
```

**설명**: gomuhouchi.com 로그인 비밀번호

⚠️ **보안**: GitHub Secrets는 암호화되어 저장되며, 누구도 볼 수 없습니다.

---

#### 3. EMAIL_FROM

**Name**: `EMAIL_FROM`

**Secret**:
```
your_gmail@gmail.com
```

**설명**: 발신 Gmail 주소

---

#### 4. EMAIL_PASSWORD

**Name**: `EMAIL_PASSWORD`

**Secret**:
```
abcdefghijklmnop
```

**설명**: Gmail **App Password** (16자리)

⚠️ **중요**: 일반 Gmail 비밀번호가 아닙니다!

**Gmail App Password 생성 방법**:
1. https://myaccount.google.com/security 접속
2. **2단계 인증** 활성화 (필수)
3. **앱 비밀번호** 생성
   - 앱 선택: 메일
   - 기기 선택: Windows 컴퓨터
4. 생성된 16자리 비밀번호 복사
5. GitHub Secret에 붙여넣기

---

#### 5. EMAIL_TO

**Name**: `EMAIL_TO`

**Secret**:
```
recipient@example.com
```

**설명**: 알림 받을 이메일 주소

**여러 수신자**:
```
email1@example.com,email2@example.com,email3@example.com
```

---

#### 6. SMTP_SERVER

**Name**: `SMTP_SERVER`

**Secret**:
```
smtp.gmail.com
```

**설명**: SMTP 서버 주소

**다른 이메일 서비스**:
- Outlook: `smtp-mail.outlook.com`
- Naver: `smtp.naver.com`
- Daum: `smtp.daum.net`

---

#### 7. SMTP_PORT

**Name**: `SMTP_PORT`

**Secret**:
```
587
```

**설명**: SMTP 포트 (TLS)

**다른 포트**:
- `465` (SSL)
- `25` (일반, 비추천)

---

### 설정 완료 확인

Secrets 페이지에 다음 7개가 모두 표시되어야 합니다:

```
✓ LOGIN_EMAIL
✓ LOGIN_PASSWORD
✓ EMAIL_FROM
✓ EMAIL_PASSWORD
✓ EMAIL_TO
✓ SMTP_SERVER
✓ SMTP_PORT
```

---

## 첫 실행 테스트

### 수동 실행 (즉시 테스트)

#### 1. Actions 탭으로 이동

Repository 상단 **Actions** 탭 클릭

![Actions 탭](https://docs.github.com/assets/cb-24816/images/help/repository/actions-tab.png)

#### 2. Workflow 선택

왼쪽 사이드바에서 **Gomu News Monitor** 클릭

#### 3. 수동 실행

1. 오른쪽 **Run workflow** 버튼 클릭
2. 드롭다운이 나타남
3. **Run workflow** 초록 버튼 다시 클릭

![Run Workflow](https://docs.github.com/assets/cb-32577/images/help/repository/actions-run-workflow.png)

#### 4. 실행 상태 확인

**실행 중** (노란색 🟡):
```
● Gomu News Monitor #1
  Running...
```

**성공** (초록색 ✅):
```
✓ Gomu News Monitor #1
  Completed in 5m 23s
```

**실패** (빨간색 ❌):
```
✗ Gomu News Monitor #1
  Failed
```

---

### 실행 로그 확인

#### 성공 시 로그 예시:

```
📥 Checkout repository
  ✓ Complete

🐍 Set up Python 3.11
  ✓ Python 3.11.5

🌐 Install Google Chrome
  ✓ Google Chrome 120.0.6099.109

📦 Install Python dependencies
  ✓ Successfully installed selenium-4.16.0 ...

🔐 Create .env file from secrets
  ✓ All secrets are set

🔍 Run monitoring
  ============================================
  Workflow: Gomu News Monitor
  Run Number: 1
  ============================================
  INFO - Initializing web scraper...
  INFO - Authentication disabled - scraping public articles only
  INFO - Scraping articles...
  INFO - Found 25 articles matching keywords
  INFO - New article: バンドー化学が新製品を発表
  INFO - Sending notifications for 3 new articles...
  INFO - Notifications sent successfully
  ✅ Monitoring completed
```

---

### 이메일 확인

새 기사가 발견되었다면:
- 📧 이메일 수신함 확인
- 제목: `[고무뉴스] 새로운 기사 3건 발견`
- 내용: HTML 형식의 예쁜 이메일

새 기사가 없다면:
- 이메일 없음 (정상)
- 다음 스케줄까지 대기

---

## 모니터링 방법

### Actions 대시보드

**Repository → Actions** 탭에서:

- ✅ **모든 실행 기록** 확인
- ⏰ **실행 시간** 확인
- 📊 **성공/실패** 통계
- 📥 **로그 다운로드**

### 실행 기록 보기

| Run | Status | Trigger | Time | Duration |
|-----|--------|---------|------|----------|
| #12 | ✅ | schedule | 15:00 | 5m 12s |
| #11 | ✅ | schedule | 12:00 | 4m 58s |
| #10 | ✅ | manual | 11:30 | 5m 23s |
| #9 | ❌ | schedule | 09:00 | 1m 45s |

### 이메일 알림 설정

GitHub에서도 실패 시 이메일 받기:

1. Settings → Notifications
2. **Actions** 섹션
3. ✅ **Send notifications for failed workflows**

---

## 스케줄 커스터마이징

### 현재 설정

```yaml
schedule:
  - cron: '0 */3 * * *'  # 3시간마다
```

### Cron 표현식 구조

```
분 시 일 월 요일
│ │ │ │ │
│ │ │ │ └─ 0-6 (일요일=0)
│ │ │ └─── 1-12 (월)
│ │ └───── 1-31 (일)
│ └─────── 0-23 (시)
└───────── 0-59 (분)

* = 모든 값
*/n = n마다
n-m = n부터 m까지
n,m = n과 m
```

### 자주 사용하는 스케줄 예시

#### 1시간마다
```yaml
schedule:
  - cron: '0 * * * *'
```

#### 2시간마다
```yaml
schedule:
  - cron: '0 */2 * * *'
```

#### 6시간마다 (0시, 6시, 12시, 18시)
```yaml
schedule:
  - cron: '0 */6 * * *'
```

#### 하루 2번 (오전 9시, 오후 6시 한국 시간)
```yaml
schedule:
  # UTC로 변환: KST - 9시간
  - cron: '0 0,9 * * *'  # UTC 0시, 9시 = KST 9시, 18시
```

#### 평일만 (월~금요일 9시, 18시 한국 시간)
```yaml
schedule:
  - cron: '0 0,9 * * 1-5'  # 1-5 = 월~금
```

#### 매일 오전 8시 (한국 시간)
```yaml
schedule:
  - cron: '0 23 * * *'  # UTC 23시 = KST 다음날 8시
```

#### 매시 정각 (24회/일)
```yaml
schedule:
  - cron: '0 * * * *'
```

### 시간대 변환표

| 한국 시간 (KST) | UTC 시간 | Cron |
|----------------|----------|------|
| 오전 9:00 | 0:00 | `0 0 * * *` |
| 정오 12:00 | 3:00 | `0 3 * * *` |
| 오후 6:00 | 9:00 | `0 9 * * *` |
| 오후 9:00 | 12:00 | `0 12 * * *` |
| 자정 24:00 | 15:00 | `0 15 * * *` |

**공식**: `UTC = KST - 9시간`

### Cron 도구

**표현식 테스트**: https://crontab.guru/

입력 예시:
```
0 */3 * * *
```

출력:
```
"At minute 0 past every 3rd hour"
→ 00:00, 03:00, 06:00, 09:00, ...
```

---

## 트러블슈팅

### 문제 1: Secrets not found

**증상**:
```
Error: .env file has empty values
```

**원인**: GitHub Secrets가 설정되지 않음

**해결**:
1. Settings → Secrets → Actions
2. 7개 Secret 모두 등록 확인
3. Secret 이름 대소문자 정확히 확인:
   - ✅ `LOGIN_EMAIL`
   - ❌ `login_email`
   - ❌ `Login_Email`

---

### 문제 2: Chrome/ChromeDriver 오류

**증상**:
```
WebDriverException: chrome not reachable
```

**원인**: Chrome 설치 실패 또는 버전 불일치

**해결**:
- 대부분 일시적 오류 → **재실행** 시 해결
- 3회 연속 실패 시:
  1. Actions 탭 → 해당 실행 클릭
  2. "Install Chrome" step 로그 확인
  3. GitHub Issues에 로그 첨부하여 문의

---

### 문제 3: Email authentication failed

**증상**:
```
SMTPAuthenticationError: Username and Password not accepted
```

**원인**:
1. `EMAIL_PASSWORD`에 일반 비밀번호 사용
2. Gmail 2단계 인증 미활성화
3. App Password 만료

**해결**:
1. Gmail 2단계 인증 확인
2. **새로운 App Password 생성**:
   - https://myaccount.google.com/apppasswords
   - 기존 비밀번호 삭제
   - 새 비밀번호 생성 (16자리)
3. GitHub Secret `EMAIL_PASSWORD` 업데이트:
   - Actions → Secrets
   - `EMAIL_PASSWORD` 클릭
   - **Update secret**
   - 새 비밀번호 붙여넣기
4. 재실행

---

### 문제 4: Timeout (10분 초과)

**증상**:
```
Error: The operation was canceled (timeout 10 minutes)
```

**원인**: 사이트가 느리거나 응답 없음

**해결**:

**방법 1**: `config.yaml` 수정
```yaml
monitoring:
  request_timeout_seconds: 90  # 60 → 90으로 증가
```

**방법 2**: Workflow 타임아웃 증가
```yaml
# .github/workflows/monitor.yml
jobs:
  monitor:
    timeout-minutes: 15  # 10 → 15로 증가
```

Commit & Push 후 재실행

---

### 문제 5: Rate limiting / IP 차단

**증상**:
```
HTTP 429: Too Many Requests
```

**원인**: 너무 자주 요청

**해결**:
1. 스케줄 간격 늘리기:
   ```yaml
   schedule:
     - cron: '0 */6 * * *'  # 3시간 → 6시간
   ```

2. `config.yaml` 딜레이 증가:
   ```yaml
   scraping:
     delay_between_requests_min: 3
     delay_between_requests_max: 6
   ```

---

### 문제 6: No articles found (항상)

**증상**:
```
INFO - Found 0 articles matching keywords
```

**원인**:
1. 사이트 구조 변경
2. 키워드 불일치
3. 로그인 필요

**해결**:

**1. 로컬에서 테스트**:
```powershell
python main.py --mode test
```

**2. 디버그 모드 활성화**:
```yaml
# config.yaml
logging:
  level: "DEBUG"
```

**3. 키워드 확인**:
```yaml
site:
  keywords:
    - "バンドー化学"  # 정확한 키워드인지 확인
    - "三ツ星ベルト"
```

**4. Issue 생성**: 로그 첨부

---

### 문제 7: Git push 실패

**증상**:
```
! [rejected] main -> main (fetch first)
```

**원인**: Remote에 로컬에 없는 변경사항 존재

**해결**:
```powershell
# Remote 변경사항 가져오기
git pull origin main --rebase

# 충돌 해결 후
git push origin main
```

---

## 비용 및 제한

### Public Repository (무료) ⭐

| 항목 | 제한 |
|------|------|
| **실행 시간** | **무제한** |
| 동시 실행 | 20개 Job |
| Job당 실행 시간 | 6시간 |
| Workflow당 실행 시간 | 72시간 |
| API 요청 | 1,000/시간 |
| Artifact 스토리지 | 500MB |
| 로그 보관 | 90일 |

**💰 비용**: **$0/월**

### Private Repository

| 플랜 | 월 무료 시간 | 초과 시 비용 |
|------|-------------|-------------|
| Free | 2,000분 | $0.008/분 |
| Pro | 3,000분 | $0.008/분 |
| Team | 3,000분 | $0.008/분 |

**예상 비용 (3시간마다 실행)**:
- 월 사용: ~1,200분
- Free 플랜: 무료 (2,000분 내)
- 초과 시: 최대 $0 (Free 플랜 충분)

### 권장사항

✅ **Public Repository 사용**
- 완전 무료
- 실행 시간 무제한
- 민감 정보는 GitHub Secrets에 안전하게 보관

❌ **코드만 공개, 자격증명은 비공개**
- 코드: GitHub에 공개
- 비밀번호: GitHub Secrets (암호화)

---

## FAQ

### Q1: Public으로 하면 내 비밀번호가 공개되나요?

**A**: 아니요! 절대 공개되지 않습니다.

- ✅ **코드만 공개**: Python 파일, 설정 파일
- ❌ **공개 안 됨**: `.env`, 비밀번호, 이메일
- 🔒 **GitHub Secrets**: 암호화되어 저장, 누구도 볼 수 없음

### Q2: 실행 시간을 더 짧게 할 수 있나요?

**A**: 네, 최소 5분마다 실행 가능합니다.

```yaml
schedule:
  - cron: '*/5 * * * *'  # 5분마다
```

**단, 주의사항**:
- 사이트 서버 부하 가능
- IP 차단 위험
- **권장**: 최소 30분 간격

### Q3: 여러 사이트를 동시에 모니터링할 수 있나요?

**A**: 네, 방법이 2가지 있습니다.

**방법 1**: 같은 Workflow에서 여러 URL
```yaml
# config.yaml에 여러 URL 추가
```

**방법 2**: 별도 Workflow 생성
```
.github/workflows/
├── monitor-site1.yml
└── monitor-site2.yml
```

### Q4: 로컬과 GitHub Actions 동시 실행 가능한가요?

**A**: 네, 가능합니다!

- 로컬: 즉시 테스트용
- GitHub Actions: 자동 스케줄용

데이터베이스는 각각 별도로 관리됩니다.

### Q5: 실행 실패 시 이메일 알림 받을 수 있나요?

**A**: 네, 설정 가능합니다.

**GitHub 알림**:
1. Settings → Notifications
2. Actions 섹션
3. ✅ "Send notifications for failed workflows"

**커스텀 알림**: Workflow에 추가
```yaml
- name: Notify on failure
  if: failure()
  run: |
    # 이메일/Slack/Telegram 알림 코드
```

### Q6: 실행 로그를 파일로 저장하고 싶어요.

**A**: Workflow에서 자동으로 보관됩니다.

**다운로드 방법**:
1. Actions → 실행 기록 클릭
2. 하단 **Artifacts** 섹션
3. `monitor-logs-XXX.zip` 다운로드

**보관 기간**: 7일 (설정 가능)

### Q7: 일시 중지하고 싶어요.

**A**: 3가지 방법이 있습니다.

**방법 1**: Workflow 비활성화
- Actions → Workflow → "..." → **Disable workflow**

**방법 2**: Schedule 주석 처리
```yaml
# schedule:
#   - cron: '0 */3 * * *'
```

**방법 3**: Repository archive
- Settings → General → 하단 **Archive this repository**

### Q8: Private repository로 변경하면?

**A**: 여전히 작동하지만, 실행 시간 제한이 생깁니다.

- Free 플랜: 월 2,000분
- 예상 사용: ~1,200분
- **결론**: Free 플랜으로도 충분

---

## 추가 팁

### 로그 분석

**실행 로그 다운로드**:
```powershell
# Actions → Artifacts → 다운로드
# logs-123.zip 압축 해제
cat logs/monitor.log
```

**에러 필터링**:
```powershell
cat logs/monitor.log | Select-String "ERROR"
```

### Workflow Badge 추가

README.md에 상태 배지 추가:

```markdown
![Monitoring Status](https://github.com/YOUR_USERNAME/gomu-news-monitor/actions/workflows/monitor.yml/badge.svg)
```

결과:
![Monitoring Status](https://github.com/YOUR_USERNAME/gomu-news-monitor/actions/workflows/monitor.yml/badge.svg)

### 환경별 설정

**Development/Production 분리**:

```yaml
# .github/workflows/monitor.yml
env:
  ENV: production
```

```python
# main.py
if os.getenv('ENV') == 'production':
    # Production 설정
else:
    # Development 설정
```

---

## 도움 받기

### 문제 해결 순서

1. **로컬 테스트**:
   ```powershell
   python main.py --mode test
   ```

2. **로그 확인**:
   - Actions → 실행 기록 → 각 step 클릭

3. **설정 검증**:
   - Secrets 7개 모두 설정됨
   - `.env` 파일이 git에 없음
   - `config.yaml` headless: true

4. **GitHub Issue 생성**:
   - Repository → Issues → New issue
   - 에러 로그 첨부
   - 실행 번호 (#123) 명시

### 유용한 리소스

- **GitHub Actions 문서**: https://docs.github.com/en/actions
- **Cron 표현식**: https://crontab.guru/
- **Gmail App Password**: https://support.google.com/accounts/answer/185833

---

## 결론

축하합니다! 🎉

이제 완전 무료로 24시간 자동 모니터링 시스템을 갖추셨습니다.

**다음 단계**:
1. ✅ 첫 실행 테스트 완료
2. 📧 이메일 수신 확인
3. 📊 통계 확인
4. 🎯 스케줄 최적화

**Happy Monitoring!** 🚀

---

**최종 수정일**: 2024년 11월
**버전**: 1.0.0
