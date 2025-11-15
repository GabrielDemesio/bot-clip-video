
# Video Lesson Splitter

🎬 Ferramenta profissional em Python para dividir vídeos longos de cursos em **aulas individuais**,
usando **detecção automática de silêncios** no áudio como pontos de corte.

## ✨ Features

- ✅ **Detecção automática de silêncios** para identificar quebras entre aulas
- ✅ **Processamento otimizado com FFmpeg** (10-50x mais rápido que re-encoding)
- ✅ **Barras de progresso** em tempo real para todas as etapas
- ✅ **Configuração flexível** via arquivo YAML
- ✅ **Logging profissional** com níveis configuráveis
- ✅ **Validação robusta** de arquivos e dependências
- ✅ **Tratamento de erros** com exceções customizadas
- ✅ **Arquitetura limpa** separada em camadas

## 🏗️ Arquitetura

```
app/
├── core/           # Regras de negócio
│   ├── config.py           # Configurações (DTOs)
│   ├── config_loader.py    # Carregador de config YAML
│   ├── dto.py              # Data Transfer Objects
│   ├── exceptions.py       # Exceções customizadas
│   ├── logger.py           # Sistema de logging
│   ├── silence_detector.py # Detecção de silêncios
│   ├── validators.py       # Validação de arquivos
│   ├── video_splitter.py   # Divisão de vídeos
│   └── utils.py            # Utilitários
├── services/       # Orquestração
│   └── module_processor.py # Processador de módulos
└── cli/            # Interface CLI
    ├── main.py             # Ponto de entrada
    └── menu.py             # Menu interativo
```

## 📋 Requisitos

- **Python 3.10+**
- **FFmpeg** instalado no sistema
- Dependências Python (instaladas automaticamente):
  - `moviepy>=1.0.3`
  - `pydub>=0.25.1`
  - `tqdm>=4.65.0`
  - `pyyaml>=6.0`

## 📁 Estrutura de Pastas

```text
video-lesson-splitter/
├── app/                    # Código fonte
│   ├── core/              # Lógica de negócio
│   ├── services/          # Orquestração
│   └── cli/               # Interface CLI
├── videos_input/          # 📥 Coloque seus vídeos aqui
├── lessons_output/        # 📤 Aulas geradas (criado automaticamente)
├── config.yaml            # ⚙️ Configurações
├── main.py                # 🚀 Ponto de entrada
├── requirements.txt       # 📦 Dependências
├── pyproject.toml         # 📝 Metadados do projeto
└── README.md              # 📖 Documentação
```

## 🚀 Como Usar

### Opção 1: Docker (Recomendado) 🐳

```bash
# 1. Build da imagem
docker-compose build

# 2. Adicione seus vídeos
cp seu_video.mp4 videos_input/

# 3. Execute
docker-compose run --rm video-splitter
```

**Vantagens:**
- ✅ Não precisa instalar Python ou FFmpeg
- ✅ Ambiente isolado e reproduzível
- ✅ Funciona em qualquer sistema operacional

📖 **[Guia Completo de Docker](DOCKER.md)**

---

### Opção 2: Instalação Local

```bash
# Clone o repositório (ou baixe o código)
git clone <seu-repo>
cd video-lesson-splitter

# Crie um ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 2. Instale o FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Baixe de [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- Adicione ao PATH do sistema

### 3. Configure (Opcional)

Edite `config.yaml` para ajustar:
- Sensibilidade de detecção de silêncio
- Duração mínima das aulas
- Padding antes/depois de cada aula
- Caminhos de entrada/saída

```yaml
silence_detection:
  min_silence_len_ms: 10000        # 10 segundos de silêncio
  silence_thresh_offset_db: 30     # Sensibilidade

lesson_split:
  min_lesson_duration_sec: 60      # Aulas mínimas de 1 minuto
  padding_before_sec: 2            # 2s antes
  padding_after_sec: 2             # 2s depois
```

### 4. Adicione seus vídeos

Coloque os vídeos na pasta `videos_input/`:
```
videos_input/
├── modulo_01.mp4
├── modulo_02.mp4
└── curso_completo.mp4
```

### 5. Execute

```bash
python main.py
```

O programa vai:
1. ✅ Validar FFmpeg
2. 📋 Listar vídeos disponíveis
3. 🎯 Permitir escolher qual processar
4. 📊 Mostrar progresso em tempo real
5. 💾 Salvar aulas em `lessons_output/`

## ⚙️ Configuração Avançada

### Ajustar Sensibilidade de Silêncio

Se o programa não está detectando os silêncios corretamente:

- **Detectando silêncios demais**: Aumente `silence_thresh_offset_db` (ex: 35)
- **Não detectando silêncios**: Diminua `silence_thresh_offset_db` (ex: 20)
- **Silêncios muito curtos**: Aumente `min_silence_len_ms` (ex: 15000)

### Logging

Para debug, ative logs em arquivo no `config.yaml`:

```yaml
logging:
  level: "DEBUG"
  save_to_file: true
  log_file: "video_splitter.log"
```

## 📊 Exemplo de Saída

```
==== Video Lesson Splitter ====

✓ Configuration loaded from config.yaml
✓ FFmpeg and FFprobe are installed

Available videos:
  [1] Go Expert part1.mp4
  [2] Python Course.mp4

Type the number of the video you want to process: 1

Selected video: Go Expert part1.mp4

Output directory: lessons_output/Go Expert part1
=== Processing video: Go Expert part1.mp4 ===
Getting video info...
Video duration: 07:27:16
Extracting audio with FFmpeg...
Extracting audio: 100%|████████████████| 100/100 [01:23<00:00,  1.20%/s]
✓ Audio extracted

Loading audio file...
Audio duration: 26836.0s
Analyzing audio (threshold: -42.3 dBFS)...
Detecting silences: 100%|████████████| 448/448 [02:15<00:00,  3.31chunk/s]

Silences detected:
  00:15:42 -> 00:15:54
  00:32:18 -> 00:32:31
  ...

Generating lesson files...
Cutting videos: 100%|████████████████| 25/25 [00:45<00:00,  1.80s/lesson]

Summary of generated lessons:
  Lesson 01: 00:00:00 -> 00:15:42 (942.0s)
  Lesson 02: 00:15:54 -> 00:32:18 (984.0s)
  ...

✓ Processing completed successfully!
```

## 🐛 Troubleshooting

### Erro: "FFmpeg not found"
- Instale o FFmpeg conforme instruções acima
- Verifique se está no PATH: `ffmpeg -version`

### Erro: "No lessons found"
- Ajuste `silence_thresh_offset_db` no `config.yaml`
- Verifique se o vídeo tem áudio
- Reduza `min_lesson_duration_sec` se as aulas forem curtas

