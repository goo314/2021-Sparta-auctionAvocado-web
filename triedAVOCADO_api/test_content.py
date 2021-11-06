import jwt
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request, redirect, url_for, g, make_response
from bson import ObjectId

app = Flask(__name__)

client = MongoClient('localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbsparta  # 'dbsparta'라는 이름의 db를 만들거나 사용합니다.


@app.route('/')
def home():
    return render_template('test_index.html')


# Read all page with id
@app.route('/content', methods=['GET'])
def read_contents():
    result = list(db.contents.find({}, {'_id': 0}))
    return jsonify({'result': 'success', 'contents': result})


# Create content
@app.route('/content/post', methods=['POST'])
def post_contents():
    sign_receive = request.form['sign_give']
    title_receive = request.form['title_give']
    product_receive = request.form['product_give']
    deadline_receive = request.form['deadline_give']
    d = datetime.now()

    content = {
        'user_objectId': 'uid',
        'sign': sign_receive,
        'title': title_receive,
        'product': product_receive,
        'created': str(d.year) + "-" + str(d.month) + "-" + str(d.day),
        'deadline': deadline_receive,
        'comments': []
    }

    db.contents.insert_one(content)
    return jsonify({'result': 'success'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
