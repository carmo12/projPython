"""
Partículas 3D controladas pela mão (webcam) - Tema: ESPAÇO
A câmera aparece dentro da própria janela (canto superior esquerdo).

Gestos (palma virada para a câmera, dedos para cima):
    0 dedos (punho)  -> galáxia
    1 dedo           -> planeta com anel
    2 dedos          -> foguete
    3 dedos          -> estrela
    4 dedos          -> buraco negro
    5 dedos          -> texto "UNIVERSO"
    Pinça (polegar + indicador) -> aumenta / diminui
    Mover a mão para os lados   -> gira
    ESC                         -> sair
"""
import cv2
import numpy as np
import mediapipe as mp
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, FULLSCREEN, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

N = 12000            # quantidade de partículas
TELA_CHEIA = True    # False = janela normal
W, H = 1200, 700     # tamanho usado só se TELA_CHEIA = False
CAM_W, CAM_H = 400, 300   # tamanho da câmera dentro da janela
CAM_MARGEM = 20           # distância da câmera até a borda


# ----------------------------------------------------------------------
# FORMAS (cada função devolve N pontos 3D)
# ----------------------------------------------------------------------
def tilt_x(p, deg):
    """Inclina a forma para ela não ficar 'de lado' (vista como uma linha)."""
    a = np.radians(deg)
    rot = np.array([[1, 0, 0],
                    [0, np.cos(a), -np.sin(a)],
                    [0, np.sin(a), np.cos(a)]])
    return p @ rot.T


def normalize(p, size):
    """Centraliza a forma e ajusta o tamanho para caber na tela."""
    p = p - (p.min(0) + p.max(0)) / 2
    return p * (size / np.abs(p).max())


def sphere(n, r=1.0):
    p = np.random.randn(n, 3)
    p /= np.linalg.norm(p, axis=1, keepdims=True)
    return p * r


def planet(n):
    """Planeta com anel (tipo Saturno)."""
    n1 = int(n * 0.55)
    body = sphere(n1, 0.55)
    a = np.random.rand(n - n1) * 2 * np.pi
    rad = 0.85 + np.random.rand(n - n1) * 0.4
    ring = np.stack([rad * np.cos(a), (np.random.rand(n - n1) - .5) * 0.02,
                     rad * np.sin(a)], 1)
    tilt = np.radians(25)
    rot = np.array([[np.cos(tilt), -np.sin(tilt), 0],
                    [np.sin(tilt), np.cos(tilt), 0], [0, 0, 1]])
    return np.vstack([body, ring]) @ rot.T


def galaxy(n):
    arms = 3
    i = np.random.randint(0, arms, n)
    d = np.random.rand(n) ** 0.6 * 1.6
    ang = d * 3 + i * 2 * np.pi / arms + np.random.randn(n) * 0.15
    return np.stack([d * np.cos(ang), np.random.randn(n) * 0.05,
                     d * np.sin(ang)], 1)


def rocket(n):
    n1, n2, n3 = int(n * .45), int(n * .2), int(n * .15)
    n4 = n - n1 - n2 - n3
    # corpo
    a = np.random.rand(n1) * 2 * np.pi
    y = np.random.rand(n1) * 1.0 - .6
    body = np.stack([.25 * np.cos(a), y, .25 * np.sin(a)], 1)
    # ponta
    t = np.random.rand(n2)
    a = np.random.rand(n2) * 2 * np.pi
    r = .25 * (1 - t)
    cone = np.stack([r * np.cos(a), .4 + t * .6, r * np.sin(a)], 1)
    # aletas
    s, t = np.random.rand(n3), np.random.rand(n3)
    sign = np.random.choice([-1, 1], n3)
    fins = np.stack([sign * (.25 + .3 * s), -.6 + .4 * t * (1 - s),
                     np.zeros(n3)], 1)
    half = n3 // 2
    fins[half:, [0, 2]] = fins[half:, [2, 0]]
    # chama
    t = np.random.rand(n4)
    a = np.random.rand(n4) * 2 * np.pi
    r = .18 * (1 - t) * np.random.rand(n4)
    flame = np.stack([r * np.cos(a), -.6 - t * .6, r * np.sin(a)], 1)
    return np.vstack([body, cone, fins, flame])


def star(n):
    ang = np.arange(10) * np.pi / 5 + np.pi / 2
    rad = np.where(np.arange(10) % 2 == 0, 1.0, .42)
    v = np.stack([rad * np.cos(ang), rad * np.sin(ang)], 1)
    i = np.random.randint(0, 10, n)
    a, b = v[i], v[(i + 1) % 10]
    r1 = np.sqrt(np.random.rand(n))[:, None]
    r2 = np.random.rand(n)[:, None]
    p = r1 * ((1 - r2) * a + r2 * b)
    z = (np.random.rand(n) - .5) * .25
    return np.column_stack([p, z])


def black_hole(n):
    n1 = int(n * .88)
    d = .45 + np.random.rand(n1) ** 1.5 * 1.3
    a = np.random.rand(n1) * 2 * np.pi
    disk = np.stack([d * np.cos(a), np.random.randn(n1) * .02,
                     d * np.sin(a)], 1)
    a2 = np.random.rand(n - n1) * 2 * np.pi
    ring = np.stack([.42 * np.cos(a2), .42 * np.sin(a2),
                     np.random.randn(n - n1) * .01], 1)
    return tilt_x(np.vstack([disk, ring]), 65)


