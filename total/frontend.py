import streamlit as st
import requests
import pandas as pd
from datetime import date

API_BASE = "http://127.0.0.1:5000"  # 필요한 경우 실제 서버 주소로 변경

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "register_mode" not in st.session_state: # 회원가입 화면 여부
    st.session_state.register_mode = False
if "user_id" not in st.session_state: # 로그인된 사용자의 고유 ID
    st.session_state.user_id = None
if "accounts" not in st.session_state: # 계좌 정보 리스트
    st.session_state.accounts = []
if "ai_mode" not in st.session_state:  # AI 챗봇 모드 여부
    st.session_state.ai_mode = False
if "messages" not in st.session_state: # 챗봇 대화 메시지 기록
    st.session_state.messages = [] 
if "login_pw" not in st.session_state: # 로그인 시 사용한 비밀번호 (재요청에 사용)
    st.session_state.login_pw = ""
# 🔐 로그인 화면
def show_login():
    st.header("🔐 나만의 자산관리 프로그램")
    with st.form("login_form_main"):
        username = st.text_input("아이디", key="login_id")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        col1, col2 = st.columns([1, 1])
        with col1:
            login_btn = st.form_submit_button("로그인", use_container_width=True) # 버튼이 화면 전체 폭을 차지
        with col2:
            join_btn = st.form_submit_button("회원가입", use_container_width=True)

    if login_btn:
        if not username or not password:
            st.error("아이디와 비밀번호를 입력하세요.")
        else:
            try:
                res = requests.post(f"{API_BASE}/api/login", json={
                    "username": username,
                    "password": password
                })
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.user_id = data["user_id"]
                    st.session_state.accounts = data.get("accounts", [])
                    st.success("✅ 로그인 성공!")
                    st.rerun() #새 상태를 반영해서 전체 앱이 다시 실행
                else:
                    st.error("❌ 로그인 실패: 아이디 또는 비밀번호를 확인하세요.")
            except Exception as e:
                st.error(f"서버 오류 발생: {e}")

    if join_btn:
        st.session_state.register_mode = True
        st.rerun()

