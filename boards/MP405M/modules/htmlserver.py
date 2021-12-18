import os
import struct
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("--htmlserver.py--")

class htmlserver:
    http_codes = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error",
        503: "Service Unavailable"
    }

    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "html": "text/html",
        "htm": "text/html",
        "css": "text/css",
        "js": "application/javascript"
    }

    def __init__(self, index_page, nic):
        dir_list=index_page.split('/')
        self._web_dir=index_page[0:len(dir_list[-1])]

    def _serve_file(self, requested_file, c_socket):
        try:
            if requested_file.split('/')[1]=='flash': # 绝对路径
                file_path=requested_file
            else:                                     #相对路径
                file_path=self._web_dir+requested_file
            # print('file_path=',file_path)
            length = os.stat(file_path)[6]
            c_socket.sendall(self._generate_headers(200, file_path, length))
            # Send file by chunks to prevent large memory consumption
            chunk_size = 1024
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    c_socket.sendall(data)
                    if len(data) < chunk_size:
                        break
            c_socket.close()
        except OSError:
            self._generate_static_page(c_socket, 500, "500 Internal Server Error [2]")

    def _serve_dir(self, requested_file, c_socket):
        requested_file=str(requested_file[:-1])
        c_socket.write(b'HTTP/1.0 200 OK\r\n')
        c_socket.write(b'Content-type: text/html; charset=utf-8\r\n')
        c_socket.write(b'\r\n')
        title = b'Directory listing ' + requested_file +'/'
        c_socket.write(b'<!DOCTYPE html><html><head><title>')
        c_socket.write(title)
        c_socket.write(b"""</title></head><body>""")
        c_socket.write(b'<h1>')
        c_socket.write(title)
        c_socket.write(b'</h1><ul>')
        # Parent directory (if not top)
        if requested_file !='/flash':
            c_socket.write(b'<li><a href="../">../</a> (parent dir)</li>')
        # List files in the dir from requested_file.
        fnames = sorted(os.listdir(requested_file))
        # Show directories first.
        odd = False
        for show_dir in (True, False):
            for fn in fnames:
                # Stat it, to check if it's a file or another directory.
                if fn=='System Volume Information':
                    continue
                s = os.stat(requested_file+'/'+str(fn))
                is_dir = bool(s[0] & 0x4000)
                if is_dir == show_dir:
                    fn_escaped = str(fn)
                    if odd:
                        cssclass = 'odd'
                    else:
                        cssclass = ''
                    if show_dir:
                        fn_escaped += '/'
                        cssclass += ' d'
                    else:
                        cssclass += ' f'
                    c_socket.write(b'<li class="%s"><a href="' % (cssclass,))
                    c_socket.write(fn_escaped)
                    c_socket.write(b'">')
                    c_socket.write(fn_escaped)
                    c_socket.write(b'</a>')
                    # file size:
                    if not is_dir:
                        if s[6]<1024:
                            c_socket.write(b'<span class="filemeta"> %d b</span>'% (s[6],) )
                        elif s[6]<1024*1024:
                            c_socket.write(b'<span class="filemeta"> %.2f kb</span>'% (s[6]/1024,) )
                        elif s[6]<1024*1024*1024:
                            c_socket.write(b'<span class="filemeta"> %.2f Mb</span>'% (s[6]/1024/1024,) )

                    c_socket.write(b'</li>\n')
                    odd = (not odd)
            if show_dir:
                # Space between dirs and files
                c_socket.write(b'</ul><ul>')
        c_socket.close()

    def _generate_headers(self,code, filename=None, length=None):
        content_type = "text/html"

        if filename:
            ext = filename.split(".")[-1]

            if ext in htmlserver.mime_types:
                content_type = htmlserver.mime_types[ext]

        # Close connection after completing the request
        return "HTTP/1.1 {} {}\n" \
               "Content-Type: {}\n" \
               "Content-Length: {}\n" \
               "Server: WSME-Server\n" \
               "Connection: close\n\n".format(
                code, htmlserver.http_codes[code], content_type, length)

    def _generate_static_page(self,sock, code, message):
        sock.sendall(self._generate_headers(code))
        sock.sendall("<html><head><link rel='icon' href='data:image/ico;base64,aWNv'></head><body><h1>" + message + "</h1></body></html>")
        sock.close()

    def send_err(self,sock, code, reason = b'Internal error'):
        sock.write(b'HTTP/1.0 ')
        sock.write(str(code).encode('ascii'))
        sock.write(b' ')
        sock.write(reason)
        sock.write(b'\r\nContent-type: text/plain; charset=utf-8\r\n\r\n')
        sock.write(reason)
        sock.close()

    def maybe_delete(self,fn):
        try:
            os.remove(fn)
        except OSError as e:
            pass

    def _save_put_request(self,sock,content_length):
        temp_filename='put.tmp'
        outf = open(temp_filename, 'wb')
        self.maybe_delete(temp_filename)
        bytesleft = content_length
        try:
            outf = open(temp_filename, 'wb')
        except OSError as e:
            logger.error(e)
            return self.send_err(sock, 500,'{"success":0}')
        
        filename=''
        content_type=''
        WebKitFormBoundary=''
        while bytesleft > 0:
            chunk = sock.readline(min(bytesleft, 4096))
            bytesleft=bytesleft-len(chunk)
            if bytesleft == 44: # 判读是否为最后一行的前一行，如果是则删除前一行结尾的\r\n
                logger.debug('end='+str(sock.readline(44)))
                bytesleft=0
                chunk=chunk[:-2]

            # logger.debug('chunk='+str(chunk))
            if '------WebKitFormBoundary' in chunk:
                WebKitFormBoundary=chunk
                logger.debug('WebKitFormBoundary='+str(WebKitFormBoundary))
                continue
            elif 'filename=' in chunk:
                chunk=str(chunk)
                filename=chunk[chunk.find('filename=')+10:-6]
                logger.debug('filename='+str(filename))
                continue
            elif 'Content-Type:' in chunk:
                chunk=str(chunk)
                content_type=chunk[chunk.find('Content-Type:')+14:-5]
                logger.debug('content_type='+str(content_type))
                logger.debug('start='+str(sock.readline(4)))
                bytesleft=bytesleft-2 # 删除开始之前的一个\r\n
                continue

            try:
                # logger.debug("writing chunk of len %d (remaining %d)" % (len(chunk), bytesleft))
                outf.write(chunk)
            except OSError:
                outf.close()
                return self.send_err(sock, 500,'{"success":0}')

        outf.flush()
        outf.close()

        if filename !='' and content_type !='' and WebKitFormBoundary !='':
            self.maybe_delete(filename)
            os.rename(temp_filename, filename)
            self.send_err(sock, 201, '{"success":1}') 
            logger.debug('save OK')
        else:
            return self.send_err(sock, 500,'{"success":0}')
            logger.debug('error no filename')