import urllib.request
import urllib.error

quals = ['1080','720','480','360']
for q in quals:
    print('=== quality', q, '===')
    url = f'http://127.0.0.1:5000/video?url=https://youtu.be/dJWFUBAUM0E?si=f1M30efWiCI0YQ1d&quality={q}'
    try:
        with urllib.request.urlopen(url, timeout=300) as r:
            data = r.read().decode('utf-8')
            print(r.status)
            print(data)
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode()
        except:
            err = str(e)
        print('HTTP', e.code, err)
    except Exception as e:
        print('ERR', e)
