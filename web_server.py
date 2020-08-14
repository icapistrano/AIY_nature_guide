#!/usr/bin/env python3

import os
import io
import cgi
import picamera
import logging
import socketserver
from http import server
from threading import Condition
from aiy.board import Board
from aiy.leds import Leds, Color, Pattern
from get_model import launch_inaturalist, search_inaturalist


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):    
    def do_GET(self):
        global leds, colour, object_info, object_url
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
            
        elif self.path == '/index.html':            
            with open("index.html", "rb") as content_file:
                content= content_file.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
       
            leds.update(Leds.rgb_on(colour))
            
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        
        elif self.path == '/stylesheet.css':
            self.send_response(200)
            self.send_header('Content-Type', 'text/css')
            self.end_headers()
            
            with open("stylesheet.css", "rb") as stylesheet:
                self.wfile.write(stylesheet.read())
                
        elif self.path == '/info':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            with open("info.html", "rb") as content_file:
                content = content_file.read()
                self.wfile.write(content)
            
            try:
                leds.update(Leds.rgb_pattern(colour))
                
                obj_output = '<div class="grid-container">'
                obj_output += '<div class="single-cols">'
                obj_output += '<h1>AIY - Quick Nature Guide</h1>'
                obj_output += '</div>'
                obj_output += '<div class="single-cols">'
                obj_output += '<img src="foo.jpg" width="640" height="480" />'
                obj_output += '</div>'
                obj_output += '<div class="single-cols">'

                obj_names = launch_inaturalist(object_name)
                object_info, object_url = search_inaturalist(obj_names)
                leds.update(Leds.rgb_on(colour))
                
                obj_output += '<h2>{}</h2>'.format(obj_names[1])
                obj_output += '</div>'
                obj_output += '<div class="single-cols">'
                obj_output += '<p id="moreBtn" class="0">{}<br><br>'.format(object_info)
                obj_output += '<span id="moreInfo"><a href={} target="_blank">Click here</a> for more info</span>'.format(object_url)
                obj_output += '</p>'
    
            except:
                obj_output += '<h2>Unknown object</h2>'
                obj_output += '</div>'
                obj_output += '<div class="single-cols">'
                obj_output += '<p>Sorry, I could not retrieve any information. Please try again.</p>'
                
                colour = (255, 255, 255)
                leds.update(Leds.rgb_on(colour))
                
            finally:
                obj_output += '<div class="single-cols"><form method="POST" action="/selfPost">'
                obj_output += '<input type="submit" value="Go HomePage">'
                obj_output += '</form></div>'
                obj_output += '</div>'
                self.wfile.write(obj_output.encode())
                
                colour = (255,255,255)
            
        elif self.path == '/foo.jpg':
            statinfo = os.stat('foo.jpg')
            img_size = statinfo.st_size
            
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpg')
            self.send_header('Content-Length', img_size)
            self.end_headers()
            
            with open('foo.jpg', "rb") as image_file:
                self.wfile.write(image_file.read())
                    
        else:
            self.send_error(404)
            self.end_headers()
            
    def do_POST(self):
        global colour, object_name
        if self.path == ('/selfPost'):
            try:
                ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
                pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
                content_len = int(self.headers.get('Content-length'))
                pdict['CONTENT-LENGTH'] = content_len
                
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    
                    for model, model_type in fields.items():
                        model_type = model_type[0].decode()
                        
                        if model_type == 'plants':
                            colour = (20, 255, 20)
                        elif model_type == 'insects':
                            colour = (255, 255, 20)
                        elif model_type == 'birds':
                            colour = (0, 153, 255)
                        else:
                            colour = (255, 255, 255)
            except:
                pass
            
            finally:
                self.send_response(301)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Location', '/index.html')
                self.end_headers()
        
        elif self.path.endswith('/new'):
            camera.capture('foo.jpg', use_video_port=True)
            
            ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
            pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                
                for model, model_type in fields.items():
                    model_type = model_type[0].decode()
                    object_name = model_type
            
            self.send_response(301)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Location', '/info')
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# I know, query strings instead of global vars might be better    
object_name, object_info, object_url = None, None, None
colour = (255, 255, 255) # white as default
leds = Leds()

leds.pattern = Pattern.breathe(1000)


with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        print("Your webpage is being served at http://your-pi-address:8000/")
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
        
    finally:
        camera.stop_recording()
        leds.update(Leds.rgb_off())
        image = [img for img in os.listdir(os.getcwd()) if img.endswith('jpg')] # deletes image captured by RPI cam
        os.remove(image[0])
        
        
