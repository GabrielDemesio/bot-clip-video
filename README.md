
# Video Lesson Splitter

Pequena ferramenta em Python para dividir um vídeo longo de módulo em **várias aulas**,
usando **intervalos de silêncio** no áudio como pontos de corte.

Arquitetura separada em camadas:
- `app/core`: regras de negócio (detecção de silêncio, split de vídeo, DTOs, config)
- `app/services`: orquestração de módulos (usa o core)
- `app/cli`: interface de linha de comando (menu para escolher o vídeo)
- `main.py`: ponto de entrada

## Requisitos

- Python 3.10+
- `ffmpeg` instalado no sistema
- Dependências Python:

```bash
pip install -r requirements.txt
```

## Estrutura de pastas

```text
video_lesson_splitter/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── dto.py
│   │   ├── silence_detector.py
│   │   ├── utils.py
│   │   └── video_splitter.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── module_processor.py
│   └── cli/
│       ├── __init__.py
│       ├── main.py
│       └── menu.py
├── lessons_output/      # será criada automaticamente
├── videos_input/        # coloque seus vídeos aqui
├── main.py
├── requirements.txt
└── README.md
```

## Como usar

1. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate   # Windows
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Garanta que o `ffmpeg` está instalado (no Linux, por exemplo):

```bash
sudo apt-get install ffmpeg
```

4. Coloque seus vídeos brutos (ex: `modulo_01.mp4`) na pasta:

```text
videos_input/
```

5. Rode o programa:

```bash
python main.py
```
## Observação

- O script espera que o áudio do vídeo tenha volume razoável. Se estiver muito baixo ou muito alto, talvez você precise brincar com `silence_thresh_offset_db` para calibrar o que é considerado silêncio.
- Ele trabalha com um vídeo por vez, escolhido via menu no terminal.
