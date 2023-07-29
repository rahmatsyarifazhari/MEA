from flask import Flask, Blueprint, Response
from flask_socketio import SocketIO
from flask_cors import CORS
import os

HTTP_PORT = os.environ.get('HTTP_PORT', 5000)
HTTP_HOST = os.environ.get('HTTP_HOST', "0.0.0.0")
url_rtsp = os.environ.get('URL_VIDEO', 0)

views = Blueprint('auth_api', __name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = "jek"
app.register_blueprint(views, url_prefix='/')
CORS(app)

socketio = SocketIO(app, async_mode="threading")
socketio.init_app(app, cors_allowed_origins="*")




def generate_stream(rtsp, socketio=socketio):
    import analitik.analitik as analitik
    stream = analitik.WebStreaming(rtsp, socketio)
    return stream

stream = generate_stream(url_rtsp, socketio)

@app.get("/video_feed")
def video_feed():
    return Response(stream.generate_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

# check to see if this is the main thread of execution
if __name__ == '__main__':
    # start the flask app
    socketio.run(app, host=HTTP_HOST, port=HTTP_PORT)