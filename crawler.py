import requests
from bs4 import BeautifulSoup
import os
from anthropic import Anthropic

NAVER_ID = os.environ.get("NAVER_ID")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = Anthropic()

def fetch_naver_keywords():
    """네이버 크리에이터 어드바이저 링크"""
    try:
        print("🔄 네이버 크롤링 시작...")
        
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
        
        session.post(login_url, data=login_data, headers=headers)
        
        # 크리에이터 어드바이저 접속
        creator_url = "https://creator-advisor.naver.com/naver_blog/ralra_1/trends"
        creator_response = session.get(creator_url, headers=headers)
        
        if creator_response.status_code == 200:
            print("✓ 네이버 접속 성공")
            message = "오늘의 네이버 블로그 트렌드 키워드\n크리에이터 어드바이저: https://creator-advisor.naver.com/naver_blog/ralra_1/trends\n페이지에 접속해서 '설정순 보기'로 확인하고, 글을 작성할 때 참고해줘!\n\n"
            return message
        else:
            return "❌ 네이버 크롤링 실패\n\n"
            
    except Exception as e:
        print(f"❌ 네이버 에러: {str(e)}")
        return f"❌ 네이버 크롤링 실패\n\n"

def fetch_fmkorea_posts():
    """에펨코리아 부동산 게시판 크롤링"""
    try:
        print("🔄 에펨코리아 크롤링 시작...")
        
        url = "https://www.fmkorea.com/index.php?mid=realestate&sort_index=pop&order_type=desc&listStyle=list&page=1"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✓ 에펨코리아 접속 성공")
            soup = BeautifulSoup(response.content, 'html.parser')
            posts = []
            
            # tbody 찾기
            tbody = soup.find('tbody')
            
            if tbody:
                rows = tbody.find_all('tr')
                print(f"총 {len(rows)}개 행 발견")
                
                # 모든 행에서 링크 추출
                for idx, row in enumerate(rows):
                    try:
                        tds = row.find_all('td')
                        if len(tds) > 1:
                            # td[2]에서 링크 찾기 (0-indexed이므로 1번 인덱스)
                            link_elem = tds[1].find('a')
                            if link_elem:
                                title = link_elem.get_text(strip=True)
                                href = link_elem.get('href', '')
                                
                                if title and href:
                                    full_url = f"https://www.fmkorea.com{href}" if href.startswith('/') else href
                                    posts.append({
                                        'title': title,
                                        'url': full_url
                                    })
                                    print(f"✓ 글 {len(posts)}: {title[:30]}...")
                                    
                                    if len(posts) >= 20:
                                        break
                    except Exception as e:
                        print(f"행 {idx} 파싱 실패: {e}")
                        continue
            
            print(f"✓ 총 {len(posts)}개 글 크롤링 성공")
            return posts
        else:
            print(f"❌ 에펨코리아 접속 실패: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ 에펨코리아 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def analyze_post_with_claude(title, url):
    """Claude AI로 글 분석"""
    try:
        prompt = f"""
이 블로그 글이 네이버 블로그 경제/금융 카테고리에서 좋은 글이 될 수 있는지 판단해줘.

글 제목: {title}

평가 기준:
1. 독창성과 실용성 (개인 경험/팁 포함?)
2. 호기심/논쟁 유발 가능성
3. 데이터/수치 기반 내용 가능성
4. 댓글 유도 가능성

답변 형식 (한국어로):
- 평점: 1~5점
- 추천 여부: 추천/비추천
- 간단한 이유 (1-2줄)

예시:
평점: 4점
추천 여부: 추천
이유: 실질적인 절세 팁이 있고 댓글을 유발할 만한 내용
"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"Claude 분석 에러: {str(e)}")
        return f"분석 실패"

def send_to_slack(message):
    """Slack으로 메시지 발송"""
    try:
        payload = {
            "text": message
        }
        
        response = requests.post(SLACK_WEBHOOK, json=payload)
        
        if response.status_code == 200:
            print("✓ Slack 발송 성공")
            return True
        else:
            print(f"❌ Slack 발송 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Slack 발송 에러: {str(e)}")
        return False

def main():
    print("=" * 50)
    print("아이리 (AI 리서처) 시작")
    print("=" * 50)
    
    if not NAVER_ID or not NAVER_PASSWORD or not SLACK_WEBHOOK:
        print("❌ 필수 환경변수 없음")
        return
    
    # 1. 네이버 크롤링
    print("\n[1단계] 네이버 크롤링")
    naver_message = fetch_naver_keywords()
    
    # 2. 에펨코리아 크롤링
    print("\n[2단계] 에펨코리아 크롤링")
    posts = fetch_fmkorea_posts()
    
    # 3. 상위 2개 글 분석
    print("\n[3단계] 상위 2개 글 분석")
    fmkorea_message = "오늘의 에펨코리아 부동산 인기글 추천\n\n"
    
    if len(posts) >= 2:
        for i in range(2):
            post = posts[i]
            print(f"\n분석 중: {post['title']}")
            
            analysis = analyze_post_with_claude(post['title'], post['url'])
            
            fmkorea_message += f"글 {i+1}: {post['title']}\n"
            fmkorea_message += f"링크: {post['url']}\n"
            fmkorea_message += f"분석:\n{analysis}\n\n"
    elif len(posts) > 0:
        print(f"⚠️ 크롤링된 글이 {len(posts)}개뿐입니다")
        fmkorea_message += f"크롤링된 글이 {len(posts)}개뿐입니다.\n\n"
        for i, post in enumerate(posts):
            analysis = analyze_post_with_claude(post['title'], post['url'])
            fmkorea_message += f"글 {i+1}: {post['title']}\n"
            fmkorea_message += f"링크: {post['url']}\n"
            fmkorea_message += f"분석:\n{analysis}\n\n"
    else:
        print("❌ 크롤링된 글이 없습니다")
        fmkorea_message += "❌ 크롤링 실패: 글을 찾을 수 없습니다.\n\n"
    
    # 4. Slack 발송
    print("\n[4단계] Slack 발송")
    full_message = naver_message + fmkorea_message
    
    send_to_slack(full_message)
    
    print("\n" + "=" * 50)
    print("아이리 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()
