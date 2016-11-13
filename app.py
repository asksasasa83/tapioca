# tmux attach
# pip install flask
# export FLASK_APP=app.py
# flask run --host=0.0.0.0

from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import shutil, subprocess, logging
from itertools import product
from werkzeug.utils import secure_filename
import os, urllib
import requests
import commands

STYPATH = "/home/ubuntu/fast-neural-style/models/instance_norm"

FNSPATH = "/home/ubuntu/fast-neural-style"

IMGPATH = "/home/ubuntu/fast-neural-style/out.png"
STATICPATH = "static/out.png"

TESTPATH = "/home/ubuntu/fast-neural-style/test.out.png"
TESTSTATICPATH = "static/test.out.png"

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = '/home/ubuntu/flask-tmp/uploads'

APPLY_FILTERS_PATH =  '/home/ubuntu/run_all_filters.py'
EMILY_FOLDER = '/home/ubuntu/flask-tmp/templates/emily'

### App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EMILY_FOLDER'] = EMILY_FOLDER 
print ("UPSTYLE")
### Logging
logger = logging.getLogger('werkzeug')
handler = logging.FileHandler('access.log')
logger.addHandler(handler)

# Also add the handler to Flask's logger for cases
#  where Werkzeug isn't used as the underlying WSGI server.
app.logger.addHandler(handler)

### Cache control
@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    return response

### App routes
@app.route("/")
def index():
  with open("templates/index.html") as f:
    content = f.read()
  return content

@app.route("/combine/")
def combine():
  return redirect(url_for('index'))
  src = request.args.get('img', 'chicago.jpg')
  sty = request.args.get('sty', 'mosaic.t7')
  shellargs = ["th", "fast_neural_style.lua",
    "-model", os.path.join(STYPATH,sty),
    "-input_image", os.path.join(app.config['UPLOAD_FOLDER'], src),
    "-output_image", "out.png",
    "-gpu", "0"]
  ret = subprocess.call(shellargs, cwd = FNSPATH)
  shutil.copy(IMGPATH, STATICPATH)
  return redirect(url_for('index'))

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename, as_attachment=False)

@app.route('/emily/<path:path>')
def serve_emily(path):
    return send_from_directory(app.config['EMILY_FOLDER'],
                               path, as_attachment=False)

@app.route("/test/")
def test():
  shutil.copy(TESTPATH, TESTSTATICPATH)
  return "<img src='/static/test.out.png'/>"

@app.route("/ui/")
def emily():
  with open("templates/emily/index.html") as f:
    content = f.read()
  return content

 
@app.route("/fbtest/")
def fbtest():
  with open("templates/fbtest.html") as f:
    content = f.read()
  return content

### Uploads
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
      # check if the post request has the file part
      if 'file' not in request.files:
          flash('No file part')
          return redirect(request.url)
      file = request.files['file']
      # if user does not select file, browser also
      # submit a empty part without filename
      if file.filename == '':
          flash('No selected file')
          return redirect(request.url)
      if file and allowed_file(file.filename):
          filename = secure_filename(file.filename)
          file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
          return redirect(url_for('index'))
  return '''
  <!doctype html>
  <title>Upload new File</title>
  <h1>Upload new File</h1>
  <form action="/upload" method=post enctype=multipart/form-data>
    <p><input type=file name=file>
       <input type=submit value=Upload>
  </form>
  '''

@app.route('/urlload')
def load_url():
  url = request.args.get('url', None)
  uid = request.args.get('userid', None)
  if url is None or uid is None:
    return "Pass a url and uid parameter"
  resp = requests.get(url)
  img = resp.content
  filename = "raw.png"
  freldir = os.path.join(uid, filename)
  try:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], uid))
  except OSError:
    return "Already exists"

  with open(os.path.join(app.config['UPLOAD_FOLDER'], freldir), 'wb') as f:
    f.write(img)
    command = '{} {}'.format(APPLY_FILTERS_PATH, uid)
    commands.getstatusoutput(command)
  
  return "Success" 
  
  
if __name__ == "__main__":
  app.run()
