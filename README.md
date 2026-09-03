# InovaInstall

Aplicativo Windows para preparar e executar a instalação do InovaFarma. A ferramenta possui uma interface gráfica em Tkinter, executa as automações auxiliares e acompanha o progresso por logs.

## Funcionalidades

- Seleção da versão do InovaFarma ou download automático da versão mais recente.
- Escolha entre os canais Normal e Preview.
- Instalação no modo Servidor ou Terminal.
- Seleção da variante SQL (`sql2016` ou `sqldev2016`) para instalações de servidor.
- Definição opcional do nome do computador.
- Reinício automático para continuar a instalação após a preparação.
- Exibição do status e dos logs das etapas executadas.

## Requisitos

- Windows.
- Python 3.10 ou superior para executar a partir do código-fonte.
- Permissões administrativas para as etapas de instalação.
- Acesso à internet para consultar releases e baixar o InovaFarma.

## Executar a partir do código-fonte

Na pasta do projeto, execute:

```powershell
python main.py
```

O programa abre a tela de preparação. Informe os dados desejados e clique em **Preparar e continuar**. Quando a preparação terminar, a tela de instalação será aberta automaticamente, a menos que o reinício esteja habilitado.

## Executável

O executável empacotado está disponível em `inovainstall/InovaInstall.exe`. Ele já inclui os executáveis auxiliares necessários:

- `terminal.exe`
- `recursos.exe`
- `download.exe`
- `instalacao.exe`

Para gerar um novo executável com PyInstaller:

```powershell
.\gerar_executavel.ps1
```

O script gera ou substitui o arquivo `inovainstall/InovaInstall.exe` e mantém os executáveis auxiliares na mesma pasta. Para executar o script caso a política do PowerShell bloqueie scripts locais, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\gerar_executavel.ps1
```

Depois de alterar o código, execute o script, teste o executável e envie o arquivo atualizado ao GitHub.

## Fluxo de instalação

1. `main.py` inicia a etapa de preparação.
2. `preparacao.py` executa as automações auxiliares e, no modo Servidor, faz o download necessário.
3. O estado da preparação é salvo em `estado.json`.
4. `segunda_etapa.py` inicia a instalação e exibe os status e logs.
5. Se o reinício estiver habilitado, o Windows reinicia e continua a instalação automaticamente.

## Logs e estado

Por padrão, o estado e os logs são armazenados em:

```text
C:\ProgramData\InovaInstall\
```

Os logs individuais ficam na subpasta `logs`. Eles são úteis para diagnosticar falhas nas automações ou no download.

## Integrações externas

As versões do InovaFarma são consultadas nas releases do GitHub de `precisaosistemas/inovafarma`. O canal Normal usa a release estável; o canal Preview usa a release marcada como pré-lançamento.

## Arquivos principais

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Ponto de entrada da aplicação. |
| `preparacao.py` | Tela de preparação, download e persistência do estado. |
| `segunda_etapa.py` | Tela e execução da instalação final. |
| `InovaInstall.spec` | Configuração do empacotamento com PyInstaller. |
| `gerar_executavel.ps1` | Gera o executável atualizado na pasta `inovainstall`. |
