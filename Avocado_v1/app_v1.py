import jwt
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request, redirect, url_for, g, make_response
from bson import ObjectId

app = Flask(__name__)

# mongodb
client = MongoClient('localhost', 27017)
db = client.dbsparta

# jwt secret key
SECRET_KEY = 'avocado'
COOKIE_KEY = 'token_give'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 쿠키에서 token_give 가져오기
        token_receive = request.cookies.get(COOKIE_KEY)
        print('token_receive :', token_receive)

        if token_receive is None:
            # token이 없는 경우
            return redirect(url_for('login'))

        try:
            # 전달받은 token이 위조되었는지 확인 (단방향이기 때문에 비밀번호와 마찬가지로 해쉬처리하여 동일한지 비교)
            # SECRET_KEY를 모르면 동일한 해쉬를 만들 수 없음
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            # 토큰 없거나 만료되었거나 올바르지 않은 경우 로그인 페이지로 이동
            return redirect(url_for('login'))

        # g는 각각의 request 내에서만 값이 유효한 스레드 로컬 변수입니다.
        # 사용자의 요청이 동시에 들어오더라도 각각의 request 내에서만 g 객체가 유효하기 때문에 사용자 ID를 저장해도 문제가 없습니다.
        g.user = db.user.find_one({'id': payload["id"]})

        # 로그인 성공시 다음 함수 실행
        return f(*args, **kwargs)

    return decorated_function


#################################
# HTML 응답 API
#################################

@app.route('/')
def home():
    return render_template('home_v1.html')


@app.route('/login')
def login():
    return render_template('login_v1.html')


@app.route('/register')
def register():
    return render_template('register_v1.html')


@app.route('/home')
@login_required
def home_after_login():
    return render_template('home_after_v1.html', user=g.user)


@app.route('/sell')
@login_required
def sell():
    return render_template('sell_v1.html', user=g.user)


@app.route('/buy')
@login_required
def buy():
    return render_template('buy_v1.html', user=g.user)


#################################
# JSON 응답 API
#################################

# 회원가입
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']

    # id 중복 확인
    user = db.user.find_one({'id': id_receive})
    if user is not None:
        return jsonify({'result': 'fail', 'msg': '아이디가 중복되었습니다 😅'})

    # pw를 sha256 방법(단방향)으로 암호화
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})

    return jsonify({'result': 'success', 'msg': '🎉 회원 가입을 축하합니다 🎉'})


# 로그인
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # pw를 sha256 방법(단방향)으로 암호화
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된 pw을 가지고 해당 유저를 찾기
    user = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    if user is not None:
        # jwt 토큰 발급
        payload = {
            'id': user['id'],  # user id
            'exp': datetime.utcnow() + timedelta(seconds=360)  # 만료 시간 (10초 뒤 만료)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        print(f'token : {token}')
        res = make_response(jsonify({'result': 'success', 'msg': f'{user["nick"]}님 안녕하세요 🙇🏻‍♂️'}))

        # set cookie
        res.set_cookie(COOKIE_KEY, token)

        return res
    else:
        return jsonify({'result': 'fail', 'msg': '아이디와 비밀번호를 확인해주세요 😓'})


# 로그아웃
@app.route('/api/logout', methods=['POST'])
def api_logout():
    res = make_response(jsonify({'result': 'success', 'msg': '로그아웃 👋'}))

    # cookie 삭제
    res.delete_cookie(COOKIE_KEY)
    return res


# Read all cards without id
@app.route('/card', methods=['GET'])
def show_cards():
    result = list(db.contents.find({}, {'_id': False}))
    return jsonify({'result': 'success', 'contents': result})


# show certain page
@app.route('/page', methods=['GET'])
def show_page():
    title_receive = request.form['title_give']
    content = db.contents.find_one({'title': title_receive}, {'_id': False})
    content['comments'] = sorted(content['comments'], key=lambda item: item['price'])
    return jsonify({'result': 'success', 'content': content})


def object_id_decoder(data):
    data['_id'] = str(data['_id'])
    return data


# Create card
@app.route('/post', methods=['POST'])
@login_required
def post_card():
    sign_receive = request.form['sign_give']
    title_receive = request.form['title_give']
    product_receive = request.form['product_give']
    deadline_receive = request.form['deadline_give']
    d = datetime.now()

    content = {
        'user_objectId': object_id_decoder(g.user)['_id'],
        'sign': sign_receive,
        'title': title_receive,
        'product': product_receive,
        'created': str(d.year) + "-" + str(d.month) + "-" + str(d.day),
        'deadline': deadline_receive,
        'comments': []
    }

    db.contents.insert_one(content)
    return jsonify({'result': 'success'})


# Comment
@app.route('/comment', methods=['POST'])
@login_required
def post_comment():
    title_receive = request.form['title_give']
    price_receive = request.form['price_give']
    d = datetime.now()

    new_comments = db.contents.find_one({'title': title_receive}, {'_id': 0})['comments']

    comment = {
        'user_objectId': object_id_decoder(g.user)['_id'],
        'nickname': object_id_decoder(g.user)['nick'],
        'price': int(price_receive),
        'date': str(d.year) + "-" + str(d.month) + "-" + str(d.day)
    }
    new_comments.append(comment)
    db.contents.update_one({'title': title_receive}, {'$set': {'comments': new_comments}})

    return jsonify({'result': 'success'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
