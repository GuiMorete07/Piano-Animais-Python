import math
import array
import os
from abc import ABC, abstractmethod
import pygame

# ---------------------------------------------------------
# CONSTANTES DE CONFIGURAÇÃO DO ECRÃ E ÁUDIO
# ---------------------------------------------------------
LARGURA_ECRA = 950 
ALTURA_ECRA = 600
TAXA_AMOSTRAGEM = 44100

# Novas Cores: Azul e Prata
COR_FUNDO = (15, 35, 80)        # Azul Escuro Elegante
COR_CARCACA = (192, 192, 192)   # Prata
COR_BORDAS = (140, 140, 140)    # Prata mais escuro para sombreamento
COR_TEXTO = (40, 40, 40)
COR_PAINEL = (240, 248, 255)    # Azul muito claro (Alice Blue)
COR_TECLA_BRANCA = (250, 250, 250)
COR_TECLA_PRETA = (30, 30, 30)
COR_TECLA_PRESSIONADA = (100, 149, 237) # Cornflower Blue para o clique

# Frequências das notas musicais em Hertz (Hz)
NOTAS = {
    "Dó": 261.63, "Ré": 293.66, "Mi": 329.63, "Fá": 349.23,
    "Sol": 392.00, "Lá": 440.00, "Si": 493.88,
    "Dó#": 277.18, "Ré#": 311.13, "Fá#": 369.99, "Sol#": 415.30, "Lá#": 466.16
}

# =========================================================
# CLASSES DE SOM
# =========================================================
class EmissorDeSom(ABC):
    def __init__(self, nome: str, nota_informativa: str):
        self._nome = nome
        self._nota_informativa = nota_informativa

    @property
    def nome(self) -> str: return self._nome
    
    @property
    def nota_informativa(self) -> str: return self._nota_informativa

    @abstractmethod
    def emitir_som(self, frequencia: float): pass

class SomAnimal(EmissorDeSom):
    def __init__(self, nome: str, nota_informativa: str, caminho_audio: str, freq_base: float = 261.63):
        super().__init__(nome, nota_informativa)
        self._som_base = None
        self._sons_notas = {}

        if caminho_audio and os.path.exists(caminho_audio):
            try:
                self._som_base = pygame.mixer.Sound(caminho_audio)
                self._sintonizar_notas(freq_base)
            except Exception as e:
                print(f"Aviso: Não foi possível carregar {caminho_audio}: {e}")

    def _sintonizar_notas(self, freq_base: float):
        if not self._som_base: return

        raw_bytes = self._som_base.get_raw()
        frame_size = 4
        num_frames = len(raw_bytes) // frame_size

        if num_frames == 0: return

        frequencias_alvo = list(NOTAS.values()) + [NOTAS["Dó"] * 2]

        for freq_nota in frequencias_alvo:
            r = freq_nota / freq_base
            novo_num_frames = int(num_frames / r)

            if novo_num_frames <= 0: continue

            out_bytes = bytearray(novo_num_frames * frame_size)
            for j in range(novo_num_frames):
                orig_frame = int(j * r)
                if orig_frame >= num_frames: break
                src_idx = orig_frame * frame_size
                dst_idx = j * frame_size
                out_bytes[dst_idx:dst_idx + frame_size] = raw_bytes[src_idx:src_idx + frame_size]

            self._sons_notas[freq_nota] = pygame.mixer.Sound(buffer=out_bytes)

    def emitir_som(self, frequencia: float):
        if not self._sons_notas:
            if self._som_base:
                self._som_base.stop()
                self._som_base.play()
            return

        freq_proxima = min(self._sons_notas.keys(), key=lambda f: abs(f - frequencia))
        som_nota = self._sons_notas[freq_proxima]
        som_nota.stop()
        som_nota.play()

class SomPiano(EmissorDeSom):
    def __init__(self):
        super().__init__("Piano Clássico", "Som tradicional para você afinar os ouvidos.")
    def emitir_som(self, frequencia: float):
        n_amostras = int(TAXA_AMOSTRAGEM * 0.6)
        buf = array.array('h')
        amplitude = 12000
        for i in range(n_amostras):
            t = i / TAXA_AMOSTRAGEM
            envelope = max(0.0, 1.0 - (i / n_amostras))
            v = int(amplitude * envelope * math.sin(2 * math.pi * frequencia * t))
            buf.append(v)
            buf.append(v)
        som = pygame.mixer.Sound(buffer=buf)
        som.play()

