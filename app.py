import requests
from flask import Flask, Response, stream_with_context, request

""" 
url
https://mdstrm.com/audio/60a2745ff943100826374a70/icecast.audio -> aac
https://liveradio.mediainbox.net/listen/popular.mp3 -> mp3

http://127.0.0.1:8080/tstream.mp3?stream_url=https://mdstrm.com/audio/60a2745ff943100826374a70/icecast.audio

"""

app = Flask(__name__)

# Re-transmit a stream
def get_stream_chunk(url):
    stream = requests.get(url, stream=True)
    for chuck in stream.iter_content(chunk_size=20000): # 20kb chunks
        yield chuck

@app.route('/stream.mp3')
def stream():
    url = request.args.get('stream_url')
    # header to mp3 content
    header = {'Content-Type': 'audio/mpeg', 'Server': 'Flask'}
    print("Sending stream...")
    if url:
        return Response(stream_with_context(get_stream_chunk(url)), mimetype="audio/mpeg", headers=header)
    else:
        return "url not found! please use ?stream_url=<url>"

# zaraRadio doesn't support 'aac' format so we need to convert the stream to mp3 in real time
def init_transcode(url):
    process = (
        ffmpeg
        .input(url)
        .output('pipe:', format='mp3')
        .run_async(pipe_stdout=True)
    )
    return process

codec_sessions = {}
@app.route('/tstream.mp3')
def tstream():
    url = request.args.get('stream_url')
    init = True
    def get_chunk(url):
        while True:
            buffer = codec_sessions[url].stdout.read(1000) # read 1kb at a time (aprox 5s)
            yield buffer

    if url:
        codec_sessions[url] =  init_transcode(url)
        return Response(stream_with_context(get_chunk(url)), mimetype="audio/mp3")
    else:
        return "url not found! please use ?stream_url=<url>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

