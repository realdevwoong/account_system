import gradio as gr
import requests
import pandas as pd

API_BASE = "http://localhost:5000"
SESSION = {"active_tab": "로그인"}  # 시작 탭: 로그인

def signup_fn(username, password, pw2, email, phone, address, birthdate):
    if not username or not password:
        return "❗ 아이디와 비밀번호는 필수입니다."
    if password != pw2:
        return "❌ 비밀번호가 일치하지 않습니다."
    res = requests.post(f"{API_BASE}/register", json={
        "username": username,
        "password": password,
        "email": email,
        "phone_number": phone,
        "address": address,
        "birthdate": birthdate
    })
    if res.status_code == 200:
        return "✅ 회원가입 성공! 로그인 해주세요."
    else:
        try:
            return f"❌ 회원가입 실패: {res.json().get('message', '에러!')}"
        except Exception:
            return f"❌ 회원가입 실패: {res.text}"

def login_fn(username, password):
    res = requests.post(f"{API_BASE}/api/login", json={
        "username": username,
        "password": password
    })
    if res.status_code == 200:
        data = res.json()
        SESSION['user_id'] = data["user_id"]
        SESSION['accounts'] = data.get("accounts", [])
        SESSION['login_pw'] = password
        SESSION["active_tab"] = "계좌/AI 챗봇"  # 탭 이동 상태 저장

        return (
            f"✅ 로그인 성공! {username} 님",
            gr.update(visible=True),   # '계좌/챗봇으로 이동' 버튼 보이기
            "",                       # 아이디 입력창 초기화
            gr.update(visible=True),   # 버튼 보이게 설정
            gr.update(value="계좌/AI 챗봇")  # 탭을 '계좌/AI 챗봇'으로 전환
        )
    else:
        SESSION["active_tab"] = "로그인"  # 실패 시 로그인 탭 유지
        return (
            "❌ 로그인 실패! 아이디/비밀번호 확인.",
            gr.update(visible=False),
            None,
            gr.update(visible=False),
            gr.update(value="로그인")
        )

def add_account(acct_num, bank, p_name, a_type, bal, ir, matd, is_fixed, monlim, autotr, note):
    if not SESSION.get("user_id"):
        return "먼저 로그인 후 사용하세요."
    res = requests.post(f"{API_BASE}/api/add_account", json={
        "user_id": SESSION["user_id"],
        "account_number": acct_num,
        "bank_name": bank,
        "balance": bal,
        "account_type": a_type,
        "interest_rate": ir,
        "maturity_date": matd,
        "product_name": p_name,
        "is_fixed_term": is_fixed,
        "monthly_limit": monlim,
        "auto_transfer": autotr,
        "note": note
    })
    if res.status_code == 200:
        acc_res = requests.post(f"{API_BASE}/api/accounts", json={"user_id": SESSION["user_id"]})
        if acc_res.status_code == 200:
            SESSION['accounts'] = acc_res.json().get("accounts", [])
        return "✅ 계좌 등록 완료!"
    else:
        try:
            return f"❌ 등록 실패: {res.json().get('message','오류')}"
        except Exception:
            return f"❌ 등록 실패: {res.text}"

def get_accounts():
    
    if not SESSION.get("user_id"):
        return pd.DataFrame()
    acc_res = requests.post(f"{API_BASE}/api/accounts", json={"user_id": SESSION["user_id"]})
    if acc_res.status_code == 200:
        SESSION['accounts'] = acc_res.json().get("accounts", [])
    accs = SESSION.get('accounts', [])
    if not accs:
        return pd.DataFrame()
    return pd.DataFrame(accs)

def ai_chat_fn(user_msg, history):
    if not SESSION.get("user_id"):
        return history + [["", "먼저 로그인 해주세요!"]]
    res = requests.post(f"{API_BASE}/ask", json={
        "user_id": SESSION["user_id"],
        "message": user_msg
    })
    if res.status_code == 200:
        answer = res.json().get("response", "AI 서버 오류")
    else:
        answer = f"❗ 서버 오류: {res.text}"
    return history + [[user_msg, answer]]

