from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)

@app.route('/')
def my_route():
    return render_template('submit.html')

#파일 업로드 & 평가 처리
@app.route('/submit', methods=['POST'])
def submit_file():
    # save_dirpath = ''
    if request.method == "POST":
        f = request.files['filename']
        
        f.save(secure_filename(f.filename))

        return "succes"

if __name__== '__main__':
    app.run(host='localhost', port=80, debug=True)