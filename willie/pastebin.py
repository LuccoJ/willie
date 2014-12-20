import web

def paste(text, title="", format='text'):
   global pastebin_key

   response = web.post("http://pastebin.com/api/api_post.php", {
      'api_option': 'paste',
      'api_dev_key': pastebin_key,
      'api_paste_code': text.encode('utf-8'),
      'api_paste_private': '1',
      'api_paste_name': title.encode('utf-8'),
      'api_paste_expire_date': '1D',
      'api_paste_format': format
   })

   if len(response) > 200: raise IOError("Pastebin is not responding correctly")

   return response

# Omit
pastebin_key = '2de0c133e1d1e0c0f3656c7789d8b4be'