# 로그인 후 '계좌/AI 챗봇' 탭으로 이동하는 함수
def go_to_accounts():
    SESSION["active_tab"] = "계좌/AI 챗봇"
    return "계좌/AI 챗봇"

with gr.Blocks() as demo:
    gr.Markdown("## 🏦 나만의 계좌관리 & AI 상담 Gradio Demo")

    with gr.Tabs(value=SESSION.get("active_tab", "로그인")) as tabs:
        with gr.Tab("로그인"):
            with gr.Row():
                lg_user = gr.Textbox(label="아이디")
                lg_pw = gr.Textbox(label="비밀번호", type="password")
                login_btn = gr.Button("로그인")
            login_out = gr.Markdown()
            account_tab_button = gr.Button("계좌/챗봇으로 이동", visible=False)

            login_btn.click(
                login_fn,
                inputs=[lg_user, lg_pw],
                outputs=[login_out, account_tab_button, lg_user, account_tab_button, tabs],
            )

            account_tab_button.click(
                go_to_accounts,
                inputs=[],
                outputs=[tabs]
            )

        with gr.Tab("회원가입"):
            with gr.Row():
                su_name = gr.Textbox(label="아이디")
                su_pw = gr.Textbox(label="비밀번호", type="password")
                su_pw2 = gr.Textbox(label="비밀번호 확인", type="password")
            with gr.Row():
                su_email = gr.Textbox(label="이메일")
                su_phone = gr.Textbox(label="전화번호")
            with gr.Row():
                su_addr = gr.Textbox(label="주소")
                su_birth = gr.Textbox(label="생년월일(YYYY-MM-DD)")
            su_btn = gr.Button("회원가입")
            su_result = gr.Markdown()

            su_btn.click(
                signup_fn,
                [su_name, su_pw, su_pw2, su_email, su_phone, su_addr, su_birth],
                su_result,
            )

        with gr.Tab("계좌/AI 챗봇"):
            gr.Markdown("### 📒 계좌 관리")

            with gr.Row():
                acct_num = gr.Textbox(label="계좌번호")
                bank = gr.Textbox(label="은행명")
                p_name = gr.Textbox(label="상품명")

            with gr.Row():
                a_type = gr.Dropdown(
                    ["입출금", "예금", "적금", "주택청약"], label="계좌 유형"
                )
                bal = gr.Number(label="잔액")
                ir = gr.Number(label="이자율(%)")

            with gr.Row():
                matd = gr.Textbox(label="만기일(YYYY-MM-DD)")
                is_fixed = gr.Checkbox(label="만기형 계좌")
                monlim = gr.Number(label="월 납입한도")

            with gr.Row():
                autotr = gr.Checkbox(label="자동이체")
                note = gr.Textbox(label="비고")

            add_btn = gr.Button("계좌 추가")
            add_result = gr.Markdown()
            add_btn.click(
                add_account,
                [
                    acct_num,
                    bank,
                    p_name,
                    a_type,
                    bal,
                    ir,
                    matd,
                    is_fixed,
                    monlim,
                    autotr,
                    note,
                ],
                add_result,
            )

            accts_tbl = gr.Dataframe(label="현재 계좌 목록")
            show_acc_btn = gr.Button("계좌 새로고침")
            show_acc_btn.click(get_accounts, outputs=accts_tbl)

            gr.Markdown("### 🤖 금융 AI 챗봇")
            chatbot = gr.Chatbot()
            usermsg_input = gr.Textbox(label="질문 입력")
            chat_btn = gr.Button("AI 상담받기")
            chat_btn.click(ai_chat_fn, [usermsg_input, chatbot], chatbot)

demo.launch()