# Classes dos 7 Animais
class SomGato(SomAnimal):
    def __init__(self): super().__init__("Gato", "Miau em Dó, Ré, Mi...", "sons/gato.mp3", NOTAS["Dó"])
class SomVaca(SomAnimal):
    def __init__(self): super().__init__("Vaca", "Muuu sintonizado!", "sons/vaca.mp3", NOTAS["Dó"])
class SomCachorro(SomAnimal):
    def __init__(self): super().__init__("Cachorro", "Au Au afinado!", "sons/cachorro.mp3", NOTAS["Dó"])
class SomGalinha(SomAnimal):
    def __init__(self): super().__init__("Galinha", "Cocoricó musical!", "sons/galinha.mp3", NOTAS["Dó"])
class SomSapo(SomAnimal):
    def __init__(self): super().__init__("Sapo", "Ribbit no ritmo certo!", "sons/sapo.mp3", NOTAS["Dó"])
class SomPato(SomAnimal):
    def __init__(self): super().__init__("Pato", "Quack afinado!", "sons/pato.mp3", NOTAS["Dó"])
class SomCobra(SomAnimal):
    def __init__(self): super().__init__("Cobra", "Ssssibilar musical!", "sons/cobra.mp3", NOTAS["Dó"])

# =========================================================
# INTERFACE GRÁFICA
# =========================================================
class ElementoGUI(ABC):
    def __init__(self, x: int, y: int, largura: int, altura: int):
        self._rect = pygame.Rect(x, y, largura, altura)
        self._pressionado = False

    @abstractmethod
    def desenhar(self, ecra: pygame.Surface): pass
    @abstractmethod
    def tratar_clique(self, pos: tuple) -> bool: pass

class Tecla(ElementoGUI):
    def __init__(self, x, y, largura, altura, nome_nota, frequencia, eh_preta=False):
        super().__init__(x, y, largura, altura)
        self.nome_nota, self.frequencia, self._eh_preta = nome_nota, frequencia, eh_preta

    def desenhar(self, ecra):
        cor = COR_TECLA_PRESSIONADA if self._pressionado else (COR_TECLA_PRETA if self._eh_preta else COR_TECLA_BRANCA)
        pygame.draw.rect(ecra, cor, self._rect, border_radius=4)
        pygame.draw.rect(ecra, (100, 100, 100), self._rect, 2, border_radius=4)
        fonte = pygame.font.SysFont("Arial", 12, bold=True)
        cor_texto = (255, 255, 255) if self._eh_preta and not self._pressionado else (30, 30, 30)
        txt = fonte.render(self.nome_nota, True, cor_texto)
        ecra.blit(txt, txt.get_rect(center=(self._rect.centerx, self._rect.bottom - 20)))

    def tratar_clique(self, pos):
        if self._rect.collidepoint(pos):
            self._pressionado = True
            return True
        return False
    
    def soltar(self): self._pressionado = False

class BotaoAnimal(ElementoGUI):
    def __init__(self, x, y, largura, altura, emissor, cor):
        super().__init__(x, y, largura, altura)
        self.emissor, self._cor = emissor, cor

    def desenhar(self, ecra):
        espessura_borda = 4 if self._pressionado else 1
        pygame.draw.ellipse(ecra, self._cor, self._rect)
        pygame.draw.ellipse(ecra, (50, 50, 50), self._rect, espessura_borda)
        txt = pygame.font.SysFont("Arial", 13, bold=True).render(self.emissor.nome, True, (255, 255, 255))
        ecra.blit(txt, txt.get_rect(center=self._rect.center))

    def tratar_clique(self, pos): return self._rect.collidepoint(pos)
    def set_ativo(self, ativo): self._pressionado = ativo

