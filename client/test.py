import mimetypes


request_file = "article.mp3"
mime = mimetypes.guess_type(request_file)[0]
print(mime)