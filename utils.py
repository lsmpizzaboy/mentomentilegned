import streamlit as st

# 💡 [최적화 핵심] 프로필 데이터 캐싱 함수
# @st.cache_data(ttl=60)은 "이 함수가 불러온 결과값을 60초 동안 메모리에 저장(캐시)해둬!"라는 뜻입니다.
# _supabase처럼 앞에 언더바(_)를 붙이면, 스트림릿이 캐시할 때 이 변수는 무시해서 에러가 나지 않습니다.
@st.cache_data(ttl=60)
def get_cached_profiles(_supabase):
    try:
        # select("*")를 써도 캐싱 덕분에 DB에 부담이 전혀 가지 않습니다.
        res = _supabase.table("profiles").select("*").execute()
        return res.data
    except Exception:
        return []

# 기존 통합 알림 센터 함수 (버그 우회 적용 버전)
def render_global_notification_center(supabase):
    st.sidebar.markdown("---") 
    
    try:
        student_id = st.session_state.student_id
        
        # [A] 매칭 요청
        mentor_req = supabase.table("matches").select("id, mentee_id").eq("mentor_id", student_id).eq("status", "대기중").execute()
        pending_matches = mentor_req.data
        
        # [B] 안 읽은 채팅 (or_ 에러 완벽 우회)
        res1 = supabase.table("matches").select("id").eq("mentor_id", student_id).execute()
        res2 = supabase.table("matches").select("id").eq("mentee_id", student_id).execute()
        
        my_match_ids = [m["id"] for m in res1.data] + [m["id"] for m in res2.data]
        
        unread_chats = []
        if my_match_ids:
            chat_res = supabase.table("chat_messages").select("*").in_("match_id", my_match_ids).eq("is_read", False).neq("sender_id", student_id).execute()
            unread_chats = chat_res.data
            
        # [C] QnA 댓글
        my_posts_res = supabase.table("qna_board").select("id, title").eq("author_id", student_id).execute()
        my_post_ids = [p["id"] for p in my_posts_res.data]
        
        recent_comments = []
        if my_post_ids:
            comments_res = supabase.table("qna_comments").select("*").in_("post_id", my_post_ids).order("created_at", desc=True).limit(5).execute()
            recent_comments = comments_res.data

        total_notifications = len(pending_matches) + len(unread_chats) + len(recent_comments)
        badge = f" 🔴 ({total_notifications})" if total_notifications > 0 else ""
        
        with st.sidebar.popover(f"🔔 실시간 알림 센터{badge}", use_container_width=True):
            st.markdown("### 🗂️ 새로운 소식")
            
            if total_notifications == 0:
                st.caption("새로운 알림이 없습니다. 아주 평화롭네요! ✨")
                
            if pending_matches:
                st.markdown("**🤝 멘토링 요청**")
                for m in pending_matches:
                    st.info(f"🙋‍♂️ `{m['mentee_id']}` 학생이 멘토링 신청을 보냈습니다! [매칭 시스템] 메뉴를 확인하세요.")
            
            if unread_chats:
                st.markdown("**💬 안 읽은 메시지**")
                unique_match_ids = set([c["match_id"] for c in unread_chats])
                st.warning(f"현재 답변을 기다리는 대화방이 {len(unique_match_ids)}개 있습니다.")
                
            if recent_comments:
                st.markdown("**💡 내 질문에 달린 댓글**")
                post_title_dict = {p["id"]: p["title"] for p in my_posts_res.data}
                for c in recent_comments:
                    p_title = post_title_dict.get(c["post_id"], "내 질문")
                    st.caption(f"📌 '{p_title}' 글에 새로운 답변이 등록되었습니다.")
                    st.write(f"👉 {c['comment']}")

    except Exception as e:
        st.sidebar.caption("알림을 불러오는 중 오류가 발생했습니다.")
