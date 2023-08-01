# simple-web-media-server
Media Server is a lightweight web application that serves as a media server for video and image files. The application is built using Flask, a Python web framework, and allows users to access and browse media files organized in directories.

## Introduction

Media Server is a simple Flask web application that allows users to browse and access media files stored in a specific directory. It organizes media files into directories and provides a user-friendly interface to navigate through the directories and view media files like videos and images.

## Installation

1. Clone this repository to your local machine.

```
git clone https://github.com/sssgun/simple-web-media-server.git
```

2. Navigate to the project directory.

```
cd simple-web-media-server
```

3. Create a virtual environment using Miniforge (or any other Python environment manager).

```
conda create -n py39mediaserver python=3.9
conda activate py39mediaserver
```

4. Install the required dependencies using pip.

```
pip install -r requirements.txt
```

5. Run the Flask development server.

```
#                      {MEDIA_PATH}   {PATH}
python media_server.py ${HOME}/Videos 8000
```