class PianinhoApp:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=TAXA_AMOSTRAGEM, size=-16, channels=2)
        self._ecra = pygame.display.set_mode((LARGURA_ECRA, ALTURA_ECRA))
        pygame.display.set_caption("Piano dos Animais - Prata e Azul")
        self._relogio = pygame.time.Clock()
        self._rodando = True
        self._emissor_atual = SomPiano()
        self._botoes_animais = []
        self._teclas = []
        self._inicializar_componentes()

    def _inicializar_componentes(self):
        # Botões (Piano + 7 Animais) - Espaçamento ajustado
        btn_piano = BotaoAnimal(30, 50, 95, 60, SomPiano(), (10, 30, 80))
        btn_piano.set_ativo(True)
        self._botoes_animais.append(btn_piano)

        animais = [
            (SomVaca(), (150, 50, 50)), (SomGato(), (150, 100, 150)),
            (SomGalinha(), (200, 120, 50)), (SomCachorro(), (80, 140, 80)),
            (SomSapo(), (50, 180, 50)), (SomPato(), (200, 180, 30)),
            (SomCobra(), (60, 120, 90))
        ]

        x_inicio = 140
        for emissor, cor in animais:
            self._botoes_animais.append(BotaoAnimal(x_inicio, 50, 95, 60, emissor, cor))
            x_inicio += 110 # Espaçamento dinâmico para caber os 8 botões

        # Teclas Brancas
        teclas_brancas_info = [
            ("Dó", NOTAS["Dó"]), ("Ré", NOTAS["Ré"]), ("Mi", NOTAS["Mi"]),
            ("Fá", NOTAS["Fá"]), ("Sol", NOTAS["Sol"]), ("Lá", NOTAS["Lá"]),
            ("Si", NOTAS["Si"]), ("Dó (2)", NOTAS["Dó"] * 2)
        ]
        
        largura_tb, altura_tb, y_teclas, x_base = 75, 220, 160, 175
        for i, (nome, freq) in enumerate(teclas_brancas_info):
            self._teclas.append(Tecla(x_base + (i * largura_tb), y_teclas, largura_tb - 4, altura_tb, nome, freq, False))

        # Teclas Pretas
        teclas_pretas_info = [(0, "Dó#", NOTAS["Dó#"]), (1, "Ré#", NOTAS["Ré#"]), (3, "Fá#", NOTAS["Fá#"]), (4, "Sol#", NOTAS["Sol#"]), (5, "Lá#", NOTAS["Lá#"])]
        largura_tp, altura_tp = 45, 130
        for idx, nome, freq in teclas_pretas_info:
            x = x_base + (idx * largura_tb) + (largura_tb - (largura_tp // 2)) - 2
            self._teclas.append(Tecla(x, y_teclas, largura_tp, altura_tp, nome, freq, True))

    def _tratar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: self._rodando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos = evento.pos
                for btn in self._botoes_animais:
                    if btn.tratar_clique(pos):
                        self._emissor_atual = btn.emissor
                        for b in self._botoes_animais: b.set_ativo(b == btn)
                        break

                for tecla in sorted(self._teclas, key=lambda t: t._eh_preta, reverse=True):
                    if tecla.tratar_clique(pos):
                        self._emissor_atual.emitir_som(tecla.frequencia)
                        break
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                for tecla in self._teclas: tecla.soltar()

    def _desenhar_interface(self):
        self._ecra.fill(COR_FUNDO)
        rect_carcaca = pygame.Rect(30, 20, LARGURA_ECRA - 60, ALTURA_ECRA - 40)
        pygame.draw.rect(self._ecra, COR_CARCACA, rect_carcaca, border_radius=30)
        pygame.draw.rect(self._ecra, COR_BORDAS, rect_carcaca, 5, border_radius=30) 

        for btn in self._botoes_animais: btn.desenhar(self._ecra)
        for tecla in self._teclas: 
            if not tecla._eh_preta: tecla.desenhar(self._ecra)
        for tecla in self._teclas:
            if tecla._eh_preta: tecla.desenhar(self._ecra)

        rect_painel = pygame.Rect(80, 420, LARGURA_ECRA - 160, 120)
        pygame.draw.rect(self._ecra, COR_PAINEL, rect_painel, border_radius=15)
        pygame.draw.rect(self._ecra, (180, 180, 180), rect_painel, 3, border_radius=15)

        txt_titulo = pygame.font.SysFont("Arial", 18, bold=True).render(f"Modo Selecionado: {self._emissor_atual.nome}", True, (50, 50, 150))
        txt_info = pygame.font.SysFont("Arial", 16).render(self._emissor_atual.nota_informativa, True, COR_TEXTO)
        self._ecra.blit(txt_titulo, (rect_painel.x + 20, rect_painel.y + 25))
        self._ecra.blit(txt_info, (rect_painel.x + 20, rect_painel.y + 65))
        
        pygame.display.flip()

    def executar(self):
        while self._rodando:
            self._tratar_eventos()
            self._desenhar_interface()
            self._relogio.tick(60)
        pygame.quit()

if __name__ == "__main__":
    PianinhoApp().executar()