def text_shape(n, txt="UNIVERSO"):
    """Qualquer texto vira nuvem de partículas."""
    img = np.zeros((240, 900), np.uint8)
    cv2.putText(img, txt, (20, 150), cv2.FONT_HERSHEY_DUPLEX, 2.2, 255, 4)
    ys, xs = np.nonzero(img)
    idx = np.random.randint(0, len(xs), n)
    return np.stack([xs[idx], -ys[idx],
                     (np.random.rand(n) - .5) * 8], 1).astype(np.float64)


# ----------------------------------------------------------------------
# TEMA: (nome, função da forma, cor RGB 0-1, tamanho na tela)
# (nomes sem acento, porque o OpenCV não desenha acentos no vídeo)
# ----------------------------------------------------------------------
SHAPES = [
    ("galaxia",      lambda n: tilt_x(galaxy(n), 60),     (0.7, 0.5, 1.0), 1.6),
    ("planeta",      planet,                              (1.0, 0.6, 0.2), 1.5),
    ("foguete",      rocket,                              (0.6, 0.9, 1.0), 1.4),
    ("estrela",      star,                                (1.0, 0.9, 0.3), 1.3),
    ("buraco negro", black_hole,                          (1.0, 0.45, 0.1), 1.6),
    ("texto",        lambda n: text_shape(n, "UNIVERSO"), (0.3, 1.0, 0.9), 2.4),
]
TARGETS = [normalize(s[1](N), s[3]).astype(np.float32) for s in SHAPES]


# ----------------------------------------------------------------------
# RASTREAMENTO DA MÃO
# ----------------------------------------------------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6,
                       min_tracking_confidence=0.5)


def read_gesture(lm):
    """Retorna (dedos_levantados, pinça 0-1, posição_x 0-1)."""
    tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
    fingers = sum(lm[t].y < lm[p].y for t, p in zip(tips, pips))
    # polegar: mais longe do mindinho quando está aberto
    d_tip = np.hypot(lm[4].x - lm[17].x, lm[4].y - lm[17].y)
    d_ip = np.hypot(lm[3].x - lm[17].x, lm[3].y - lm[17].y)
    fingers += int(d_tip > d_ip)
    pinch = np.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y)
    return fingers, float(np.clip(pinch / 0.25, 0, 1)), lm[9].x


# ----------------------------------------------------------------------
# CÂMERA DENTRO DA JANELA (textura OpenGL no canto superior esquerdo)
# ----------------------------------------------------------------------
def criar_textura():
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    return tex


def desenhar_camera(frame, tex, sw, sh):
    small = cv2.resize(frame, (CAM_W, CAM_H))
    rgb = np.ascontiguousarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))

    glBindTexture(GL_TEXTURE_2D, tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, CAM_W, CAM_H, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, rgb)

    # projeção 2D só para o desenho da câmera
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, sw, 0, sh, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    x0, x1 = CAM_MARGEM, CAM_MARGEM + CAM_W
    y1 = sh - CAM_MARGEM
    y0 = y1 - CAM_H

    glEnable(GL_TEXTURE_2D)
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1); glVertex2f(x0, y0)
    glTexCoord2f(1, 1); glVertex2f(x1, y0)
    glTexCoord2f(1, 0); glVertex2f(x1, y1)
    glTexCoord2f(0, 0); glVertex2f(x0, y1)
    glEnd()
    glDisable(GL_TEXTURE_2D)

    # borda
    glColor3f(0.6, 0.8, 1.0)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x0, y0); glVertex2f(x1, y0)
    glVertex2f(x1, y1); glVertex2f(x0, y1)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def main():
    cap = cv2.VideoCapture(0)
    pygame.init()
    if TELA_CHEIA:
        info = pygame.display.Info()
        sw, sh = info.current_w, info.current_h
        pygame.display.set_mode((sw, sh), DOUBLEBUF | OPENGL | FULLSCREEN)
    else:
        sw, sh = W, H
        pygame.display.set_mode((sw, sh), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Partículas controladas pela mão")
    glViewport(0, 0, sw, sh)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, sw / sh, 0.1, 50)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_POINT_SMOOTH)
    glPointSize(2)
    cam_tex = criar_textura()

    pos = np.random.randn(N, 3).astype(np.float32) * 2
    shape_i, scale, rot_y = 0, 1.0, 0.0
    target_scale, target_rot = 1.0, 0.0
    clock = pygame.time.Clock()

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                running = False

        frame = None
        ok, img = cap.read()
        if ok:
            frame = cv2.flip(img, 1)
            res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if res.multi_hand_landmarks:
                hl = res.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)
                fingers, pinch, hx = read_gesture(hl.landmark)
                shape_i = fingers % len(SHAPES)
                target_scale = 0.7 + pinch * 0.6        # zoom de 0.7x a 1.3x
                target_rot = (hx - 0.5) * 120           # gira no máx. +-60 graus
            cv2.putText(frame, SHAPES[shape_i][0], (15, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

        # suaviza e move as partículas até o alvo
        scale += (target_scale - scale) * 0.1
        rot_y += (target_rot - rot_y) * 0.1
        pos += (TARGETS[shape_i] - pos) * 0.07
        pos += np.random.randn(N, 3).astype(np.float32) * 0.004  # "vida"

        glClearColor(0, 0, 0.02, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, -5)
        glRotatef(rot_y, 0, 1, 0)
        glScalef(scale, scale, scale)
        glColor3f(*SHAPES[shape_i][2])
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, pos)
        glDrawArrays(GL_POINTS, 0, N)
        glDisableClientState(GL_VERTEX_ARRAY)

        if frame is not None:
            desenhar_camera(frame, cam_tex, sw, sh)

        pygame.display.flip()
        clock.tick(60)

    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()