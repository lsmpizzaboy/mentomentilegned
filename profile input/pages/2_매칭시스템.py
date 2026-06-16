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
    st.warning("🔒 로그인이 필요한 서비스입니다.")
    st.stop()

st.title("🤝 멘토-멘티 매칭 시스템")
st.write(f"현재 로그인: **{st.session_state.name}** ({st.session_state.student_id})")

# 2. 프로필 및 별점 데이터 가져오기
try:
    profiles_res = supabase.table("profiles").select("*").execute()
    all_profiles = profiles_res.data
except Exception as e:
    st.error(f"프로필 오류: {e}")
    all_profiles = []

# ==========================================
# 💡 [새로운 기능] 멘토들의 평균 별점 계산기
# ==========================================
try:
    # 멘티들이 남긴 별점(rating)이 있는 매칭 내역만 전부 가져옵니다.
    ratings_res = supabase.table("matches").select("mentor_id, rating").execute()
    rated_data = [m for m in ratings_res.data if m.get("rating") is not None]
    
    avg_ratings = {}
    for r in rated_data:
        m_id = r["mentor_id"]
        if m_id not in avg_ratings:
            avg_ratings[m_id] = []
        avg_ratings[m_id].append(r["rating"])
        
    # 평균 점수 내기
    for m_id in avg_ratings:
        avg_ratings[m_id] = sum(avg_ratings[m_id]) / len(avg_ratings[m_id])
except Exception:
    avg_ratings = {}

# ==========================================
# 📬 나에게 도착한 멘토링 요청 우편함 (멘토 전용)
# ==========================================
st.markdown("### 📬 나에게 도착한 멘토링 요청")
try:
    req_res = supabase.table("matches").select("*").eq("mentor_id", st.session_state.student_id).eq("status", "대기중").execute()
    my_requests = req_res.data
    
    if not my_requests:
        st.info("아직 도착한 멘토링 신청이 없습니다.")
    else:
        for req in my_requests:
            mentee_profile = next((p for p in all_profiles if p["student_id"] == req["mentee_id"] and p["role"] == "멘티"), None)
            mentee_name = mentee_profile["name"] if mentee_profile else "알 수 없는 멘티"
            
            with st.expander(f"🔔 {mentee_name} ({req['mentee_id']}) 학생이 멘토링을 신청했습니다!", expanded=True):
                if mentee_profile:
                    st.write(f"**🔍 도움이 필요한 과목:** {', '.join(mentee_profile.get('subjects', []))}")
                    st.write(f"**💬 멘티의 고민/요청:** {mentee_profile.get('bio', '')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 수락하기", key=f"acc_{req['id']}", use_container_width=True):
                        supabase.table("matches").update({"status": "수락됨"}).eq("id", req["id"]).execute()
                        st.rerun()
                with col2:
                    if st.button("❌ 거절하기", key=f"rej_{req['id']}", use_container_width=True):
                        supabase.table("matches").update({"status": "거절됨"}).eq("id", req["id"]).execute()
                        st.rerun()
except Exception:
    pass

st.markdown("---")

# ==========================================
# 3. 멘토/멘티 목록 필터링
# ==========================================
try:
    accepted_res = supabase.table("matches").select("mentee_id").eq("status", "수락됨").execute()
    accepted_mentee_ids = [match["mentee_id"] for match in accepted_res.data]
except:
    accepted_mentee_ids = []

try:
    my_active_reqs = supabase.table("matches").select("mentor_id").eq("mentee_id", st.session_state.student_id).in_("status", ["대기중", "수락됨"]).execute()
    already_applied_mentor_ids = [m["mentor_id"] for m in my_active_reqs.data]
except:
    already_applied_mentor_ids = []

mentors = [p for p in all_profiles if p.get("role") == "멘토"]
mentees = [p for p in all_profiles if p.get("role") == "멘티" and p.get("student_id") not in accepted_mentee_ids]

tab1, tab2 = st.tabs(["👨‍🏫 등록된 멘토 목록", "👩‍🎓 등록된 멘티 목록"])

# --- [👨‍🏫 멘토 목록 탭] ---
with tab1:
    st.subheader("나에게 맞는 멘토를 찾아 신청해 보세요!")
    if not mentors:
        st.info("현재 등록된 멘토 프로필이 없습니다.")
    else:
        for mentor in mentors:
            mentor_id = mentor.get("student_id")
            
            # 💡 평균 별점 예쁘게 표시하기
            avg_score = avg_ratings.get(mentor_id, 0)
            if avg_score > 0:
                star_display = f"{'⭐' * int(round(avg_score))} ({avg_score:.1f} / 5.0점)"
            else:
                star_display = "아직 평가 없음 (첫 평가자가 되어보세요!)"
                
            with st.expander(f"▶ [멘토] {mentor.get('name')} | 📊 평점: {star_display}"):
                st.write(f"🆔 **학번:** {mentor_id}")
                st.write(f"📚 **과목:** {', '.join(mentor.get('subjects', []))}")
                st.write(f"⏰ **가능 시간대:** {', '.join(mentor.get('available_times', []))}")
                st.write(f"💬 **자기소개:** {mentor.get('bio')}")
                
                if mentor_id == st.session_state.student_id:
                    st.button("나의 프로필입니다", disabled=True, key=f"self_{mentor_id}")
                elif mentor_id in already_applied_mentor_ids:
                    st.button("🔒 이미 신청했거나 진행 중인 멘토입니다", disabled=True, key=f"already_{mentor_id}")
                else:
                    if st.button(f"👉 {mentor.get('name')} 멘토에게 신청하기", key=f"req_{mentor_id}"):
                        try:
                            supabase.table("matches").insert({"mentee_id": st.session_state.student_id, "mentor_id": mentor_id, "status": "대기중"}).execute()
                            st.success(f"🎉 신청이 완료되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error("신청 실패")

# --- [👩‍🎓 멘티 목록 탭] ---
with tab2:
    st.subheader("도움이 필요한 멘티들을 확인해 보세요.")
    if not mentees:
        st.info("현재 등록된 멘티 프로필이 없습니다.")
    else:
        for mentee in mentees:
            with st.expander(f"▶ [멘티] {mentee.get('name')} | 🔍 필요 과목: {', '.join(mentee.get('subjects', []))}"):
                st.write(f"🆔 **학번:** {mentee.get('student_id')}")
                st.write(f"📅 **기한:** {mentee.get('mentee_deadline', '기한 없음')}")
                st.write(f"⏰ **시간대:** {', '.join(mentee.get('available_times', []))}")
                st.write(f"💬 **요청사항:** {mentee.get('bio')}")
