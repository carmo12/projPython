# ✋🌌 Partículas 3D controladas pela mão

Sistema de partículas 3D controlado por gestos da mão através da webcam. Com a mão na frente da câmera, você muda a forma formada pelas partículas (galáxia, planeta, foguete, estrela, buraco negro e texto), aumenta, diminui e gira.

Feito com **Python**, **MediaPipe** (rastreamento da mão), **OpenCV** (câmera) e **PyOpenGL + Pygame** (gráficos 3D).

## ✨ Funcionalidades

- Rastreamento de mão em tempo real
- 6 formas 3D feitas de milhares de partículas, com transição suave entre elas
- Câmera exibida dentro da própria janela, com os pontos da mão
- Tela cheia
- Fácil de personalizar: crie suas próprias formas e temas

## 🖐️ Gestos

Deixe a **palma virada para a câmera** e os dedos apontando para cima. A forma é escolhida pelo número de dedos levantados.

| Gesto | Dedos | Forma |
|---|---|---|
| ✊ Punho fechado | 0 | Galáxia |
| ☝️ Só o indicador | 1 | Planeta com anel |
| ✌️ Indicador + médio | 2 | Foguete |
| Indicador + médio + anelar | 3 | Estrela |
| Quatro dedos (sem o polegar) | 4 | Buraco negro |
| 🖐️ Mão toda aberta | 5 | Texto "UNIVERSO" |

**Controles extras**

- 🤏 **Pinça** (polegar + indicador): diminui ou aumenta a forma
- ↔️ **Mover a mão para os lados**: gira a forma
- **ESC**: sair

> Dica: nos gestos de 1 a 4 dedos, mantenha o polegar dobrado sobre a palma, senão ele conta como mais um dedo.

## 🚀 Como rodar

### Requisitos

- **Python 3.10, 3.11 ou 3.12** (o MediaPipe pode não funcionar em versões mais novas)
- Uma webcam

### Instalação

```bash
# 1. Clone o repositório
   git clone https://github.com/carmo12/projPython.git
   cd projPython

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash)
# venv\Scripts\activate           # Windows (CMD / PowerShell)
# source venv/bin/activate        # Mac / Linux

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode
python particulas_mao.py
```

## 🎨 Como personalizar

Abra o `particulas_mao.py` e edite a lista `SHAPES`. Cada item tem o formato:

```python
("nome", função_da_forma, (R, G, B), tamanho)
```

- **Nova forma:** crie uma função que receba `n` e devolva `n` pontos 3D (um array `n x 3`) e adicione na lista.
- **Texto:** troque `"UNIVERSO"` por qualquer palavra na função `text_shape`.
- **Cores:** valores de 0 a 1 em RGB.
- **Tamanho na tela:** o último número de cada item.

Outras configurações no começo do arquivo:

| Variável | O que faz |
|---|---|
| `N` | Quantidade de partículas (diminua se estiver lento) |
| `TELA_CHEIA` | `True` para tela cheia, `False` para janela |
| `CAM_W`, `CAM_H` | Tamanho da câmera dentro da janela |

## 🛠️ Problemas comuns

| Problema | Solução |
|---|---|
| `module 'mediapipe' has no attribute 'solutions'` | `pip install mediapipe==0.10.14` |
| Erro ao instalar o `mediapipe` | Use Python 3.10, 3.11 ou 3.12 |
| Câmera preta ou não abre | Feche apps que usam a webcam (Zoom, Meet, Teams). Se tiver mais de uma câmera, troque `VideoCapture(0)` por `VideoCapture(1)` |
| Lento | Diminua o valor de `N` |
| Forma não troca | Mantenha a palma para a câmera, com boa iluminação, e o polegar dobrado |

## 📦 Tecnologias

- [Python](https://www.python.org/)
- [MediaPipe](https://developers.google.com/mediapipe)
- [OpenCV](https://opencv.org/)
- [Pygame](https://www.pygame.org/)
- [PyOpenGL](https://pyopengl.sourceforge.net/)
- [NumPy](https://numpy.org/)

## 📄 Licença

Projeto livre para estudo e experimentação.