# Sucht gemeinfreie/CC0-Fotos auf Wikimedia Commons. Aufruf: python3 scripts/archiv_suche.py bitmap "Suchwort" "Suchwort 2"
import json,sys,urllib.parse,urllib.request,re,time
sys.stdout.reconfigure(encoding='utf-8')
typ=sys.argv[1]
for q in sys.argv[2:]:
    print('####',q)
    u="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","format":"json","generator":"search","gsrsearch":q+" filetype:"+typ,"gsrnamespace":6,"gsrlimit":14,"prop":"imageinfo","iiprop":"size|extmetadata"})
    try: d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"video-buero/2 (automated video tool)"}),timeout=30))
    except Exception as e: print(e); time.sleep(30); continue
    for p in d.get("query",{}).get("pages",{}).values():
        i=p["imageinfo"][0];m=i["extmetadata"];l=m.get("LicenseShortName",{}).get("value","")
        if not re.match(r"(public domain|cc0|pd\b)",l.lower()) or (typ=='bitmap' and i['width']<700): continue
        print(' ',p["title"],f'{i["width"]}x{i["height"]}',str(i.get("duration",""))[:5],'|',re.sub('<[^>]+>','',m.get("ImageDescription",{}).get("value",""))[:110].replace('\n',' '))
    time.sleep(9)
