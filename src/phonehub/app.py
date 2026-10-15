from __future__ import annotations
import os, sys, platform, subprocess
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton, QSpinBox, QTabWidget,
    QVBoxLayout, QWidget, QCheckBox, QGroupBox, QFrame, QDialog, QDialogButtonBox,
    QGridLayout, QStackedWidget)
from .config import load_config, save_config
from .services.android import list_devices, connect_ip, start_scrcpy
from .services.ios import list_ios_devices, device_name

STYLE = r"""
* { font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: #0b0f17; color: #e8edf7; }
QWidget#sidebar { background: #101621; border-right: 1px solid #202a3a; }
QLabel#brand { font-size: 25px; font-weight: 800; letter-spacing: 1px; color: #f5f8ff; }
QLabel#brandAccent { color: #62e6c6; font-size: 25px; font-weight: 800; }
QLabel#muted, QLabel.muted { color: #8794a9; }
QLabel#pageTitle { font-size: 24px; font-weight: 750; color: #f5f8ff; }
QLabel#pageSubtitle { color: #8d9bb0; font-size: 13px; }
QFrame#hero, QGroupBox, QFrame#metric { background: #111925; border: 1px solid #263246; border-radius: 13px; }
QFrame#hero { border: 1px solid #2b4354; background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #13212b,stop:1 #111925); }
QLabel#heroTitle { font-size: 19px; font-weight: 700; }
QLabel#metricValue { font-size: 22px; font-weight: 800; color: #62e6c6; }
QLabel#metricLabel { color: #91a0b5; font-size: 11px; }
QTabWidget::pane { border: 1px solid #263246; border-radius: 12px; top: -1px; }
QTabBar::tab { background: #111925; color: #91a0b5; padding: 11px 17px; margin: 3px 4px 0 0; border-radius: 8px; }
QTabBar::tab:selected { color: #f7fbff; background: #21483f; border: 1px solid #2b7868; }
QPushButton { background: #1c2838; color: #e9f0fa; border: 1px solid #33445b; padding: 10px 14px; border-radius: 8px; font-weight: 600; }
QPushButton:hover { background: #29394e; border-color: #4d6788; }
QPushButton:pressed { background: #172331; }
QPushButton#primary { background: #45d8b3; color: #061711; border: 1px solid #45d8b3; }
QPushButton#primary:hover { background: #69e8c9; }
QPushButton#quiet { background: transparent; border-color: #263246; color: #b3c0d2; }
QLineEdit, QComboBox, QSpinBox, QListWidget { background: #0c121c; border: 1px solid #2a374b; padding: 9px 10px; border-radius: 8px; selection-background-color: #285b50; }
QComboBox::drop-down { border: 0; width: 24px; }
QListWidget { padding: 7px; }
QListWidget::item { padding: 11px; border-radius: 6px; }
QListWidget::item:selected { background: #1e3b39; border: 1px solid #286e60; }
QGroupBox { margin-top: 14px; padding: 15px 12px 12px 12px; font-weight: 700; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #c3d0e1; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 17px; height: 17px; }
QStatusBar { background: #0b0f17; color: #93a1b5; border-top: 1px solid #202a3a; }
QScrollBar:vertical { background: #0b0f17; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #2b394d; min-height: 22px; border-radius: 5px; }
"""

class LaunchDialog(QDialog):
    def __init__(self):
        super().__init__(); self.choice = 'app'
        self.setWindowTitle('PhoneHUB — modo de execução'); self.setFixedWidth(470)
        layout=QVBoxLayout(self); layout.setContentsMargins(26,24,26,22); layout.setSpacing(12)
        title=QLabel('Como você quer iniciar?'); title.setObjectName('pageTitle'); layout.addWidget(title)
        sub=QLabel('Escolha a interface completa ou o modo de terminal para diagnóstico.'); sub.setObjectName('pageSubtitle'); sub.setWordWrap(True); layout.addWidget(sub)
        app=QPushButton('Abrir aplicativo'); app.setObjectName('primary'); app.setMinimumHeight(46)
        term=QPushButton('Rodar pelo terminal'); term.setMinimumHeight(46)
        app.clicked.connect(lambda: self.finish('app')); term.clicked.connect(lambda: self.finish('terminal'))
        layout.addSpacing(8); layout.addWidget(app); layout.addWidget(term)
        note=QLabel('O modo terminal mostra versões e dependências detectadas; não abre a interface gráfica.'); note.setObjectName('muted'); note.setWordWrap(True); layout.addWidget(note)
    def finish(self, choice): self.choice=choice; self.accept()

class PhoneHubWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.config=load_config(); self.android_devices=[]
        self.setWindowTitle('PhoneHUB'); self.resize(1180,780); self.setMinimumSize(900,620)
        central=QWidget(); outer=QHBoxLayout(central); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        sidebar=QWidget(); sidebar.setObjectName('sidebar'); sidebar.setFixedWidth(215); side=QVBoxLayout(sidebar); side.setContentsMargins(18,24,18,18); side.setSpacing(9)
        brandrow=QHBoxLayout(); brand=QLabel('Phone'); brand.setObjectName('brand'); accent=QLabel('HUB'); accent.setObjectName('brandAccent'); brandrow.addWidget(brand); brandrow.addWidget(accent); brandrow.addStretch(); side.addLayout(brandrow)
        tag=QLabel('DEVICE CONTROL STUDIO'); tag.setObjectName('muted'); side.addWidget(tag); side.addSpacing(20)
        self.nav=[]
        for text,idx in [('Visão geral',0),('Tela e desempenho',1),('Câmera',2),('Áudio',3),('Controles',4),('Configurações',5)]:
            b=QPushButton(text); b.setObjectName('quiet'); b.setCheckable(True); b.clicked.connect(lambda checked=False,i=idx:self.go_tab(i)); self.nav.append(b); side.addWidget(b)
        side.addStretch(); self.connection_label=QLabel('●  Procurando dispositivos'); self.connection_label.setStyleSheet('color:#62e6c6'); self.connection_label.setWordWrap(True); side.addWidget(self.connection_label)
        version=QLabel('PhoneHUB 0.2.0\nQt / scrcpy / ADB'); version.setObjectName('muted'); side.addWidget(version)
        main=QWidget(); ml=QVBoxLayout(main); ml.setContentsMargins(26,23,26,20); ml.setSpacing(17)
        top=QHBoxLayout(); headings=QVBoxLayout(); self.page_title=QLabel('Visão geral'); self.page_title.setObjectName('pageTitle'); self.page_sub=QLabel('Conecte, espelhe e controle seu dispositivo.'); self.page_sub.setObjectName('pageSubtitle'); headings.addWidget(self.page_title); headings.addWidget(self.page_sub); top.addLayout(headings); top.addStretch()
        refresh=QPushButton('↻  Atualizar dispositivos'); refresh.clicked.connect(self.refresh_devices); top.addWidget(refresh); ml.addLayout(top)
        self.tabs=QTabWidget(); self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._devices_tab(),'Dispositivos'); self.tabs.addTab(self._screen_tab(),'Tela'); self.tabs.addTab(self._webcam_tab(),'Câmera'); self.tabs.addTab(self._audio_tab(),'Áudio'); self.tabs.addTab(self._controls_tab(),'Controles'); self.tabs.addTab(self._settings_tab(),'Configurações')
        self.tabs.currentChanged.connect(self._sync_nav); ml.addWidget(self.tabs,1)
        outer.addWidget(sidebar); outer.addWidget(main,1); self.setCentralWidget(central)
        self.status=self.statusBar().showMessage('Pronto. Conecte um Android por USB ou configure ADB por Wi-Fi.')
        self.refresh_timer=QTimer(self); self.refresh_timer.timeout.connect(self.refresh_devices); self.refresh_timer.start(max(3,int(self.config.get('refresh_seconds',4)))*1000)
        self._sync_nav(0); self.refresh_devices()
    def go_tab(self,idx): self.tabs.setCurrentIndex(idx)
    def _sync_nav(self,idx):
        titles=[('Visão geral','Conecte, espelhe e controle seu dispositivo.'),('Tela e desempenho','Ajuste qualidade, latência e uso de recursos.'),('Câmera','Configure a câmera Android e sua pré-visualização.'),('Áudio','Escolha o que será encaminhado durante a sessão.'),('Controles','Use teclado e mouse e organize perfis por jogo.'),('Configurações','Preferências locais e diagnóstico do sistema.')]
        self.page_title.setText(titles[idx][0]); self.page_sub.setText(titles[idx][1])
        for i,b in enumerate(self.nav): b.setChecked(i==idx); b.setStyleSheet('background:#1b3834;border:1px solid #2c6c5e;color:#f2fff9;' if i==idx else '')
    def _metric(self,value,label):
        f=QFrame(); f.setObjectName('metric'); l=QVBoxLayout(f); l.setContentsMargins(15,13,15,13); v=QLabel(value); v.setObjectName('metricValue'); t=QLabel(label); t.setObjectName('metricLabel'); l.addWidget(v); l.addWidget(t); return f
    def _devices_tab(self):
        tab=QWidget(); layout=QVBoxLayout(tab); layout.setContentsMargins(4,14,4,4); layout.setSpacing(14)
        hero=QFrame(); hero.setObjectName('hero'); h=QHBoxLayout(hero); h.setContentsMargins(22,19,22,19); left=QVBoxLayout(); t=QLabel('Seu dispositivo. Sua tela. Seu controle.'); t.setObjectName('heroTitle'); d=QLabel('Conexão USB ou ADB por rede local. Sem instalar um app no Android.'); d.setObjectName('pageSubtitle'); d.setWordWrap(True); left.addWidget(t); left.addWidget(d); h.addLayout(left,1); self.hero_status=QLabel('AGUARDANDO'); self.hero_status.setStyleSheet('color:#62e6c6;font-weight:800;letter-spacing:1px'); h.addWidget(self.hero_status); layout.addWidget(hero)
        metrics=QGridLayout(); metrics.setSpacing(10); self.android_metric=self._metric('0','Android detectados'); self.ios_metric=self._metric('0','iPhone/iPad detectados'); self.transport_metric=self._metric('USB / Wi-Fi','Conexão'); metrics.addWidget(self.android_metric,0,0); metrics.addWidget(self.ios_metric,0,1); metrics.addWidget(self.transport_metric,0,2); layout.addLayout(metrics)
        group=QGroupBox('Dispositivos Android — ADB'); gl=QVBoxLayout(group); self.android_list=QListWidget(); self.android_list.setMinimumHeight(130); gl.addWidget(self.android_list)
        row=QHBoxLayout(); self.ip_input=QLineEdit(); self.ip_input.setPlaceholderText('Endereço ADB (ex.: 192.168.1.50:5555)'); connect_btn=QPushButton('Conectar por IP'); connect_btn.setObjectName('primary'); connect_btn.clicked.connect(self._connect_ip); row.addWidget(self.ip_input,1); row.addWidget(connect_btn); gl.addLayout(row); layout.addWidget(group,2)
        group2=QGroupBox('iPhone / iPad — serviços disponíveis'); g2=QVBoxLayout(group2); self.ios_list=QListWidget(); self.ios_list.setMaximumHeight(105); g2.addWidget(self.ios_list); note=QLabel('No iOS, esta versão detecta dispositivos e informações acessíveis. Espelhamento e controle completo sem app não são suportados de forma geral pelo sistema.'); note.setObjectName('muted'); note.setWordWrap(True); g2.addWidget(note); layout.addWidget(group2,1)
        actions=QHBoxLayout(); mirror=QPushButton('Iniciar espelhamento'); mirror.setObjectName('primary'); mirror.clicked.connect(lambda:self._start_selected(False)); camera=QPushButton('Abrir câmera'); camera.clicked.connect(lambda:self._start_selected(True)); actions.addWidget(mirror); actions.addWidget(camera); actions.addStretch(); layout.addLayout(actions); return tab
    def _screen_tab(self):
        tab=QWidget(); layout=QVBoxLayout(tab); layout.setContentsMargins(4,14,4,4)
        group=QGroupBox('Perfil de imagem'); form=QFormLayout(group); self.max_size=QComboBox(); self.max_size.addItems(['720','960','1280','1600','1920','2560']); self.max_size.setCurrentText(str(self.config['video'].get('max_size',1280)))
        self.bit_rate=QComboBox(); self.bit_rate.addItems(['2M','4M','6M','8M','12M','16M','24M']); self.bit_rate.setCurrentText(self.config['video'].get('bit_rate','8M'))
        self.max_fps=QComboBox(); self.max_fps.addItems(['15','24','30','45','60','90','120']); self.max_fps.setCurrentText(str(self.config['video'].get('max_fps',60)))
        self.render_backend=QComboBox(); self.render_backend.addItems(['Automático (recomendado)','OpenGL / GPU (quando disponível)','Compatibilidade / CPU']); self.render_backend.setCurrentText(self.config.get('render_backend','Automático (recomendado)'))
        self.low_latency=QCheckBox('Priorizar baixa latência (pode reduzir qualidade)'); self.low_latency.setChecked(self.config.get('low_latency',True))
        form.addRow('Resolução máxima',self.max_size); form.addRow('Bitrate de vídeo',self.bit_rate); form.addRow('FPS máximo',self.max_fps); form.addRow('Renderização no PC',self.render_backend); form.addRow('',self.low_latency); layout.addWidget(group)
        hint=QLabel('A qualidade final depende do aparelho, cabo, rede e decodificador. O scrcpy usa codificação no telefone e decodificação no PC. A opção de renderização configura o ambiente do processo quando aplicável; ela não cria uma GPU dedicada nem garante que toda a carga passe pela placa escolhida.'); hint.setObjectName('muted'); hint.setWordWrap(True); layout.addWidget(hint)
        btn=QPushButton('Salvar e iniciar espelhamento'); btn.setObjectName('primary'); btn.clicked.connect(self._save_and_mirror); layout.addWidget(btn); layout.addStretch(); return tab
    def _webcam_tab(self):
        tab=QWidget(); layout=QVBoxLayout(tab); layout.setContentsMargins(4,14,4,4); group=QGroupBox('Câmera do Android'); form=QFormLayout(group)
        self.camera_facing=QComboBox(); self.camera_facing.addItems(['back','front','external']); self.camera_size=QComboBox(); self.camera_size.addItems(['640x480','1280x720','1920x1080']); self.camera_fps=QComboBox(); self.camera_fps.addItems(['15','24','30','60','120'])
        cam=self.config.get('camera',{}); self.camera_facing.setCurrentText(cam.get('facing','back')); self.camera_size.setCurrentText(cam.get('size','1280x720')); self.camera_fps.setCurrentText(str(cam.get('fps',30)))
        self.camera_mic=QCheckBox('Usar microfone do celular nesta sessão'); self.camera_mic.setChecked(self.config.get('camera',{}).get('mic',True))
        form.addRow('Lente',self.camera_facing); form.addRow('Resolução',self.camera_size); form.addRow('FPS',self.camera_fps); form.addRow('',self.camera_mic); layout.addWidget(group)
        btn=QPushButton('Abrir pré-visualização'); btn.setObjectName('primary'); btn.clicked.connect(lambda:self._start_selected(True)); layout.addWidget(btn)
        note=QLabel('Esta ação abre a janela nativa do scrcpy. Transformar o vídeo em webcam virtual para Discord/OBS exige um backend específico (V4L2 no Linux ou câmera virtual no Windows) e não é ativado automaticamente nesta versão.'); note.setObjectName('muted'); note.setWordWrap(True); layout.addWidget(note); layout.addStretch(); return tab
    def _audio_tab(self):
        tab=QWidget(); layout=QVBoxLayout(tab); layout.setContentsMargins(4,14,4,4); group=QGroupBox('Roteamento de áudio'); form=QVBoxLayout(group)
        self.audio_enabled=QCheckBox('Reproduzir o áudio do Android no computador'); self.audio_enabled.setChecked(self.config.get('audio',{}).get('enabled',True)); self.mic_enabled=QCheckBox('Capturar microfone do celular (quando compatível)'); self.mic_enabled.setChecked(self.config.get('audio',{}).get('microphone',False)); self.audio_low=QCheckBox('Preferir baixa latência de áudio'); self.audio_low.setChecked(self.config.get('audio',{}).get('low_latency',True))
        form.addWidget(self.audio_enabled); form.addWidget(self.mic_enabled); form.addWidget(self.audio_low); layout.addWidget(group)
        note=QLabel('O áudio encaminhado depende da versão do Android, permissões e aplicativo em reprodução. O scrcpy não oferece controle universal de todo microfone/saída do PC; o roteamento do sistema operacional continua sendo responsável pelos dispositivos de áudio locais.'); note.setObjectName('muted'); note.setWordWrap(True); layout.addWidget(note); save=QPushButton('Salvar preferências de áudio'); save.clicked.connect(self.save_settings); layout.addWidget(save); layout.addStretch(); return tab
    def _controls_tab(self):
        tab=QWidget(); layout=QVBoxLayout(tab); layout.setContentsMargins(4,14,4,4); group=QGroupBox('Teclado e mouse'); form=QFormLayout(group)
        self.profile=QComboBox(); self.profile.addItems(list(self.config.get('profiles',{'Padrão':{}}).keys()) or ['Padrão']); self.input_mode=QComboBox(); self.input_mode.addItems(['Teclado e mouse do scrcpy','Perfil de jogo (experimental / sem mapa de toques)']); form.addRow('Perfil',self.profile); form.addRow('Modo de entrada',self.input_mode); layout.addWidget(group)
        start=QPushButton('Iniciar sessão para jogar'); start.setObjectName('primary'); start.clicked.connect(lambda:self._start_selected(False)); layout.addWidget(start)
        note=QLabel('O teclado e o mouse são encaminhados pelo scrcpy. Roblox no Android funciona com isso apenas nas experiências que aceitam entrada externa. Este projeto ainda não injeta um mapa universal de teclas para toques na tela; isso exige perfis por jogo e uma camada de mapeamento dedicada. O PhoneHUB não executa Roblox de PC no telefone.'); note.setObjectName('muted'); note.setWordWrap(True); layout.addWidget(note); layout.addStretch(); return tab
    def _settings_tab(self):
        tab=QWidget(); layout=QVBoxLayout(tab); layout.setContentsMargins(4,14,4,4); group=QGroupBox('Preferências gerais'); form=QFormLayout(group)
        self.refresh_seconds=QSpinBox(); self.refresh_seconds.setRange(3,30); self.refresh_seconds.setValue(int(self.config.get('refresh_seconds',4))); self.theme=QComboBox(); self.theme.addItems(['Escuro (PhoneHUB)','Sistema']); self.theme.setCurrentText(self.config.get('theme','Escuro (PhoneHUB)')); form.addRow('Atualização automática (segundos)',self.refresh_seconds); form.addRow('Tema',self.theme); layout.addWidget(group)
        sysgroup=QGroupBox('Diagnóstico'); sysform=QFormLayout(sysgroup); sysform.addRow('Sistema operacional',QLabel(f'{platform.system()} {platform.release()}')); sysform.addRow('Python',QLabel(platform.python_version())); sysform.addRow('Renderização',QLabel(self.config.get('render_backend','Automático (recomendado)'))); layout.addWidget(sysgroup)
        save=QPushButton('Salvar todas as configurações'); save.setObjectName('primary'); save.clicked.connect(self.save_settings); layout.addWidget(save)
        note=QLabel('Segurança: use ADB por Wi-Fi apenas em uma rede confiável e não exponha a porta ADB diretamente à internet. Para empacotar no Windows, consulte README.md e scripts/build-windows.bat.'); note.setObjectName('muted'); note.setWordWrap(True); layout.addWidget(note); layout.addStretch(); return tab
    def selected_android(self):
        idx=self.android_list.currentRow()
        if idx<0 or idx>=len(self.android_devices): return None
        dev=self.android_devices[idx]
        return dev if dev.state=='device' else None
    def refresh_devices(self):
        current=self.android_list.currentItem().text() if self.android_list.currentItem() else ''
        devices,error=list_devices(); self.android_devices=devices; self.android_list.clear()
        for dev in devices: self.android_list.addItem(dev.label)
        if current:
            matches=self.android_list.findItems(current,Qt.MatchFlag.MatchExactly)
            if matches: self.android_list.setCurrentItem(matches[0])
        ids,ios_error=list_ios_devices(); self.ios_list.clear()
        for udid in ids: self.ios_list.addItem(f'{device_name(udid)} — {udid}')
        self._set_metric(self.android_metric,str(len(devices))); self._set_metric(self.ios_metric,str(len(ids)))
        connected=sum(d.state=='device' for d in devices); self.hero_status.setText('CONECTADO' if connected else 'AGUARDANDO'); self.connection_label.setText(f'●  {connected} Android conectado(s)' if connected else '●  Nenhum Android conectado')
        self.statusBar().showMessage(error if not devices and error else (ios_error if not ids and ios_error and 'não instalado' not in ios_error else 'Dispositivos atualizados.'))
    def _set_metric(self,frame,value):
        labels=frame.findChildren(QLabel); 
        if labels: labels[0].setText(value)
    def _connect_ip(self):
        ok,msg=connect_ip(self.ip_input.text()); self.statusBar().showMessage(msg); self.refresh_devices()
        if not ok: QMessageBox.warning(self,'Conexão ADB',msg)
    def _start_selected(self,camera=False):
        dev=self.selected_android()
        if not dev:
            QMessageBox.information(self,'Nenhum Android selecionado','Selecione um dispositivo Android em estado "device" e autorize a depuração USB no telefone.'); return
        opts={'max_size':int(self.max_size.currentText()),'bit_rate':self.bit_rate.currentText(),'max_fps':int(self.max_fps.currentText()),'audio_enabled':self.audio_enabled.isChecked(),'microphone_enabled':self.mic_enabled.isChecked() if hasattr(self,'mic_enabled') else False,'camera_facing':self.camera_facing.currentText(),'camera_size':self.camera_size.currentText(),'camera_fps':int(self.camera_fps.currentText()),'camera_mic':self.camera_mic.isChecked() if hasattr(self,'camera_mic') else True,'render_backend':self.render_backend.currentText() if hasattr(self,'render_backend') else 'Automático (recomendado)','low_latency':self.low_latency.isChecked() if hasattr(self,'low_latency') else True}
        ok,msg=start_scrcpy(dev.serial,opts,camera=camera); self.statusBar().showMessage(msg)
        if not ok: QMessageBox.warning(self,'Não foi possível iniciar',msg)
    def _save_and_mirror(self): self.save_settings(); self._start_selected(False)
    def save_settings(self):
        self.config['video']={'max_size':int(self.max_size.currentText()),'bit_rate':self.bit_rate.currentText(),'max_fps':int(self.max_fps.currentText())}
        self.config['audio']={'enabled':self.audio_enabled.isChecked(),'microphone':self.mic_enabled.isChecked(),'low_latency':self.audio_low.isChecked()}
        self.config['camera']={'facing':self.camera_facing.currentText(),'size':self.camera_size.currentText(),'fps':int(self.camera_fps.currentText()),'mic':self.camera_mic.isChecked()}
        self.config['render_backend']=self.render_backend.currentText(); self.config['low_latency']=self.low_latency.isChecked(); self.config['refresh_seconds']=self.refresh_seconds.value(); self.config['theme']=self.theme.currentText()
        save_config(self.config); self.refresh_timer.setInterval(self.refresh_seconds.value()*1000); self.statusBar().showMessage('Configurações salvas.')

