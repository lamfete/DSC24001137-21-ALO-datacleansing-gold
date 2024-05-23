import re
import pandas as pd
import os
#import codecs
import sqlite3

from flask import Flask, jsonify, request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
from werkzeug.utils import secure_filename
from io import StringIO

app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#UPLOAD_FOLDER = os.path.join(APP_ROOT, 'staticFiles/uploads')
UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class CustomFlaskAppWithEncoder(Flask):
    json_provider_class = LazyJSONEncoder

app = CustomFlaskAppWithEncoder(__name__)

conn = sqlite3.connect('data/binar_dsc_gold_challenge.db', check_same_thread=False)

swagger_template = dict(
    info={
        'title': LazyString(lambda: 'Binar Data Science Wave 21 Gold Level Challenge'),
        'version': LazyString(lambda: '1.0.0'),
        'description': LazyString(lambda: 'Dokumentasi API untuk Binar Data Science Wave 21 Gold Level Challenge'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)

@swag_from("docs/view_all_text.yml", methods=['GET'])
@app.route('/view_all_text', methods=['GET'])
def view_all_text():
    cursor = conn.execute("SELECT teks_sebelum, teks_setelah FROM pengolahan_teks")
    all_text = []

    for row in cursor:
        all_text.append(row)

    conn.close()

    json_response = {
        'status_code': 200,
        'description': "Menampilkan semua teks",
        'data': all_text,
    }

    response_data = jsonify(json_response)
    return response_data


@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():
    text = request.form.get('text')
    text_processed = re.sub(r'[^a-zA-Z0-9]', ' ', text)

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': text_processed,
    }

    conn.execute("INSERT INTO pengolahan_teks(teks_sebelum, teks_setelah) VALUES (?, ?)", (text, text_processed))
    conn.commit()
    conn.close()

    response_data = jsonify(json_response)
    return response_data

@swag_from("docs/file_processing.yml", methods=['POST'])
@app.route('/file-processing', methods=['POST'])
def file_processing():
    
    f = request.files.get('file_yg_diupload')
    data_filename = secure_filename(f.filename)
    f.save(os.path.join(UPLOAD_FOLDER, data_filename))
    path = os.path.join(UPLOAD_FOLDER)

    data_file_path = os.path.join(path, data_filename)
    try:
        with open(data_file_path, 'r', encoding='utf-8') as fopen:
            q = fopen.read()
        
        # Import file csv ke Pandas
        df = pd.read_csv(StringIO(q), header=None)
        
        # Ambil teks yang akan diproses dalam format list
        texts = df[0].to_list()
        
        # Lakukan cleansing pada teks
        cleaned_text = []
        for text in texts:
            cleaned_text.append(re.sub(r'[^a-zA-Z0-9]', ' ', text))

        json_response = {
            'status_code': 200,
            'description': "Teks yang sudah diproses",
            'data': cleaned_text,
        }

        conn.execute("INSERT INTO pengolahan_teks(teks_sebelum, teks_setelah) VALUES (?, ?)", (str(texts), str(cleaned_text)))
        conn.commit()
        conn.close()

        response_data = jsonify(json_response)
        return response_data
    except Exception as e:
        json_response = {
            'status_code': 415,
            #'description': "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe2.",
            'description': "Unsupported Media Type: File type yang diupload bukan utf-8. Mohon untuk diubah di notepad, pilih save as, ganti dari ANSI menjadi utf-8.",
            'data': []
        }
        response_data = jsonify(json_response)

        return response_data

if __name__ == '__main__':
    app.run(debug=True)
