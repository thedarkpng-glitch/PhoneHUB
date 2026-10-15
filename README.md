# PhoneHub — versão inicial

Central desktop para dispositivos Android e, inicialmente, identificação básica de iPhone/iPad. Desenvolvido no CachyOS com Python + PySide6.

## Estado real desta versão

Implementado:
- Interface desktop com abas e tema escuro.
- Descoberta de Androids listados pelo ADB.
- Conexão manual por `IP:porta` usando `adb connect`.
- Identificação de iPhones/iPads usando `idevice_id`, quando `libimobiledevice` e a confiança USB estão configurados.
- Abertura do scrcpy com resolução, bitrate e FPS configuráveis.
- Pré-visualização da câmera Android usando `scrcpy --video-source=camera`.
- Configurações persistidas em `~/.config/phonehub/config.json`.

Ainda não implementado:
- Vídeo incorporado dentro da janela PhoneHub (scrcpy abre uma janela separada).
- Mapeador visual de teclas para coordenadas/toques.
- Saída de webcam virtual integrada com configuração automática do V4L2.
- Roteamento avançado de áudio.
- Espelhamento/controle de tela do iPhone.
- Descoberta automática de IP na rede; por enquanto o IP é informado manualmente.
- Pacote Windows totalmente autocontido com ADB/scrcpy incluídos.

## Instalação no CachyOS

Instale as ferramentas nativas disponíveis nos repositórios:

```bash
sudo pacman -S --needed python python-pip android-tools scrcpy libimobiledevice usbmuxd ffmpeg
```

Se algum nome de pacote tiver mudado nos repositórios, procure o pacote equivalente com `pacman -Ss nome`.

Clone/copie a pasta do projeto e execute:

```bash
cd PhoneHub
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python main.py
```

Ou use `bash scripts/run-linux.sh`.

## Preparar Android

1. Ative as Opções do desenvolvedor e a Depuração USB.
2. Conecte o cabo e aceite a chave RSA no celular.
3. Verifique a conexão:

```bash
adb devices -l
```

Para ADB por rede, habilite a depuração sem fio nas opções do desenvolvedor e use o IP/porta exibido pelo Android. Android moderno pode exigir o fluxo de pareamento (`adb pair IP:PORTA`) antes de conectar. O botão atual chama `adb connect` e não implementa a tela de pareamento ainda.

Não exponha ADB diretamente à internet. Para acesso remoto, use uma rede privada segura/VPN e autenticação adequada.

## Preparar iPhone

Instale `libimobiledevice` e `usbmuxd`, conecte o iPhone por USB e desbloqueie-o. Confirme a solicitação de confiança no iPhone e teste:

```bash
idevice_id -l
ideviceinfo
```

O suporte é deliberadamente limitado: essas ferramentas permitem conversar com vários serviços do iOS, mas não fornecem um equivalente geral ao ADB para controlar a tela, injetar toques ou transmitir a câmera sem app. Não considere o iPhone compatível com espelhamento/control remoto até que um método específico seja implementado e testado.

## Dependências

- Python 3.11+ (Python 3.13 recomendado)
- PySide6 / Qt
- `adb` (pacote `android-tools`)
- `scrcpy`
- Opcional para iOS: `libimobiledevice`, `usbmuxd`
- Opcional para processamento de mídia: FFmpeg
- Linux webcam virtual: V4L2 loopback, a configurar numa etapa posterior

## Build Windows

Execute `scripts/build-windows.bat` no Windows com Python 3.13 instalado. Isso gera um diretório `dist/PhoneHub/`. É um primeiro empacotamento da interface Python, não um instalador completo: ADB, scrcpy e DLLs/dependências precisam ser distribuídos e configurados separadamente. Compile/teste no próprio Windows; um executável Windows deve ser gerado no Windows.

## Estrutura

```text
PhoneHub/
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── scripts/
│   ├── run-linux.sh
│   └── build-windows.bat
└── src/phonehub/
    ├── app.py
    ├── config.py
    └── services/
        ├── android.py
        ├── commands.py
        └── ios.py
```

## Próxima etapa recomendada

Validar no CachyOS: instalação, listagem de dispositivos, conexão USB/IP, espelhamento e câmera Android. Depois disso, evoluir o módulo de vídeo para integração na janela e implementar mapeamento visual de controles.


## Build automático no GitHub Actions

O projeto inclui `.github/workflows/build-windows.yml`. O GitHub compila o app em um runner Windows; não é necessário ter Windows no computador de desenvolvimento. O build usa Python 3.12 para maximizar a compatibilidade com as wheels do PySide6 e PyInstaller.

### Como ativar

1. Envie **todos os arquivos e pastas do projeto** para o repositório, incluindo `.github/workflows/build-windows.yml`. Enviar apenas o ZIP como um arquivo não ativa o workflow.
2. Faça commit e push para a branch `main`. Abra a aba **Actions** para acompanhar o build; os `.exe` ficam em **Artifacts** por 30 dias.
3. Para publicar os `.exe` numa Release, crie e envie uma nova tag, por exemplo `v0.2.1`:
   ```bash
   git tag v0.2.1
   git push origin v0.2.1
   ```
4. O workflow compila `PhoneHUB.exe` e `PhoneHUB-console.exe`; em tags `v*`, também compila `setup.exe` com a URL do executável daquela Release e anexa os três arquivos à Release do GitHub.

**Importante:** o workflow não atualiza uma Release já publicada só porque você enviou um commit para `main`. Para gerar os assets de uma versão, crie uma tag nova. Não reutilize uma tag de release antiga: prefira `v0.2.1`, `v0.2.2` etc. O primeiro build pode falhar por dependências ou configuração; confira o log em **Actions** e corrija antes de divulgar.

O `setup.exe` baixa o `PhoneHUB.exe` da mesma Release. O build do app ainda não embute automaticamente `adb` nem `scrcpy`; o README descreve essa limitação. O instalador não precisa instalar Python na máquina do usuário porque o app é empacotado pelo PyInstaller.
