from flask import Flask, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection
import os
import requests
from requests.exceptions import Timeout, HTTPError, RequestException, ConnectionError as ReqConnectionError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)

bcrypt = Bcrypt(app)

AI_ENDPOINT = os.getenv("AI_ENDPOINT", "http://aiserver:8000/ai")
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "60"))  # 초

# -----------------------------------------------------------
# 유틸
# -----------------------------------------------------------
def json_error(message: str, status: int = 500):
    return jsonify({"message": message}), status


# -----------------------------------------------------------
# 헬스체크
# -----------------------------------------------------------
@app.get("/health")
def health():
    # DB 연결 체크
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                _ = cursor.fetchone()
    except Exception as e:
        return json_error(f"DB unhealthy: {e}", 500)

    # AI 서버 간단 체크
    try:
        r = requests.post(
            AI_ENDPOINT,
            json={"message": "ping", "account_info": "healthcheck"},
            timeout=10,
        )
        if r.status_code != 200:
            return json_error(f"AI unhealthy: {r.status_code}", 502)
    except Exception as e:
        return json_error(f"AI unhealthy: {e}", 502)

    return jsonify({"status": "ok"}), 200


# -----------------------------------------------------------
# 회원가입
# -----------------------------------------------------------
@app.post("/register")
def register():
    try:
        data = request.get_json(force=True)
        username  = data.get("username")
        password  = data.get("password")
        email     = data.get("email")
        phone     = data.get("phone_number")
        address   = data.get("address")
        birthdate = data.get("birthdate")

        if not username or not password:
            return json_error("❌ 아이디와 비밀번호는 필수입니다.", 400)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM login WHERE username=%s", (username,))
                if cursor.fetchone():
                    return json_error("❌ 이미 사용 중인 아이디입니다.", 409)

                hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
                cursor.execute(
                    """
                    INSERT INTO login (username, password, email, phone_number, address, birthdate)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (username, hashed_pw, email, phone, address, birthdate),
                )
                conn.commit()

        return jsonify({"message": "✅ 회원가입 성공!"}), 200

    except Exception as e:
        return json_error(f"❗ 서버 오류: {str(e)}", 500)


# -----------------------------------------------------------
# 로그인(API)
# -----------------------------------------------------------
@app.post("/api/login")
def api_login():
    try:
        data = request.get_json(force=True)
        username = data.get("username")
        password = data.get("password")

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM login WHERE username=%s", (username,))
                user = cursor.fetchone()

                if not user or not bcrypt.check_password_hash(user["password"], password):
                    return jsonify({"error": "로그인 실패"}), 401

                cursor.execute(
                    """
                    SELECT account_number, bank_name, product_name, account_type, balance,
                           interest_rate, maturity_date, monthly_limit, auto_transfer, note
                    FROM account WHERE user_id = %s
                    """,
                    (user["id"],),
                )
                accounts = cursor.fetchall()

        return jsonify({"user_id": user["id"], "accounts": accounts}), 200

    except Exception as e:
        return json_error(f"❗ 서버 오류: {str(e)}", 500)


# -----------------------------------------------------------
# 계좌 추가
# -----------------------------------------------------------
@app.post("/api/add_account")
def add_account():
    try:
        data = request.get_json(force=True)
        user_id        = data.get("user_id")
        account_number = data.get("account_number")
        bank_name      = data.get("bank_name")
        balance        = data.get("balance", 0.0)
        account_type   = data.get("account_type")
        interest_rate  = data.get("interest_rate", 0.0)
        maturity_date  = data.get("maturity_date") or None
        product_name   = data.get("product_name")
        is_fixed_term  = data.get("is_fixed_term", False)
        monthly_limit  = data.get("monthly_limit", 0.0)
        auto_transfer  = data.get("auto_transfer", False)
        note           = data.get("note")

        if not user_id or not account_number:
            return json_error("❌ 필수 데이터 누락", 400)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO account (
                        user_id, account_number, bank_name, balance,
                        account_type, interest_rate, maturity_date,
                        product_name, is_fixed_term, monthly_limit,
                        auto_transfer, note
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        account_number,
                        bank_name,
                        balance,
                        account_type,
                        interest_rate,
                        maturity_date,
                        product_name,
                        is_fixed_term,
                        monthly_limit,
                        auto_transfer,
                        note,
                    ),
                )
                conn.commit()

        return jsonify({"message": "✅ 계좌가 등록되었습니다."}), 200

    except Exception as e:
        # UNIQUE 제약 위반 등도 여기로 들어옴
        return json_error(f"❗ 서버 오류: {str(e)}", 500)


# -----------------------------------------------------------
# 계좌 목록
# -----------------------------------------------------------
@app.post("/api/accounts")
def get_accounts():
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        if not user_id:
            return json_error("user_id가 없습니다.", 400)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT account_number, bank_name, product_name, account_type, balance,
                           interest_rate, maturity_date, monthly_limit, auto_transfer, note
                    FROM account WHERE user_id = %s
                    """,
                    (user_id,),
                )
                accounts = cursor.fetchall()

        return jsonify({"accounts": accounts}), 200

    except Exception as e:
        return json_error(f"❗ 서버 오류: {str(e)}", 500)


