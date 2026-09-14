# BC-2800Vet Receptor

Aplicativo desktop Windows que escuta a Mindray **BC-2800Vet** pela porta serial RS-232, grava cada exame num **SQLite** (fonte da verdade, com payload bruto) e anexa uma linha na **planilha Excel** para a veterinária completar nome do animal, tutor e observações depois.

- Ícone na bandeja, uma janela e nenhum cadastro prévio.
- Suporta os três formatos que a máquina envia (cão/gato/cavalo, produção, caprino) e o QC (B e C).
- Se a planilha estiver aberta no Excel, o exame fica em fila; o SQLite nunca perde nada.

## Requisitos

- **Windows 10/11**.
- Cabo **DB9** ligado à **porta serial 2** da máquina + adaptador **RS-232 USB** (preferir chipset FTDI). Máx. 12 m.
- Na BC-2800Vet, menu **Setup → Print & comm.** (recomendado):
  - Baud **9600**, Paridade **None**, Data bits **7** (o app aceita 8 e Odd/Even se a sua unidade estiver diferente)
  - **Handshake = On**
  - **Auto transmit = On**
- **Python 3.12+** (só para rodar/testar em modo dev — a versão empacotada não precisa).

## Instalar e rodar em modo desenvolvimento

```powershell
cd C:\Projetos\comunicacao-bc2800
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m bc2800
```

Na primeira execução, a janela abre com o ícone na bandeja. Se houver uma única porta COM disponível, ela é usada automaticamente; senão, clique em **Configurações** e escolha a porta.

## Rodar os testes

```powershell
python -m pytest tests -q
```

Cobre os três layouts de exame (com ID 6 vs 8 dígitos, sem DIFF, caprino sem PLT), QC B e C, handshake ligado/desligado, NACK em corpo truncado e a deduplicação por SHA-256 do payload.

## Gerar o executável (empacotar para a clínica)

```powershell
.\scripts\build.ps1
```

O script instala as dependências, roda o PyInstaller com `packaging/bc2800.spec`, verifica que `dist\BC2800 Receptor\BC2800 Receptor.exe` existe e cria um atalho na **Área de Trabalho**. Basta copiar a pasta `dist\BC2800 Receptor` para o PC da clínica.

A opção **Iniciar com o Windows (bandeja)** em Configurações registra o programa em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` — sem privilégio de administrador.

## O que aparece na tela

- **Barra de status**: porta em uso, conectado/desconectado, “Aguardando exame” / “Exame recebido” / “QC recebido”. O ícone da bandeja fica verde quando a porta está aberta e vermelho quando cai.
- **Cartão do último exame**: ID, espécie, data/hora, WBC, RBC, HGB, PLT (em branco se for caprino, que não tem PLT).
- **Histórico**: tabela filtrável por ID, nome do animal, tutor ou observação. **Duplo clique numa linha** abre o diálogo para completar Nome do animal / Tutor / Observações — o app grava no SQLite e atualiza a linha correspondente na planilha (se ela não estiver aberta).
- **Sincronizar planilha**: força o flush da fila de exames pendentes; o timer já tenta a cada 15 s automaticamente.
- **Configurações**: COM, baud, bits, paridade, handshake, caminho da planilha, autostart.

Fechar a janela **não** encerra o receptor — ele volta para a bandeja. Para encerrar de verdade, use **Sair** no menu da bandeja.

## Onde ficam os arquivos

Tudo mora ao lado do executável (ou da raiz do projeto em dev):

```
data/
  bc2800.sqlite         # fonte da verdade (WAL)
  exames.xlsx           # planilha unificada; o app só anexa linhas novas
  config.json           # porta, baud, paridade, caminho da planilha, autostart
  bc2800.lock           # trava contra segunda instância
  backup/               # cópia diária do .sqlite
logs/
  app.log               # log geral
  YYYYMMDD-HHMMSS-A.bin # payload bruto de cada frame recebido
  YYYYMMDD-HHMMSS-A.hex # o mesmo em hex (útil para calibrar 7 vs 8 bits)
```

Você pode mover a planilha para qualquer lugar (rede, OneDrive) e apontar o novo caminho em **Configurações**.

## Estrutura do código

```
src/bc2800/
  app.py                # bootstrap: QApplication, lock, config, janela
  paths.py              # onde vivem data/, logs/, config.json etc.
  config.py             # carregar/salvar config.json
  logging_setup.py      # logger + dump de frames em logs/
  domain/
    models.py           # Exam, QcEvent
    species.py          # tabela fixa de espécies e formatação
  protocol/
    symbols.py          # ENQ/ACK/EOT/ETX/EOF, tamanho do histograma
    framer.py           # envelope (ENQ/ACK ou STX/EOF), timeouts, NACK
    layouts.py          # offsets dos 3 layouts A + QC B/C
    parser.py           # despacha pelo AnimalType e materializa Exam/QcEvent
  serial_io/
    listener.py         # QThread pyserial, reabre a porta se o USB cair
  persistence/
    sqlite_repo.py      # tabelas exams e qc_events, dedup por SHA-256
    excel_writer.py     # anexa linhas na aba "Exames", edita Nome/Tutor/Obs
    backup.py           # cópia diária do banco
  ui/
    main_window.py      # janela, bandeja, histórico, diálogos
    settings_dialog.py  # COM, baud, bits, paridade, handshake, planilha
    autostart.py        # HKCU\...\Run (só Windows)
    icons.py            # ícone da bandeja
packaging/bc2800.spec   # receita do PyInstaller
scripts/build.ps1       # build + atalho na Área de Trabalho
tests/                  # frames sintéticos + testes de parser/framer/persistência
```

## Solução de problemas

- **“Nenhuma porta COM definida”** — abra **Configurações** e escolha a porta do adaptador USB (aparece como `COMx`).
- **Máquina acusa erro de transmissão** — o programa não estava aberto ou a paridade/baud está diferente da máquina. Deixe o receptor iniciar com o Windows e confira **Configurações**.
- **Planilha não atualiza** — provavelmente o arquivo está aberto no Excel; a badge “N exames aguardando a planilha” aparece na barra superior. Feche o Excel e clique **Sincronizar planilha** (ou espere 15 s).
- **Exame chegou mas o parser não entendeu** — a linha aparece em vermelho na tabela; o payload bruto está em `logs/*.bin` e no SQLite (`raw_payload`). Provavelmente é um ajuste de 7 vs 8 bits/paridade.
- **Encerrar de verdade** — clique com o botão direito no ícone da bandeja → **Sair**. Só fechar a janela mantém o listener ativo.
