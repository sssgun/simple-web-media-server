import os
import mimetypes
from flask import Flask, send_file, render_template
import sys

app = Flask(__name__)

def get_media_files_by_directory(directory):
    video_files = []
    image_files = []
    for filename in sorted(os.listdir(directory)):
        # 파일 확장자를 기준으로 MIME 타입 추출
        media_path = os.path.join(directory, filename)
        mime_type, _ = mimetypes.guess_type(media_path)
        if mime_type:
            if mime_type.startswith('video/'):
                video_files.append(filename)
            elif mime_type.startswith('image/'):
                image_files.append(filename)
    return video_files + image_files

@app.route('/')
def index():
    return 'Hello, this is a media server!'

@app.route('/media')
def media():
    # 미디어 디렉토리에서 디렉토리 목록을 가져옴
    directories = get_media_directories(MEDIA_DIRECTORY)
    return render_template('media_list.html', directories=directories)

@app.route('/media/<directory>')
def media_directory(directory):
    # 특정 디렉토리에서 파일 목록을 가져옴
    files = get_media_files_by_directory(os.path.join(MEDIA_DIRECTORY, directory))
    return render_template('media_list_directory.html', directory=directory, files=files)

def get_media_directories(directory):
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

@app.route('/media/<path:file_path>')
def get_media_file(file_path):
    # 미디어 파일의 전체 경로 생성
    media_path = os.path.join(MEDIA_DIRECTORY, file_path)

    # 파일 확장자를 기준으로 MIME 타입 추출
    mime_type, _ = mimetypes.guess_type(media_path)
    if mime_type is None:
        return 'Unsupported file type'

    # 미디어 파일을 스트리밍 형식으로 전송
    return send_file(media_path, mimetype=mime_type, as_attachment=False)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python file_server.py MEDIA_DIRECTORY PORT")
        sys.exit(1)

    MEDIA_DIRECTORY = sys.argv[1]
    try:
        PORT = int(sys.argv[2])
    except ValueError:
        print("Error: Invalid port number.")
        sys.exit(1)

    app.run(host='0.0.0.0', port=PORT)