def terminal_diagnostics():
    from .services.commands import executable
    print('PhoneHUB — diagnóstico'); print('Sistema:',platform.platform()); print('Python:',sys.version.split()[0])
    for tool in ('adb','scrcpy','idevice_id','ideviceinfo','ffmpeg'):
        print(f'{tool}:',executable(tool) or 'não encontrado')
    print('\nPara abrir a interface: execute PhoneHUB sem o argumento --terminal.')
    return 0

def main() -> int:
    if '--terminal' in sys.argv: return terminal_diagnostics()
    app=QApplication(sys.argv); app.setApplicationName('PhoneHUB'); app.setOrganizationName('PhoneHUB'); app.setStyle('Fusion'); app.setStyleSheet(STYLE)
    if '--skip-launcher' not in sys.argv:
        chooser=LaunchDialog()
        if chooser.exec()!=QDialog.DialogCode.Accepted: return 0
        if chooser.choice=='terminal':
            if getattr(sys,'frozen',False):
                companion=os.path.join(os.path.dirname(sys.executable),'PhoneHUB-console.exe')
                if os.path.isfile(companion):
                    subprocess.Popen([companion,'--terminal']); return 0
                QMessageBox.information(None,'Modo terminal','O PhoneHUB-console.exe não está instalado junto do aplicativo. No pacote de desenvolvimento, execute main.py --terminal pelo CMD.')
                return 0
            return terminal_diagnostics()
    window=PhoneHubWindow(); window.show(); return app.exec()