# ✍️ 회원가입 화면
def show_register():
    st.header("✍️ 회원가입")
    with st.form("register_form_main"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        pw2 = st.text_input("비밀번호 확인", type="password")
        email = st.text_input("이메일")
        phone = st.text_input("전화번호")
        address = st.text_input("주소")
        # birthdate = st.date_input("생년월일")
        birthdate = st.date_input(
            "생년월일",
            value=date(1990, 1, 1),          # 기본 표시 날짜(예시)
            min_value=date(1900, 1, 1),      # 최소 선택 가능 날짜
            max_value=date.today()           # 최대 선택 가능 날짜(오늘)
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("가입하기", use_container_width=True)
        with col2:
            back = st.form_submit_button("로그인으로 돌아가기", use_container_width=True)

    if submit:
        if not username or not password:
            st.error("❗ 아이디와 비밀번호는 필수입니다.")
        elif password != pw2:
            st.error("❌ 비밀번호가 일치하지 않습니다.")
        else:
            try:
                res = requests.post(f"{API_BASE}/register", json={
                    "username": username,
                    "password": password,
                    "email": email,
                    "phone_number": phone,
                    "address": address,
                    "birthdate": str(birthdate)
                })

                try:
                    response_data = res.json()
                    if res.status_code == 200:
                        st.success(response_data.get("message", "✅ 회원가입 성공!"))
                        st.session_state.register_mode = False
                        st.rerun()
                    else:
                        st.error(response_data.get("message", "❌ 회원가입 실패"))
                except ValueError:
                    st.error("❌ 서버 응답이 JSON 형식이 아닙니다.")
                    st.text(f"서버 응답 원문:\n{res.text}")
            except Exception as e:
                st.error(f"❗ 서버 통신 오류 발생: {e}")

    if back:
        st.session_state.register_mode = False
        st.rerun()

# 📊 메인 대시보드 (계좌/로그아웃/AI 분석)
def show_main():
    st.success(f"🎉 {st.session_state.current_user}님, 환영합니다!")

    # ➕ 새 계좌 등록
    st.subheader("➕ 새 계좌 등록")
    with st.form("add_account_form"):
        account_number = st.text_input("계좌번호")
        bank_name = st.text_input("은행명")
        account_type = st.selectbox("계좌유형", ["입출금", "적금", "정기예금", "주택청약"])
        balance = st.number_input("잔액", min_value=0.0, step=1000.0)
        interest_rate = st.number_input("이자율(%)", min_value=0.0, step=0.1)
        maturity_date = st.date_input("만기일")
        product_name = st.text_input("상품명")
        is_fixed_term = st.checkbox("만기형 계좌")
        monthly_limit = st.number_input("월 납입한도", min_value=0.0, step=1000.0)
        auto_transfer = st.checkbox("자동이체 여부")
        note = st.text_area("비고")
        submitted = st.form_submit_button("계좌 추가")

    if submitted:
        try:
            # 👉 POST 요청으로 계좌 등록
            res = requests.post(f"{API_BASE}/api/add_account", json={
                "user_id": st.session_state.user_id,
                "account_number": account_number,
                "bank_name": bank_name,
                "balance": balance,
                "account_type": account_type,
                "interest_rate": interest_rate,
                "maturity_date": maturity_date.strftime("%Y-%m-%d"),
                "product_name": product_name,
                "is_fixed_term": is_fixed_term,
                "monthly_limit": monthly_limit,
                "auto_transfer": auto_transfer,
                "note": note
            })

            if res.status_code == 200:
                st.success("✅ 계좌가 등록되었습니다!")

                # 🔄 계좌 다시 불러오기 (📌 이게 핵심!)
                acc_res = requests.post(f"{API_BASE}/api/accounts", json={
                    "user_id": st.session_state.user_id
                })

                if acc_res.status_code == 200:
                    st.session_state.accounts = acc_res.json().get("accounts", [])
                else:
                    st.warning("계좌 새로고침 실패")

                st.rerun()  # 📢 화면 갱신!

                # 🔄 계좌 정보 갱신을 위해 로그인 다시 호출
                login_res = requests.post(f"{API_BASE}/api/login", json={
                    "username": st.session_state.current_user,
                    "password": st.session_state.login_pw  # 주의: session_state에 있어야 함
                })

                if login_res.status_code == 200:
                    data = login_res.json()
                    st.session_state.accounts = data.get("accounts", [])
                else:
                    st.warning("등록은 되었지만 계좌 재불러오기에 실패했습니다.")

                st.rerun()

            else:
                try:
                    error_msg = res.json().get("message", "서버 오류 발생")
                except Exception:
                    error_msg = res.text or "서버 오류 또는 JSON 파싱 실패"
                st.error(f"❌ 등록 실패: {error_msg}")

        except Exception as e:
            st.error(f"🔥 요청 중 오류 발생: {str(e)}")

    st.markdown("---")

    # ▶ 기존 계좌 출력
    if st.session_state.accounts:
        st.subheader("📒 현재 계좌 정보")
        df = pd.DataFrame(st.session_state.accounts)
        df = df.rename(columns={
            "account_number": "계좌번호",
            "bank_name": "은행명",
            "product_name": "상품명",
            "account_type": "계좌유형",
            "balance": "잔액",
            "interest_rate": "이자율(%)",
            "maturity_date": "만기일",
            "monthly_limit": "월 납입한도",
            "auto_transfer": "자동이체여부",
            "note": "비고"
        })
        st.dataframe(df, use_container_width=True)
    else:
        st.info("등록된 계좌 정보가 없습니다.")

    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🧠 AI 분석하러 가기", use_container_width=True):
            st.session_state.ai_mode = True
            st.rerun()

    with col2:
        if st.button("🔓 로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                if not key.startswith("FormSubmitter"):
                    st.session_state[key] = None
            st.rerun()
def show_ai_chat():
    st.title("💬 AI 금융 분석 챗봇")
    st.markdown("💡 질문을 입력하시면 AI가 분석하여 답변을 제공합니다.")

    st.markdown("---")

    for idx, msg in enumerate(st.session_state.messages):
        with st.container():
            if msg["role"] == "user":
                st.markdown(
                    f"""
                    <div style='background-color:#F0F0F0; padding:10px; border-radius:8px; margin-bottom:5px; width:fit-content; max-width:80%;'>
                        <b>질문:</b><br>{msg["content"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                      f"""
                      <div style='
                          background-color:#2B2B2BE;
                          padding:10px;
                          border-radius:8px;
                          margin-bottom:10px;
                          width:fit-content;
                          max-width:80%;
                          '>
                          <b>답변:</b><br>{msg["content"]}
                      </div>
                      """,
                      unsafe_allow_html=True
                  )

    # ✍️ 사용자 입력
    user_input = st.text_area("질문 입력", height=100, key="input_box")

    if st.button("전송"):
        if user_input.strip():
            # 사용자 질문 추가
            st.session_state.messages.append({"role": "user", "content": user_input})

            # 서버로 질문 전송
            try:
                res = requests.post(f"{API_BASE}/ask", json={
                    "user_id": st.session_state.user_id,
                    "message": user_input
                })
                if res.status_code == 200:
                    answer = res.json()["response"]
                else:
                    answer = "❗ 서버 응답 오류가 발생했습니다."
            except Exception as e:
                answer = f"❌ 서버 오류: {e}"

            # 답변 저장
            st.session_state.messages.append({"role": "assistant", "content": answer})

            st.rerun()

    st.divider()

    if st.button("🏠 대시보드로 돌아가기", use_container_width=True):
        st.session_state.ai_mode = False
        st.rerun()
# 📍 실행 분기
if not st.session_state.logged_in:
    if st.session_state.register_mode:
        show_register()
    else:
        show_login()
elif st.session_state.ai_mode:
    show_ai_chat()
else:
    show_main()
