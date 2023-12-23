from flask import Flask, request, render_template, url_for, send_file, jsonify
import requests
import os
import hashlib
import sqlite3
from datetime import datetime
from chat_paper import chat_paper_function
from io import BytesIO
from flask_cors import CORS  # 导入CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 设置跨域

# 数据库初始化
def init_db():
    conn = sqlite3.connect('paper.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS paper 
                    (timestamp TEXT, title TEXT, file_path TEXT, md5_hash TEXT, content TEXT, result TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('paper.db')
    conn.row_factory = sqlite3.Row
    return conn

# 根据MD5哈希值获取文件路径
def get_file_path(md5_hash):
    conn = get_db_connection()
    cursor = conn.execute("SELECT file_path FROM paper WHERE md5_hash=?", (md5_hash,))
    try:
        file_path = cursor.fetchone()[0]
    except TypeError:
        print("File does not exist.")
        file_path = None
    conn.close()
    return file_path

# 将文件解析结果保存到数据库
def save_to_database(timestamp, title, file_path, md5_hash, content, result):
    conn = get_db_connection()
    conn.execute("INSERT INTO paper VALUES (?, ?, ?, ?, ?, ?)", 
                 (timestamp, title, file_path, md5_hash, content, result))
    conn.commit()
    conn.close()

# 根据MD5哈希值获取文件解析结果
def get_analysis_result(md5_hash):
    conn = get_db_connection()
    cursor = conn.execute("SELECT result FROM paper WHERE md5_hash=?", (md5_hash,))
    try:
        result = cursor.fetchone()[0]
    except TypeError:
        result = None
    conn.close()
    return result

def download_pdf(url):
    response = requests.get(url)
    if response.headers['Content-Type'] != 'application/pdf':
        raise ValueError("URL does not contain a PDF file.")
    
    # 使用MD5哈希值作为文件名 如果文件已经存在则直接返回文件路径
    file_md5 = hashlib.md5(response.content).hexdigest()
    file_path = get_file_path(file_md5)
    if file_path:
        return file_path
    
    # 保存文件到本地
    static_dir = 'static'
    pdf_dir = 'pdf'
    date_path = datetime.now().strftime('%Y/%m/%d')
    base_dir = os.path.join(static_dir, pdf_dir, date_path)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    file_name = file_md5 + '.pdf'
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, 'wb') as f:
        f.write(response.content)

    return file_path

@app.route('/upload', methods=['GET'])
def upload():
    pdf_url = request.args.get('pdf_url')
    if not pdf_url:
        return "No PDF URL provided", 400

    try:
        file_path = download_pdf(pdf_url)
    except ValueError as e:
        return str(e), 400

    # file_path 需要变成静态文件的URL
    file_path = file_path.replace('\\', '/')
    pdf_url = url_for('static', filename=file_path.split('static/')[1])
    return render_template('display_results.html', pdf_url=pdf_url)

@app.route('/download', methods=['POST'])
def download_file():
    data = request.get_json()
    url = data['url']

    # 文件名为url最后一部分
    file_name = url.split('/')[-1]
    print(file_name)
    
    # 使用requests下载文件
    response = requests.get(url)
    if response.status_code == 200:
        # 将下载的文件转换为BytesIO对象
        file_object = BytesIO(response.content)
        file_object.seek(0)
        return send_file(file_object, as_attachment=True, download_name=file_name)
    else:
        return "文件下载失败", 400


@app.route('/analysis', methods=['POST'])
def analysis():
    data = request.get_json()
    file_path = data['file_path']
    print(file_path)

    # 提取文件名
    file_name = file_path.split('/')[-1].split('.')[0]
    # 文件名作为MD5哈希值
    md5_hash = file_name
    # 获取文件解析结果
    result = get_analysis_result(md5_hash)
    if result:
        # 返回JSON格式的响应
        return jsonify(result=result)

    # 文件解析
    title, content, result = chat_paper_function(file_path)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # content是dict.values()的结果，需要转换成字符串
    content = '\n'.join(content)
    save_to_database(timestamp, title, file_path, md5_hash, content, result)
    return jsonify(result=result)


@app.route('/', methods=['GET'])
def index():
    return 'hello world'


if __name__ == '__main__':
    app.run(debug=True, port=5000)
