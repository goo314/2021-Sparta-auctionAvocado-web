from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient  # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)

app = Flask(__name__)

client = MongoClient('localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbsparta  # 'dbsparta'라는 이름의 db를 만들거나 사용합니다.


@app.route('/')
def home():
    return render_template('test_index.html')


@app.route('/list', methods=['GET'])
def read_contents():
    result = list(db.contents.find({}, {'_id': 0}))
    return jsonify({'result': 'success', 'contents': result})


# Make card
@app.route('/post', methods=['POST'])
def post_contents():
    sign_receive = request.form['sign_give']
    title_receive = request.form['title_give']
    product_receive = request.form['product_give']

    content = {
        'sign': sign_receive,
        'title': title_receive,
        'product': product_receive
    }

    db.contents.insert_one(content)

    return jsonify({'result': 'success'})


# Write comment
@app.route('/comment', methods=['POST'])
def post_comment():
    nickname_receive = request.form['nickname_give']
    price_receive = request.form['price_give']
    comment = {
        'nickname': nickname_receive,
        'price': price_receive
    }

    db.conmments.insert_one(comment)

    return jsonify({'result': 'success'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
