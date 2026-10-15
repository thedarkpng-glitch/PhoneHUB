from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import os
if os.name=='nt':
    APP_DIR=Path(os.environ.get('APPDATA',str(Path.home()))) / 'PhoneHUB'
else: APP_DIR=Path.home()/'.config'/'phonehub'
CONFIG_FILE=APP_DIR/'config.json'
DEFAULT_CONFIG: dict[str,Any]={'theme':'Escuro (PhoneHUB)','refresh_seconds':4,'video':{'max_size':1280,'bit_rate':'8M','max_fps':60},'audio':{'enabled':True,'microphone':False,'low_latency':True},'camera':{'facing':'back','size':'1280x720','fps':30,'mic':True},'render_backend':'Automático (recomendado)','low_latency':True,'saved_devices':[],'profiles':{'Padrão':{'description':'Teclado/mouse via scrcpy; não injeta toques automaticamente.'},'Roblox Android':{'description':'Entrada externa depende de suporte do jogo.'}}}
def load_config():
    APP_DIR.mkdir(parents=True,exist_ok=True)
    if not CONFIG_FILE.exists(): save_config(DEFAULT_CONFIG); return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        data=json.loads(CONFIG_FILE.read_text(encoding='utf-8')); merged=json.loads(json.dumps(DEFAULT_CONFIG))
        for key,value in data.items():
            if isinstance(value,dict) and isinstance(merged.get(key),dict): merged[key].update(value)
            else: merged[key]=value
        return merged
    except (OSError,json.JSONDecodeError): return json.loads(json.dumps(DEFAULT_CONFIG))
def save_config(data):
    APP_DIR.mkdir(parents=True,exist_ok=True); CONFIG_FILE.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
