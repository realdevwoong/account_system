from flask import Flask, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection
import os
import requests  
from flask_bcrypt import Bcrypt
app = Flask(__name__)
app.secret_key = os.urandom(24)

bcrypt = Bcrypt(app)

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True)
        username    = data.get("username")
        password    = data.get("password")
        email       = data.get("email")
        phone       = data.get("phone_number")
        address     = data.get("address")
        birthdate   = data.get("birthdate")

        if not username or not password:
            return jsonify({"message": "❌ 아이디와 비밀번호는 필수입니다."}), 400

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM login WHERE username=%s", (username,))
                if cursor.fetchone():
                    return jsonify({"message": "❌ 이미 사용 중인 아이디입니다."}), 409

                hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
                cursor.execute("""
                    INSERT INTO login (username, password, email, phone_number, address, birthdate)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    username, hashed_pw, email, phone, address, birthdate
                ))
                conn.commit()

        return jsonify({"message": "✅ 회원가입 성공!"}), 200

    except Exception as e:
        return jsonify({"message": f"❗ 서버 오류: {str(e)}"}), 500

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM login WHERE username=%s", (username,))
            user = cursor.fetchone()

            # ✅ 들여쓰기 수정됨
            if not user or not bcrypt.check_password_hash(user["password"], password):
                return jsonify({"error": "로그인 실패"}), 401

            # ✅ 통과한 사용자에 대해 계좌 조회
            cursor.execute("""
                SELECT account_number, bank_name, product_name, account_type, balance,
                       interest_rate, maturity_date, monthly_limit, auto_transfer, note
                FROM account WHERE user_id = %s
            """, (user["id"],))
            accounts = cursor.fetchall()

            return jsonify({
                "user_id": user["id"],
                "accounts": accounts
            }), 200
@app.route("/api/add_account", methods=["POST"])
def add_account():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        account_number = data.get("account_number")
        bank_name = data.get("bank_name")
        balance = data.get("balance", 0.0)
        account_type = data.get("account_type")
        interest_rate = data.get("interest_rate", 0.0)
        maturity_date = data.get("maturity_date", None)
        product_name = data.get("product_name")
        is_fixed_term = data.get("is_fixed_term", False)
        monthly_limit = data.get("monthly_limit", 0.0)
        auto_transfer = data.get("auto_transfer", False)
        note = data.get("note")

        # 필수값 확인
        if not user_id or not account_number:
            return jsonify({"message": "❌ 필수 데이터 누락"}), 400
        
        # 날짜 유효성 처리
        if maturity_date in [None, ""]:
            maturity_date = None

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO account (
                        user_id, account_number, bank_name, balance,
                        account_type, interest_rate, maturity_date,
                        product_name, is_fixed_term, monthly_limit,
                        auto_transfer, note
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, account_number, bank_name, balance,
                    account_type, interest_rate, maturity_date,
                    product_name, is_fixed_term, monthly_limit,
                    auto_transfer, note
                ))
                conn.commit()

        return jsonify({"message": "✅ 계좌가 등록되었습니다."}), 200

    except Exception as e:
        return jsonify({"message": f"❗ 서버 오류: {str(e)}"}), 500

@app.route("/api/accounts", methods=["POST"])
def get_accounts():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"message": "user_id가 없습니다."}), 400

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT account_number, bank_name, product_name, account_type, balance,
                       interest_rate, maturity_date, monthly_limit, auto_transfer, note
                FROM account WHERE user_id = %s
            """, (user_id,))
            accounts = cursor.fetchall()

    return jsonify({"accounts": accounts}), 200


@app.route('/accounts')
def my_accounts():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
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

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('my_accounts'))
    return redirect(url_for('login'))

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_id = data.get("user_id")
    user_message = data.get("message")
    if not user_id or not user_message:
        return jsonify({"response": "❌ 요청이 올바르지 않습니다."}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT bank_name, account_number, balance, account_type, maturity_date, interest_rate, note, auto_transfer
                FROM account WHERE user_id=%s
            """, (user_id,))
            accounts = cursor.fetchall()
    finally:
        conn.close()

    if not accounts:
        return jsonify({"response": "❗ 계좌 정보가 없습니다."})

    account_info = " | ".join([
        f"은행명: {acc['bank_name']}, 계좌유형: {acc['account_type']}, 잔액: {acc['balance']}원, 이자율: {acc['interest_rate']}%, 만기일: {acc['maturity_date']}, 자동이체: {'있음' if acc['auto_transfer'] else '없음'}, 메모: {acc['note']}"
        for acc in accounts
    ])

    response = requests.post("http://127.0.0.1:8000/ai", json={
        "message": user_message,
        "account_info": account_info
    })

    if response.status_code == 200:
        return jsonify({"response": response.json()["response"]})
    else:
        return jsonify({"response": "❗ AI 서버 응답 오류"})

if __name__ == '__main__':
    app.run(debug=True)
