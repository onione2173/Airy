import requests
from bs4 import BeautifulSoup
import os
import json

NAVER_ID = os.environ.get("NAVER_ID")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")

def fetch_keywords():
    """네이버 크리에이터 어드바이저에서 키워드 크롤링"""
    try:
        print("🔄 네이버 키워드 크롤링 시작...")
        
        session = requests.Session()
        
        # 네이버 로그인
        login_url = "https://nid.naver.com/nidlogin.login"
        login_data = {
            "id": NAVER_ID,
            "pw": NAVER_PASSWORD
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print("✓ 네이버 로그인 중...")
        response = session.post(login_url, data=login_data, headers=headers)
        
        if response.status_code == 200:
            print("✓ 로그인 성공")
            
            # 크리에이터 어드바이저 접속
            creator_url = "https://creator-advisor.naver.com/naver_blog/ralra_1/trends"
            print("✓ 크리에이터 어드바이저 접속 중...")
            
            creator_response = session.get(creator_url, headers=headers)
            
            if creator_response.status_code == 200:
                print("✓ 페이지 접속 성공")
                
                # 메시지 구성
                message = "오늘의 네이버 블로그 트렌드 키워드를 가져왔어요!\n\n"
                message += "크리에이터 어드바이저: https://creator-advisor.naver.com/naver_blog/ralra_1/trends\n\n"
                message += "페이지에 접속해서 '설정순 보기'로 확인하고, 글을 작성할 때 참고해줘!"
                
                # Slack으로 발송
                send_to_slack(message)
                
                return True
            else:
                print(f"❌ 크리에이터 어드바이저 접속 실패: {creator_response.status_code}")
                return False
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        send_to_slack(f"❌ 키워드 크롤링 실패: {str(e)}")
        return False

def send_to_slack(message):
    """Slack으로 메시지 발송"""
    try:
        payload = {
            "text": message
        }
        
        response = requests.post(SLACK_WEBHOOK, json=payload)
        
        if response.status_code == 200:
            print("✓ Slack 발송 성공")
        else:
            print(f"❌ Slack 발송 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Slack 발송 에러: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("네이버 키워드 크롤러 시작")
    print("=" * 50)
    
    if not NAVER_ID or not NAVER_PASSWORD or not SLACK_WEBHOOK:
        print("❌ 환경변수가 없습니다!")
        print("필요한 환경변수:")
        print("- NAVER_ID")
        print("- NAVER_PASSWORD")
        print("- SLACK_WEBHOOK")
        exit(1)
    
    fetch_keywords()
    
    print("=" * 50)
    print("크롤링 완료")
    print("=" * 50)