# -----------------------------------------------------------
# 간단 HTML 페이지 (세션 기반, 사용 안 하면 무시)
# -----------------------------------------------------------
@app.get("/accounts")
def my_accounts():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM account WHERE user_id=%s", (user_id,))
            accounts = cursor.fetchall()

        result = "<h2>📒 내 계좌 목록</h2><ul>"
        for acc in accounts:
            result += f"<li>{acc['bank_name']} / {acc['account_number']} / {acc['balance']}원 / {acc['account_type']}</li>"
        result += "</ul>"
        return result
    finally:
        conn.close()


@app.get("/")
def home():
    if "user_id" in session:
        return redirect(url_for("my_accounts"))
    # 별도 로그인 페이지가 없으므로 단순 안내
    return "API 서버 동작 중입니다.", 200


# -----------------------------------------------------------
# AI 요청
# -----------------------------------------------------------
@app.post("/ask")
def ask():
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        user_message = data.get("message")

        if not user_id or not user_message:
            return jsonify({"response": "❌ 요청이 올바르지 않습니다."}), 400

        # 계좌 조회
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT bank_name, account_number, balance, account_type,
                           maturity_date, interest_rate, note, auto_transfer
                    FROM account WHERE user_id=%s
                    """,
                    (user_id,),
                )
                accounts = cursor.fetchall()

        if not accounts:
            return jsonify({"response": "❗ 계좌 정보가 없습니다."})

        account_info = " | ".join(
            [
                "은행명: {bank_name}, 계좌유형: {account_type}, 잔액: {balance}원, "
                "이자율: {interest_rate}%, 만기일: {maturity_date}, "
                "자동이체: {auto}, 메모: {note}".format(
                    bank_name=acc["bank_name"],
                    account_type=acc["account_type"],
                    balance=acc["balance"],
                    interest_rate=acc["interest_rate"],
                    maturity_date=acc["maturity_date"],
                    auto=("있음" if acc["auto_transfer"] else "없음"),
                    note=(acc["note"] or ""),
                )
                for acc in accounts
            ]
        )

        # AI 서버 호출
        try:
            resp = requests.post(
                AI_ENDPOINT,
                json={"message": user_message, "account_info": account_info},
                timeout=AI_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("response", "").strip()
            if not answer:
                return jsonify({"response": "❗ AI 서버가 빈 응답을 반환했습니다."}), 502
            return jsonify({"response": answer}), 200

        except Timeout:
            return jsonify({"response": "⏱️ AI 서버 응답이 지연되었습니다. 잠시 후 다시 시도해 주세요."}), 504
        except HTTPError as e:
            body = e.response.text[:400] if e.response is not None else ""
            return jsonify({"response": f"❗ AI 서버 오류 ({e.response.status_code}): {body}"}), 502
        except ReqConnectionError as e:
            return jsonify({"response": f"❗ AI 서버에 연결할 수 없습니다: {str(e)}"}), 502
        except RequestException as e:
            return jsonify({"response": f"❗ AI 요청 중 오류가 발생했습니다: {str(e)}"}), 502

    except Exception as e:
        return jsonify({"response": f"❗ 서버 오류: {str(e)}"}), 500


if __name__ == "__main__":
    # 도커에서 외부 접근 가능하도록 0.0.0.0 바인딩
    app.run(debug=True, host="0.0.0.0")
