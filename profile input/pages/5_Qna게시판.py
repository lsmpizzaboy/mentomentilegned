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
    st.warning("🔒 로그인이 필요한 서비스입니다.")
    st.stop()

st.title("💡 실시간 Q&A 질문게시판")
st.write("모르는 문제를 올리거나, 다른 친구들의 질문에 답변을 달아주세요!")

# 프로필 정보 가져오기 (작성자 이름 표시용)
try:
    profiles_res = supabase.table("profiles").select("student_id, name").execute()
    profile_dict = {p["student_id"]: p["name"] for p in profiles_res.data}
except:
    profile_dict = {}

# ==========================================
# [상단] 새 질문 작성하기 영역
# ==========================================
with st.expander("📝 새로운 질문 작성하기"):
    with st.form("new_post_form", clear_on_submit=True):
        new_title = st.text_input("제목 (어떤 과목/내용인지 간략히 적어주세요)")
        new_content = st.text_area("질문 내용", height=150)
        uploaded_image = st.file_uploader("사진 첨부 (선택사항)", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("🚀 질문 등록하기"):
            if new_title and new_content:
                image_base64 = None
                if uploaded_image:
                    image_base64 = base64.b64encode(uploaded_image.read()).decode("utf-8")
                
                post_data = {
                    "author_id": st.session_state.student_id,
                    "title": new_title,
                    "content": new_content,
                    "image_data": f"DATA_IMAGE:{image_base64}" if image_base64 else None
                }
                supabase.table("qna_board").insert(post_data).execute()
                st.success("질문이 등록되었습니다!")
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해 주세요.")

st.markdown("---")

# ==========================================
# [하단] 질문 목록 및 댓글 영역
# ==========================================
st.subheader("📋 전체 질문 목록")

try:
    # 모든 게시글과 댓글 불러오기 (최신 글이 위로 오도록 내림차순 정렬)
    posts_res = supabase.table("qna_board").select("*").order("created_at", desc=True).execute()
    posts = posts_res.data
    
    comments_res = supabase.table("qna_comments").select("*").order("created_at", desc=False).execute()
    all_comments = comments_res.data
    
    if not posts:
        st.info("아직 등록된 질문이 없습니다. 첫 번째 질문의 주인공이 되어보세요!")
    else:
        for post in posts:
            author_name = profile_dict.get(post["author_id"], "알 수 없는 사용자")
            
            # 이 게시글에 달린 댓글만 필터링
            post_comments = [c for c in all_comments if c["post_id"] == post["id"]]
            comment_count = len(post_comments)
            
            # 접이식 상자로 간략한 제목만 표시
            with st.expander(f"📌 {post['title']}  |  👤 {author_name}  |  💬 댓글 {comment_count}개"):
                
                # 1. 본문 내용 표시
                st.write(post["content"])
                
                # 2. 이미지가 있다면 화면에 꽉 차지 않게 width 제한하여 출력
                if post.get("image_data"):
                    img_base64 = post["image_data"].replace("DATA_IMAGE:", "")
                    st.image(f"data:image/png;base64,{img_base64}", width=400) # 가로 400픽셀로 고정!
                
                st.divider()
                
                # 3. 댓글 목록 표시
                st.markdown("**💬 댓글**")
                if not post_comments:
                    st.caption("아직 댓글이 없습니다.")
                else:
                    for c in post_comments:
                        c_author_name = profile_dict.get(c["author_id"], "알 수 없는 사용자")
                        st.markdown(f"- **{c_author_name}**: {c['comment']}")
                
                # 4. 새 댓글 달기 (고유한 key 부여)
                col1, col2 = st.columns([4, 1])
                with col1:
                    comment_input = st.text_input("댓글 남기기", key=f"input_{post['id']}", label_visibility="collapsed")
                with col2:
                    if st.button("등록", key=f"btn_{post['id']}", use_container_width=True):
                        if comment_input:
                            supabase.table("qna_comments").insert({
                                "post_id": post["id"],
                                "author_id": st.session_state.student_id,
                                "comment": comment_input
                            }).execute()
                            st.rerun()

except Exception as e:
    st.error(f"게시판 데이터를 불러오는 중 오류가 발생했습니다: {e}")
