from __future__ import annotations
import os, subprocess
from dataclasses import dataclass
from .commands import executable, run_command
@dataclass
class AndroidDevice:
    serial: str
    state: str
    model: str = ''
    @property
    def label(self): return f"{self.model or 'Android'} — {self.serial} [{self.state}]"
def adb_available(): return executable('adb') is not None
def list_devices():
    if not adb_available(): return [], 'ADB não encontrado. Instale Android Platform Tools.'
    result=run_command(['adb','devices','-l'],timeout=5)
    if not result.ok and not result.output: return [],result.error or 'Não foi possível consultar o ADB.'
    devices=[]
    for line in result.output.splitlines()[1:]:
        parts=line.split()
        if len(parts)<2 or parts[0].startswith('*'): continue
        model=''
        for item in parts[2:]:
            if item.startswith('model:'): model=item.removeprefix('model:').replace('_',' '); break
        devices.append(AndroidDevice(parts[0],parts[1],model))
    return devices,result.error
def connect_ip(address):
    address=address.strip()
    if not address: return False,'Informe IP:porta, por exemplo 192.168.1.50:5555.'
    if '://' in address or '/' in address or ' ' in address: return False,'Endereço inválido. Use IP:porta, sem protocolo.'
    result=run_command(['adb','connect',address],timeout=10); msg=result.output or result.error or 'Sem resposta do ADB.'
    return result.ok and 'unable to connect' not in msg.lower(),msg
def start_scrcpy(serial,options,camera=False):
    scrcpy=executable('scrcpy')
    if not scrcpy: return False,'scrcpy não encontrado. Instale o scrcpy ou configure o caminho do executável.'
    args=[scrcpy,'--serial',serial]
    if camera:
        args += ['--video-source=camera',f"--camera-facing={options.get('camera_facing','back')}",f"--camera-size={options.get('camera_size','1280x720')}",f"--camera-fps={max(1,min(int(options.get('camera_fps',30)),120))}"]
        if options.get('camera_mic',True): args.append('--audio-source=mic')
        else: args.append('--no-audio')
    else:
        args += [f"--max-size={int(options.get('max_size',1280))}",f"--video-bit-rate={options.get('bit_rate','8M')}",f"--max-fps={int(options.get('max_fps',60))}"]
        if not options.get('audio_enabled',True): args.append('--no-audio')
        if options.get('microphone_enabled',False): args.append('--audio-source=mic')
    env=os.environ.copy(); backend=options.get('render_backend','')
    # This is a best-effort Qt/OpenGL preference for the child process; scrcpy's renderer may use a different backend.
    if 'Compatibilidade' in backend: env.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
    elif 'OpenGL' in backend: env.pop('LIBGL_ALWAYS_SOFTWARE',None)
    try:
        subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env,start_new_session=(os.name!='nt'),creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0))
        return True,'scrcpy iniciado. Para jogar, use a janela do scrcpy e confira se o jogo Android aceita teclado/mouse.'
    except OSError as exc: return False,f'Falha ao iniciar scrcpy: {exc}'
