from __future__ import annotations
import os, sys, urllib.request, tempfile, shutil, subprocess
from pathlib import Path
from urllib.parse import urlparse
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal

def release_url():
    env=os.environ.get('PHONEHUB_RELEASE_URL','').strip()
    if env and env.startswith('https://') and 'SEU-DOMINIO' not in env: return env
    for p in (Path(sys._MEIPASS)/'release_url.txt' if getattr(sys,'frozen',False) else Path(__file__).with_name('release_url.txt'), Path.cwd()/'release_url.txt'):
        try:
            value=p.read_text(encoding='utf-8').strip()
            if value.startswith('https://') and 'SEU-DOMINIO' not in value: return value
        except OSError: pass
    return ''
class DownloadWorker(QThread):
    progress=Signal(int); done=Signal(bool,str)
    def __init__(self,url,dest): super().__init__(); self.url=url; self.dest=dest
    def run(self):
        try:
            req=urllib.request.Request(self.url,headers={'User-Agent':'PhoneHUB-Setup/1.0'})
            with urllib.request.urlopen(req,timeout=30) as response, open(self.dest,'wb') as out:
                total=int(response.headers.get('Content-Length','0')); done=0
                while True:
                    chunk=response.read(1024*256)
                    if not chunk: break
                    out.write(chunk); done+=len(chunk)
                    if total: self.progress.emit(min(100,int(done*100/total)))
            if Path(self.dest).stat().st_size<100_000: raise RuntimeError('O arquivo baixado parece pequeno demais; verifique a URL de release.')
            self.done.emit(True,'Download concluído.');
        except Exception as exc:
            try: Path(self.dest).unlink(missing_ok=True)
            except OSError: pass
            self.done.emit(False,str(exc))
class Setup(QDialog):
    def __init__(self):
        super().__init__(); self.setWindowTitle('PhoneHUB Setup'); self.setFixedWidth(480); self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint,False)
        layout=QVBoxLayout(self); title=QLabel('Instalar PhoneHUB'); title.setStyleSheet('font-size:22px;font-weight:700'); layout.addWidget(title)
        self.label=QLabel('O instalador vai baixar a versão publicada pelo desenvolvedor.'); self.label.setWordWrap(True); layout.addWidget(self.label)
        self.bar=QProgressBar(); self.bar.setValue(0); layout.addWidget(self.bar)
        self.button=QPushButton('Baixar e instalar'); self.button.clicked.connect(self.install); layout.addWidget(self.button)
        self.url=release_url()
        if not self.url:
            self.label.setText('URL de release não configurada. O desenvolvedor precisa editar installer/release_url.txt e recompilar setup.exe.'); self.button.setEnabled(False)
    def install(self):
        if not self.url.startswith('https://') or urlparse(self.url).scheme!='https': QMessageBox.critical(self,'URL inválida','A URL precisa usar HTTPS.'); return
        self.button.setEnabled(False); self.label.setText('Baixando PhoneHUB.exe…')
        destdir=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'Programs' / 'PhoneHUB'; destdir.mkdir(parents=True,exist_ok=True)
        self.dest=destdir/'PhoneHUB.exe'; self.worker=DownloadWorker(self.url,str(self.dest)); self.worker.progress.connect(self.bar.setValue); self.worker.done.connect(self.finished_download); self.worker.start()
    def finished_download(self,ok,message):
        if not ok: self.label.setText('Falha no download: '+message); self.button.setEnabled(True); return
        self.bar.setValue(100)
        # Optional companion enables the terminal choice in the launch dialog.
        try:
            companion_url=self.url.rsplit('/',1)[0] + '/PhoneHUB-console.exe'
            req=urllib.request.Request(companion_url,headers={'User-Agent':'PhoneHUB-Setup/1.0'})
            with urllib.request.urlopen(req,timeout=8) as response:
                data=response.read()
            if len(data)>100_000: (self.dest.parent/'PhoneHUB-console.exe').write_bytes(data)
        except Exception: pass
        self.label.setText(f'Instalado em: {self.dest}')
        reply=QMessageBox.question(self,'Instalação concluída','PhoneHUB foi baixado. Deseja abrir agora?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if reply==QMessageBox.StandardButton.Yes:
            try: os.startfile(str(self.dest))
            except Exception as exc: QMessageBox.warning(self,'Não foi possível abrir',str(exc))
        self.button.setText('Concluído')
if __name__=='__main__':
    app=QApplication(sys.argv); app.setStyle('Fusion'); app.setStyleSheet('QWidget{background:#101621;color:#e8edf7;font-size:13px} QPushButton{padding:10px;background:#45d8b3;color:#061711;border:0;border-radius:7px;font-weight:700} QProgressBar{border:1px solid #33445b;border-radius:5px;text-align:center} QProgressBar::chunk{background:#45d8b3}'); w=Setup(); w.show(); sys.exit(app.exec())
