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

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요한 서비스입니다. 첫 번째 페이지에서 로그인을 먼저 진행해 주세요.")
    st.stop()

st.title("🤝 멘토-멘티 매칭 시스템")
st.write(f"현재 로그인: **{st.session_state.name}** ({st.session_state.student_id})")

# 2. 데이터베이스에서 모든 프로필 가져오기
try:
    profiles_res = supabase.table("profiles").select("*").execute()
    all_profiles = profiles_res.data
except Exception as e:
    st.error(f"프로필 데이터를 불러오지 못했습니다: {e}")
    all_profiles = []

# ==========================================
# 🚀 [새로운 기능] 나에게 도착한 멘토링 요청 우편함
# ==========================================
st.markdown("### 📬 나에게 도착한 멘토링 요청")
try:
    # 내 학번이 멘토로 지정되어 있고, 아직 상태가 '대기중'인 신청서만 찾아옵니다.
    req_res = supabase.table("matches").select("*").eq("mentor_id", st.session_state.student_id).eq("status", "대기중").execute()
    my_requests = req_res.data
    
    if not my_requests:
        st.info("아직 도착한 멘토링 신청이 없습니다.")
    else:
        for req in my_requests:
            # 신청한 멘티의 프로필 정보 찾기
            mentee_profile = next((p for p in all_profiles if p["student_id"] == req["mentee_id"]), None)
            mentee_name = mentee_profile["name"] if mentee_profile else "알 수 없는 멘티"
            
            # 도착한 요청을 보여주는 알림 상자
            with st.expander(f"🔔 {mentee_name} ({req['mentee_id']}) 학생이 멘토링을 신청했습니다!", expanded=True):
                if mentee_profile:
                    st.write(f"**🔍 도움이 필요한 과목:** {', '.join(mentee_profile.get('subjects', []))}")
                    st.write(f"**💬 멘티의 고민/요청:** {mentee_profile.get('bio', '')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    # [수락] 버튼: 누르면 데이터베이스의 상태를 '수락됨'으로 바꿈
                    if st.button("✅ 수락하기", key=f"acc_{req['id']}", use_container_width=True):
                        supabase.table("matches").update({"status": "수락됨"}).eq("id", req["id"]).execute()
                        st.success("멘토링을 수락했습니다! (이제 채팅이나 연락을 시작할 수 있습니다.)")
                        st.rerun() # 버튼을 누르면 화면을 새로고침하여 목록에서 지웁니다.
                with col2:
                    # [거절] 버튼: 누르면 데이터베이스의 상태를 '거절됨'으로 바꿈
                    if st.button("❌ 거절하기", key=f"rej_{req['id']}", use_container_width=True):
                        supabase.table("matches").update({"status": "거절됨"}).eq("id", req["id"]).execute()
                        st.warning("멘토링 신청을 정중히 거절했습니다.")
                        st.rerun()
except Exception as e:
    st.error(f"요청 내역을 불러오는 중 오류가 발생했습니다: {e}")

st.markdown("---")

# ==========================================
# 3. 멘토/멘티 목록 필터링 및 보여주기
# ==========================================

# [새로운 로직] 이미 매칭이 완료된(수락됨) 멘티들의 학번을 데이터베이스에서 찾아냅니다.
try:
    accepted_res = supabase.table("matches").select("mentee_id").eq("status", "수락됨").execute()
    # 수락된 멘티들의 학번만 모아서 하나의 리스트로 만듭니다. (예: ["30516", "10101"])
    accepted_mentee_ids = [match["mentee_id"] for match in accepted_res.data]
except Exception as e:
    st.error(f"매칭 완료 데이터를 불러오지 못했습니다: {e}")
    accepted_mentee_ids = []

# 멘토 목록은 그대로 가져옵니다.
mentors = [p for p in all_profiles if p.get("role") == "멘토"]

# 멘티 목록은 '수락된 멘티 명단(accepted_mentee_ids)'에 없는 학생만 걸러서 가져옵니다.
mentees = [p for p in all_profiles if p.get("role") == "멘티" and p.get("student_id") not in accepted_mentee_ids]

tab1, tab2 = st.tabs(["👨‍🏫 등록된 멘토 목록", "👩‍🎓 등록된 멘티 목록"])

# (이 아래부터는 기존의 with tab1: 과 with tab2: 코드를 그대로 두시면 됩니다!)

# --- [👨‍🏫 멘토 목록 탭] ---
with tab1:
    st.subheader("나에게 맞는 멘토를 찾아 신청해 보세요!")
    if not mentors:
        st.info("현재 등록된 멘토 프로필이 없습니다.")
    else:
        for mentor in mentors:
            subjects_str = ", ".join(mentor.get("subjects", []))
            with st.expander(f"▶ [멘토] {mentor.get('name')} 학생 | 📚 과목: {subjects_str}"):
                st.write(f"🆔 **학번:** {mentor.get('student_id')}")
                st.write(f"⏰ **가능 시간대:** {', '.join(mentor.get('available_times', []))}")
                st.write(f"💬 **자기소개:** {mentor.get('bio')}")
                
                if mentor.get("student_id") == st.session_state.student_id:
                    st.button("나의 프로필입니다", disabled=True, key=f"self_{mentor.get('student_id')}")
                else:
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
