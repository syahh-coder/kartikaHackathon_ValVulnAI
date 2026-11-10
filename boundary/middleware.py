class BodyLimit:
    """Bound streamed bodies before the target application's parser."""
    def __init__(self,app,maximum=4096):
        self.app,self.maximum=app,maximum

    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or scope["method"] in {"GET","HEAD","OPTIONS"}:
            return await self.app(scope,receive,send)
        chunks=[]
        size=0
        while True:
            message=await receive()
            if message["type"]=="http.disconnect":
                return
            data=message.get("body",b"")
            size+=len(data)
            if size>self.maximum:
                await send({"type":"http.response.start","status":413,"headers":[(b"content-type",b"application/json")]})
                return await send({"type":"http.response.body","body":b'{"error":"BODY_LIMIT"}'})
            chunks.append(data)
            if not message.get("more_body",False):
                break
        delivered=False
        async def bounded():
            nonlocal delivered
            if delivered: return await receive()
            delivered=True
            return {"type":"http.request","body":b"".join(chunks),"more_body":False}
        await self.app(scope,bounded,send)
