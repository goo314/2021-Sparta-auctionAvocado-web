from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient  # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)

app = Flask(__name__)

client = MongoClient('localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbsparta  # 'dbsparta'라는 이름의 db를 만들거나 사용합니다.


@app.route('/')
def home():
    return render_template('test_card.html')


@app.route('/api/list', methods=['GET'])
def read_contents():
    result = list(db.contents.find({}, {'_id': 0}))
    return jsonify({'result': 'success', 'contents': result})


@app.route('/api/post', methods=['POST'])
def post_contents():
    # sign 정렬기준, title 제목, comment
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


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
