import streamlit as st

# 페이지 설정
st.set_page_config(page_title="교내 멘토-멘티 시스템", page_icon="🏫", layout="wide")

# ==========================================
# 💡 사이드바 메뉴 카테고리 분류 및 간격 설정
# ==========================================
# 주의: 아래 "pages/..." 부분의 파일 이름이 깃허브에 있는 실제 파일 이름과 대소문자, 띄어쓰기까지 100% 똑같아야 합니다!
pages = {
    "🏫 서비스 시작": [
        st.Page("pages/1_프로필등록.py", title="프로필 등록 및 홈", icon="📝"),
        st.Page("pages/2_매칭시스템.py", title="멘토-멘티 매칭", icon="🤝"),
    ],
    "🧑‍🤝‍🧑 나의 활동 (관리실)": [
        st.Page("pages/3_나의_멘티.py", title="나의 멘티 (멘토용)", icon="👨‍🏫"),
        st.Page("pages/4_나의_멘토.py", title="나의 멘토 (멘티용)", icon="👩‍🎓"),
    ],
    "💡 학교 커뮤니티": [
        # 대문자 QnA가 아니라 유저님이 만드신 Qna로 수정 완료!
        st.Page("pages/5_Qna게시판.py", title="실시간 QnA 질문방", icon="💬"), 
    ]
}

# 네비게이션 실행 및 화면에 그리기
pg = st.navigation(pages)
pg.run()
