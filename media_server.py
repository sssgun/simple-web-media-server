import os
import mimetypes
import asyncio
from flask import Flask, send_file, render_template, request, jsonify
from flask_paginate import Pagination
import sys
from math import ceil

from skimage import io
from skimage.color import rgb2gray
from skimage.metrics import structural_similarity as ssim

from PIL import Image, ImageOps
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import datetime

###############################################################################
# logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.INFO)

# Generate log file name with "output_YYMMDD.log" format
current_date = datetime.datetime.now().strftime("%Y%m%d")
log_file = os.path.join(os.getcwd(), f"output_{current_date}.log")

# Set maximum file size to 100MB
max_file_size_bytes = 100 * 1024 * 1024
backup_count = 10  # Number of backup files to keep

file_handler = RotatingFileHandler(log_file, maxBytes=max_file_size_bytes, backupCount=backup_count)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s:%(lineno)d %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

###############################################################################
# utils

def compare_ssim(image1, image2):
    try:
        # Calculate SSIM
        similarity = ssim(image1, image2, win_size=11, data_range=image2.max() - image2.min())
        return similarity
    except Exception as e:
        logger.info(f"Error occurred during SSIM comparison: {e}")
        return 0.0  # Return 0 on error

###############################################################################
# web server

def add_border_to_media(media_path, border_color):
    # Load the media item (image or video)
    # Apply border to the media item
    # Return the processed media item
    
    # For example, if the media is an image:
    img = Image.open(media_path)
    bordered_img = ImageOps.expand(img, border=5, fill=tuple(border_color))
    return bordered_img

# Create a custom filter function
def custom_endswith(value, substrings):
    return any(value.lower().endswith(sub) for sub in substrings)

app = Flask(__name__)

# Add the custom filter to the Jinja2 environment
app.jinja_env.filters['endswith'] = custom_endswith

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

def paginate_files(files, page, per_page):
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    return files[start_idx:end_idx]

@app.route('/')
def index():
    return 'Hello, this is a media server!'

@app.route('/media')
def media():
    # 미디어 디렉토리에서 디렉토리 목록을 가져옴
    directories = get_media_directories(MEDIA_DIRECTORY)
    return render_template('media_list.html', directories=directories)

processed_images = {}
valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
previous_image_path = None
previous_index = 0

@app.route('/media/<directory>')
def media_directory(directory):
    global previous_image_path, previous_index, processed_images

    files = get_media_files_by_directory(os.path.join(MEDIA_DIRECTORY, directory))
    
    # Pagination settings
    per_page = int(request.args.get('per_page', 50))  # Get the per_page parameter, default is 50
    total_files = len(files)
    total_pages = ceil(total_files / per_page)
    page = request.args.get('page', type=int, default=1)
    
    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Paginate the files
    files_to_display = paginate_files(files, page, per_page)

    media_items_with_borders = []

    for file in files_to_display:
        media_path = os.path.join(MEDIA_DIRECTORY, directory, file)

        if any(file.lower().endswith(ext) for ext in valid_image_extensions):
            logger.info(f"image_path={media_path}")
            if media_path not in processed_images:
                processed_images[media_path] = rgb2gray(io.imread(media_path))

            if previous_image_path is not None:
                previous_image = processed_images.get(previous_image_path, None)
                current_image = processed_images.get(media_path, None)

                if previous_image is not None and current_image is not None:
                    similarity = compare_ssim(previous_image, current_image)
                    logger.info(f"similarity={similarity}")

                    # Choose border color based on similarity
                    border_color = "#FF0000" if similarity <= 0.6 else "#0000FF"

                # Append file information and border color to the list
                media_items_with_borders.append({'name': file, 'border_color': border_color, 'similarity': f"Similarity: {similarity:.2f}"})
            else:
                media_items_with_borders.append({'name': file})

            previous_image_path = media_path
        else:
            media_items_with_borders.append({'name': file})
            previous_image_path = None

    return render_template('media_list_directory.html', directory=directory, \
                           files=media_items_with_borders, page=page, total_pages=total_pages, \
                           per_page=per_page)

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

@app.route('/media_list/<directory>')
def media_list(directory):
    # Get a list of files in the specified directory
    files = get_media_files_by_directory(os.path.join(MEDIA_DIRECTORY, directory))
    return render_template('media_list_directory_simple.html', directory=directory, files=files)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        logger.info("Usage: python file_server.py MEDIA_DIRECTORY PORT")
        sys.exit(1)

    MEDIA_DIRECTORY = sys.argv[1]
    try:
        PORT = int(sys.argv[2])
    except ValueError:
        logger.info("Error: Invalid port number.")
        sys.exit(1)

    app.run(host='0.0.0.0', port=PORT)
