import streamlit as st

# 페이지 설정 (사이드바 메뉴판이 렌더링되기 전에 가장 먼저 실행됨)
st.set_page_config(page_title="교내 멘토-멘티 시스템", page_icon="🏫", layout="wide")

# ==========================================
# 💡 사이드바 메뉴 카테고리 분류 및 간격 설정
# ==========================================
# 딕셔너리({ }) 구조를 사용하면 자동으로 카테고리 간격이 예쁘게 떨어집니다!
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
        st.Page("pages/5_QnA게시판.py", title="실시간 QnA 질문방", icon="💬"),
    ]
}

# 네비게이션 실행 및 화면에 그리기
pg = st.navigation(pages)
pg.run()
