import streamlit as st
from supabase import create_client

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

st.set_page_config(page_title="멘토-멘티 매칭 현황", page_icon="🤝", layout="wide")

# 2. 로그인 여부 검사 (1.py에서 로그인을 안 하고 이 페이지로 바로 오면 차단)
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요한 서비스입니다. 첫 번째 페이지에서 로그인을 먼저 진행해 주세요.")
    st.stop()

st.title("🤝 멘토-멘티 매칭 시스템")
st.write(f"현재 로그인: **{st.session_state.name}** ({st.session_state.student_id})")

# 3. 데이터베이스에서 모든 프로필 가져오기
try:
    profiles_res = supabase.table("profiles").select("*").execute()
    all_profiles = profiles_res.data
except Exception as e:
    st.error(f"프로필 데이터를 불러오지 못했습니다: {e}")
    all_profiles = []

# 멘토와 멘티 분리하기
mentors = [p for p in all_profiles if p.get("role") == "멘토"]
mentees = [p for p in all_profiles if p.get("role") == "멘티"]

# 4. 화면을 멘토와 멘티 탭으로 분리
tab1, tab2 = st.tabs(["👨‍🏫 등록된 멘토 목록", "👩‍🎓 등록된 멘티 목록"])

# --- [👨‍🏫 멘토 목록 탭] ---
with tab1:
    st.subheader("나에게 맞는 멘토를 찾아 신청해 보세요!")
    if not mentors:
        st.info("현재 등록된 멘토 프로필이 없습니다.")
    else:
        for mentor in mentors:
            # 멘토별로 깔끔한 카드 형태(접히는 상자) 구성
            # 리스트로 저장된 과목을 글자(텍스트)로 변환
            subjects_str = ", ".join(mentor.get("subjects", []))
            
            with st.expander(f"▶ [멘토] {mentor.get('name')} 학생 | 📚 과목: {subjects_str}"):
                st.write(f"🆔 **학번:** {mentor.get('student_id')}")
                st.write(f"⏰ **가능 시간대:** {', '.join(mentor.get('available_times', []))}")
                st.write(f"💬 **자기소개:** {mentor.get('bio')}")
                
                # 본인이 본인에게 신청하는 것 방지
                if mentor.get("student_id") == st.session_state.student_id:
                    st.button("나의 프로필입니다", disabled=True, key=f"self_{mentor.get('student_id')}")
                else:
                    # 멘토링 신청하기 버튼
                    if st.button(f"👉 {mentor.get('name')} 멘토에게 신청하기", key=f"req_{mentor.get('student_id')}"):
                        with st.spinner("신청서 전송 중..."):
                            try:
                                match_data = {
                                    "mentee_id": st.session_state.student_id,
                                    "mentor_id": mentor.get("student_id"),
                                    "status": "대기중"
                                }
                                supabase.table("matches").insert(match_data).execute()
                                st.success(f"🎉 {mentor.get('name')} 멘토에게 멘토링 신청이 완료되었습니다! 수락을 기다려주세요.")
                            except Exception as e:
                                st.error(f"신청 실패: {e}")

# --- [👩‍🎓 멘티 목록 탭] ---
with tab2:
    st.subheader("도움이 필요한 멘티들을 확인해 보세요.")
    if not mentees:
        st.info("현재 등록된 멘티 프로필이 없습니다.")
    else:
        for mentee in mentees:
            subjects_str = ", ".join(mentee.get("subjects", []))
            deadline_str = mentee.get("mentee_deadline", "기한 없음")
            
            with st.expander(f"▶ [멘티] {mentee.get('name')} 학생 | 🔍 필요 과목: {subjects_str}"):
                st.write(f"🆔 **학번:** {mentee.get('student_id')}")
                st.write(f"📅 **도움 요청 기한:** {deadline_str}")
                st.write(f"⏰ **가능 시간대:** {', '.join(mentee.get('available_times', []))}")
                st.write(f"💬 **고민 및 요청사항:** {mentee.get('bio')}")
