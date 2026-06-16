import streamlit as st
from supabase import create_client
import base64

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요합니다.")
    st.stop()

# ==========================================
# [채팅방 화면 모드]
# ==========================================
if "current_chat_match" in st.session_state:
    match = st.session_state.current_chat_match
    st.subheader(f"💬 {match['partner_name']} 멘티와의 대화")
    
    if st.button("◀ 목록으로 돌아가기"):
        del st.session_state.current_chat_match
        st.rerun()
        
    # 읽음 처리
    supabase.table("chat_messages").update({"is_read": True}).eq("match_id", match['id']).neq("sender_id", st.session_state.student_id).execute()
    
    # 채팅 내역 불러오기
    chat_res = supabase.table("chat_messages").select("*").eq("match_id", match['id']).order("created_at", desc=False).execute()
    messages = chat_res.data
    
    # 채팅창 출력
    chat_box = st.container(height=400)
    with chat_box:
        if not messages:
            st.info("아직 나눈 대화가 없습니다. 먼저 인사를 건네보세요!")
        for msg in messages:
            is_me = (msg["sender_id"] == st.session_state.student_id)
            
            # 💡 [기능 1] 로봇 대신 실제 보낸 사람의 이름을 말아주기
            sender_label = f"🙋‍♂️ {st.session_state.name} (나)" if is_me else f"👨‍🎓 {match['partner_name']}"
            
            with st.chat_message("user" if is_me else "assistant", avatar="🧑‍💻" if is_me else "📝"):
                st.write(f"**{sender_label}**")
                
                # 💡 [기능 2] 만약 메시지가 이미지 데이터라면 이미지로 렌더링
                if msg["message"].startswith("DATA_IMAGE:"):
                    img_base64 = msg["message"].replace("DATA_IMAGE:", "")
                    st.image(f"data:image/png;base64,{img_base64}", use_container_width=True)
                else:
                    st.write(msg["message"])
                
    # 💡 [기능 2] 사진 파일 업로더 추가
    with st.expander("📸 사진 보내기"):
        uploaded_file = st.file_uploader("이미지 파일을 선택하세요 (jpg, jpeg, png)", type=["png", "jpg", "jpeg"], key="img_uploader")
        if uploaded_file:
            if st.button("🚀 선택한 사진 전송하기"):
                file_bytes = uploaded_file.read()
                base64_str = base64.b64encode(file_bytes).decode("utf-8")
                supabase.table("chat_messages").insert({
                    "match_id": match['id'],
                    "sender_id": st.session_state.student_id,
                    "message": f"DATA_IMAGE:{base64_str}"
                }).execute()
                st.rerun()

    # 텍스트 메시지 입력창
    prompt = st.chat_input("메시지를 입력하세요...")
    if prompt:
        supabase.table("chat_messages").insert({
            "match_id": match['id'],
            "sender_id": st.session_state.student_id,
            "message": prompt
        }).execute()
        st.rerun()
        
    st.stop()

# ==========================================
# [목록 화면 모드] 기본 화면
# ==========================================
st.title("👨‍🏫 나의 멘티 관리실")

try:
    my_mentees_res = supabase.table("matches").select("*").eq("mentor_id", st.session_state.student_id).eq("status", "수락됨").execute()
    my_mentees = my_mentees_res.data
    
    profiles_res = supabase.table("profiles").select("*").execute()
    profile_dict = {p["student_id"]: p for p in profiles_res.data}
    
    if not my_mentees:
        st.info("현재 매칭되어 진행 중인 멘티가 없습니다.")
    else:
        for match in my_mentees:
            mentee_id = match["mentee_id"]
            mentee_profile = profile_dict.get(mentee_id, {})
            mentee_name = mentee_profile.get("name", "알 수 없는 멘티")
            
            unread_res = supabase.table("chat_messages").select("id", count="exact").eq("match_id", match["id"]).eq("is_read", False).neq("sender_id", st.session_state.student_id).execute()
            unread_count = unread_res.count
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    alert = f" 🔴 **새 메시지 {unread_count}건**" if unread_count > 0 else ""
                    st.write(f"**9️⃣ 학번:** {mentee_id} | **👤 이름:** {mentee_name} {alert}")
                    
                    # 💡 [기능 3] 관리창에서 상대방 프로필 즉시 보기
                    with st.expander("🔍 이 멘티의 프로필 상세보기"):
                        st.write(f"📚 **요청 과목:** {', '.join(mentee_profile.get('subjects', []))}")
                        st.write(f"⏰ **가능 시간대:** {', '.join(mentee_profile.get('available_times', []))}")
                        st.write(f"📅 **도움 요청 기한:** {mentee_profile.get('mentee_deadline', '없음')}")
                        st.write(f"💬 **고민 내용:** {mentee_profile.get('bio', '')}")
                        
                with col2:
                    if st.button("💬 채팅방 입장", key=f"chat_{match['id']}", use_container_width=True):
                        st.session_state.current_chat_match = {"id": match["id"], "partner_name": mentee_name}
                        st.rerun()
                with col3:
                    if st.button("🏁 멘토링 종료", key=f"end_{match['id']}", use_container_width=True):
                        supabase.table("matches").update({"status": "종료됨"}).eq("id", match["id"]).execute()
                        st.success("멘토링을 성공적으로 종료했습니다.")
                        st.rerun()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
