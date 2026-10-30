import usocket


class Response:
    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None
        self.status_code = 0
        self.reason = ""
        self.headers = {}

    def close(self):
        if self.raw is not None:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            if self.raw is not None:
                self._cached = self.raw.read()
                self.raw.close()
                self.raw = None
            else:
                self._cached = b""
        return self._cached

    @property
    def text(self):
        return self.content.decode(self.encoding)

    def json(self):
        import ujson

        return ujson.loads(self.content)


def request(
    method,
    url,
    data=None,
    json=None,
    headers=None,
    stream=None,
    auth=None,
    timeout=None,
    parse_headers=True,
):
    headers = dict(headers) if headers else {}
    redirect = None
    chunked_data = data and getattr(data, "__iter__", None) and not getattr(data, "__len__", None)

    if auth is not None:
        import ubinascii

        username, password = auth
        formated = "{}:{}".format(username, password).encode("ascii")
        formated = str(ubinascii.b2a_base64(formated)[:-1], "ascii")
        headers["Authorization"] = "Basic {}".format(formated)

    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto == "http:":
        port = 80
    elif proto == "https:":
        import ussl

        port = 443
    else:
        raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
    ai = ai[0]

    resp_d = None
    if parse_headers is not False:
        resp_d = {}

    s = usocket.socket(ai[0], usocket.SOCK_STREAM, ai[2])

    if timeout is not None:
        s.settimeout(timeout)

    status = 0
    reason = ""

    try:
        s.connect(ai[-1])
        if proto == "https:":
            s = ussl.wrap_socket(s, server_hostname=host)
        s.write(b"%s /%s HTTP/1.0\r\n" % (method.encode("ascii"), path.encode("ascii")))
        if "Host" not in headers:
            s.write(b"Host: %s\r\n" % host.encode("ascii"))
        for k in headers:
            s.write(k.encode("ascii") if isinstance(k, str) else k)
            s.write(b": ")
            s.write(headers[k].encode("ascii") if isinstance(headers[k], str) else headers[k])
            s.write(b"\r\n")
        if json is not None:
            assert data is None
            import ujson

            data = ujson.dumps(json)
            if isinstance(data, str):
                data = data.encode("utf-8")
            s.write(b"Content-Type: application/json\r\n")
        if data:
            if isinstance(data, str):
                data = data.encode("utf-8")
            if chunked_data:
                s.write(b"Transfer-Encoding: chunked\r\n")
            else:
                s.write(b"Content-Length: %d\r\n" % len(data))
        s.write(b"Connection: close\r\n\r\n")
        if data:
            if chunked_data:
                for chunk in data:
                    b_chunk = chunk if isinstance(chunk, bytes) else str(chunk).encode("utf-8")
                    s.write(f"{len(b_chunk):x}\r\n".encode("ascii"))
                    s.write(b_chunk)
                    s.write(b"\r\n")
                s.write(b"0\r\n\r\n")
            else:
                s.write(data if isinstance(data, bytes) else str(data).encode("utf-8"))

        l = s.readline()
        l_split = l.split(None, 2)
        if len(l_split) < 2:
            raise ValueError("HTTP error: BadStatusLine:\n%s" % l)
        status = int(l_split[1])
        if len(l_split) > 2:
            reason = str(l_split[2].rstrip(), "utf-8")
        while True:
            l = s.readline()
            if not l or l == b"\r\n":
                break
            l_lower = l.lower()
            if l_lower.startswith(b"transfer-encoding:"):
                if b"chunked" in l_lower:
                    raise ValueError("Unsupported " + str(l, "utf-8"))
            elif l_lower.startswith(b"location:") and not 200 <= status <= 299:
                if status in [301, 302, 303, 307, 308]:
                    redirect = str(l.split(b":", 1)[1].strip(), "utf-8")
                else:
                    raise NotImplementedError("Redirect %d not yet supported" % status)
            if parse_headers is False:
                pass
            elif parse_headers is True:
                l_str = str(l, "utf-8")
                if ":" in l_str:
                    k, v = l_str.split(":", 1)
                    if resp_d is not None:
                        resp_d[k] = v.strip()
            else:
                if callable(parse_headers):
                    parse_headers(l, resp_d)
    except OSError:
        s.close()
        raise

    if redirect:
        s.close()
        if status in [301, 302, 303]:
            return request("GET", redirect, None, None, headers, stream)
        else:
            return request(method, redirect, data, json, headers, stream)
    else:
        resp = Response(s)
        resp.status_code = status
        resp.reason = reason
        if resp_d is not None:
            resp.headers = resp_d
        return resp


def head(url, **kw):
    return request("HEAD", url, **kw)


def get(url, **kw):
    return request("GET", url, **kw)


def post(url, **kw):
    return request("POST", url, **kw)


def put(url, **kw):
    return request("PUT", url, **kw)


def patch(url, **kw):
    return request("PATCH", url, **kw)


def delete(url, **kw):
    return request("DELETE", url, **kw)