# 🎮 호요봇 (Hoyo Bot)

![Version](https://img.shields.io/badge/version-1.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-yellow?style=flat-square&logo=python)
![Discord](https://img.shields.io/badge/Discord.py-2.3+-5865F2?style=flat-square&logo=discord)

호요버스 게임(원신, 스타레일, 젠레스 존 제로), 명조, 명일방주: 엔드필드 플레이어를 위한 디스코드 봇입니다.

## ✨ 주요 기능

- **🎁 리딤코드 자동 알림**: 새로운 리딤코드가 나오면 자동으로 알림 (원신, 스타레일, 젠레스, 엔드필드)
- **🎬 유튜브 알림**: 공식 유튜브 채널 새 영상 알림
- **🔮 오늘의 운세**: 캐릭터 테마의 재미있는 운세
- **🎰 가챠 시뮬레이터**: 뽑기 시뮬레이션
- **📊 캐릭터/무기/성유물 정보**: 게임 내 정보 조회
- **💬 AI 채팅**: Gemini 기반 대화 (선택사항)

---

## 🚀 설치 가이드

### 1단계: 디스코드 봇 생성

1. [Discord Developer Portal](https://discord.com/developers/applications)에 접속
2. **"New Application"** 클릭 → 이름 입력 → 생성
3. 왼쪽 메뉴에서 **"Bot"** 클릭
4. **"Reset Token"** 클릭 → 토큰 복사 (이 토큰은 절대 공유하지 마세요!)
5. 아래 설정 활성화:
   - ✅ MESSAGE CONTENT INTENT

### 2단계: 봇을 서버에 초대

1. 왼쪽 메뉴에서 **"OAuth2"** → **"URL Generator"** 클릭
2. SCOPES에서 **"bot"** 체크
3. BOT PERMISSIONS에서 다음 체크:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Use Slash Commands
4. 생성된 URL을 복사하여 브라우저에서 열기 → 서버 선택 → 초대

### 3단계: 환경 변수 설정 (가장 쉬운 방법!)

**`설정하기.bat`** 파일을 더블클릭하세요! 🎉

설정 마법사가 실행되면:
1. 디스코드 봇 토큰 붙여넣기
2. (선택) Gemini API 키 입력
3. 완료!

> 💡 수동 설정을 원하시면 `.env.example` 파일을 `.env`로 복사 후 편집하세요.

### 4단계: Python 설치

1. [Python 3.11](https://www.python.org/downloads/)을 다운로드하여 설치
2. ⚠️ 설치 시 **"Add Python to PATH"** 체크 필수!

### 5단계: 봇 실행

**`봇 시작하기.bat`** 파일을 더블클릭하세요! 🚀

- 첫 실행 시 필요한 패키지가 자동으로 설치됩니다
- 이후에는 바로 봇이 시작됩니다

> 💡 봇을 종료하려면 창을 닫거나 `Ctrl+C`를 누르세요.

### 6단계: 선택 기능 설치 (Optional)

#### 📊 캐릭터/무기/성유물 정보 기능

캐릭터 정보(`!캐릭터`), 무기 정보(`!무기`) 등의 기능을 사용하려면 다음 명령어를 실행하세요:

```bash
pip install git+https://github.com/seriaati/hakushin-py.git
```

> ⚠️ **오류 발생 시:**
> ```
> ❌ cogs.hoyo_characters는 hakushin 모듈이 필요합니다. (선택사항)
> ❌ ModuleNotFoundError: No module named 'hakushin'
> ```
> 위 에러가 표시되면 cmd 또는 PowerShell에서 위 명령어를 실행한 후 봇을 재시작하세요.

---

## 📺 사용 방법

**[호요봇 사용법 영상 보러가기](https://youtu.be/OCn8zAULs1U?si=TvshBzbYdlgdFZzy)**

---

## 📝 기본 명령어

| 명령어 | 설명 |
|--------|------|
| `!도움` | 전체 명령어 목록 보기 |
| `!운세` | 오늘의 운세 확인 |
| `!뽑기` | 가챠 시뮬레이터 |
| `!캐릭터 [이름]` | 캐릭터 정보 조회 |
| `!무기 [이름]` | 무기 정보 조회 |
| `!성유물 [이름]` | 성유물 정보 조회 |

### 관리자 명령어

| 명령어 | 설명 |
|--------|------|
| `!알림설정` | 현재 채널에 알림 설정 |
| `!알림해제` | 알림 해제 |
| `!알림상태` | 현재 알림 설정 확인 |

---

## ⚙️ 알림 설정 방법

1. 알림을 받고 싶은 채널에서 `!알림설정` 입력
2. 원하는 알림 유형 선택:
   - 📋 코드 알림 (리딤코드)
   - 🎬 유튜브 알림 (새 영상)
   - 🆕 신규 업데이트 (신캐릭터/무기 등)

---

## 🔧 문제 해결

### "DISCORD_TOKEN 환경 변수가 설정되지 않았습니다"
→ `.env` 파일이 올바르게 생성되었는지 확인하세요.

### 봇이 오프라인으로 표시됨
→ Python 창이 실행 중인지 확인하세요. 창을 닫으면 봇도 종료됩니다.

### 명령어가 작동하지 않음
→ MESSAGE CONTENT INTENT가 활성화되어 있는지 확인하세요.

### 명조 리딤코드가 안 나와요
→ ⚠️ 명조 코드 알림 기능은 현재 **임시 중단** 상태입니다. (외부 사이트 접근 차단 문제)

## 💬 문의 및 지원

문제 발생 시 디스코드 서버로 문의 부탁드립니다!

[![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/VEtKNCB7m3)

👉 **https://discord.gg/VEtKNCB7m3**

---

## 🎨 프로젝트 정보

이 프로젝트는 **Claude Opus 4.5**, **Sonnet 4.5**, **Gemini 3 Pro**, **ChatGPT 5.2**와 
**Replit**, **Antigravity**, **Cursor**를 사용해 제작된 **비개발자 바이브코딩 프로젝트**입니다.

> 🎵 *"코딩을 몰라도 AI와 함께라면!"*

---

## 📄 라이선스

**자유롭게 수정하고 배포하세요!** 🎉

- ✅ 코드 자유 수정 가능
- ✅ 자유 배포 가능
- ✅ 상업적 사용 가능

---

## 🙏 크레딧

- 리딤코드 API: [hoyo-codes.seria.moe](https://hoyo-codes.seria.moe)
- 게임 데이터: [Hakushin](https://gi.hakush.in)
