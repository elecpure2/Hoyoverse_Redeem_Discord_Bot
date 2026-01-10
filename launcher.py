import os
import sys
import subprocess
import time

def install_packages():
    print("\n📦 [초기 설정] 필요한 패키지를 설치합니다...")
    print("   (이 과정은 처음에만 실행됩니다)\n")
    try:
        # requirements.txt 설치
        print("1️⃣  기본 패키지 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 기본 패키지 설치 완료\n")
        
        # Hakushin 설치
        print("2️⃣  Hakushin 라이브러리 설치 중...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/thesadru/hakushin.git"])
            print("✅ Hakushin 설치 완료\n")
        except:
            print("⚠️  Hakushin 설치 실패 (Git이 없거나 네트워크 문제). 일단 진행합니다.\n")
        
        # 설치 마커 생성
        with open(".installed", "w") as f:
            f.write("installed")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 패키지 설치 중 오류가 발생했습니다: {e}")
        input("엔터를 누르면 종료합니다...")
        sys.exit(1)

def main():
    # 콘솔 인코딩 설정 (윈도우용)
    if os.name == 'nt':
        os.system('chcp 65001')
        os.system('cls')

    print("\n╔════════════════════════════════════════════╗")
    print("║          🚀 호요봇 런처 (Launcher)         ║")
    print("╚════════════════════════════════════════════╝\n")

    # 1. .env 확인
    if not os.path.exists(".env"):
        print("❌ .env 파일이 없습니다!")
        print("   먼저 '설정하기.bat'를 실행하여 설정을 완료해주세요.\n")
        input("엔터를 누르면 종료합니다...")
        sys.exit(1)

    # 2. 첫 실행 확인 (패키지 설치)
    if not os.path.exists(".installed"):
        install_packages()

    # 3. 봇 실행
    print("🚀 봇을 시작합니다... (종료: Ctrl+C)")
    print("──────────────────────────────────────────────\n")
    
    try:
        # main.py 실행
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 봇을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        input("엔터를 누르면 종료합니다...")

if __name__ == "__main__":
    main()
