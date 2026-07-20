# -*- coding: utf-8 -*-
"""Gera o icone do carrinho de mercado (azul) -> icone_carrinho.ico / .png
Estilo inspirado na imagem: carrinho branco sobre fundo azul com leve gradiente.
"""
from PIL import Image, ImageDraw, ImageFilter

S = 512  # canvas de alta resolucao (com supersampling)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fundo(img):
    """Fundo azul com gradiente vertical e cantos arredondados + borda."""
    top = (74, 116, 176)      # azul mais claro em cima
    bot = (34, 74, 134)       # azul mais escuro embaixo
    grad = Image.new("RGB", (1, S))
    for y in range(S):
        grad.putpixel((0, y), _lerp(top, bot, y / (S - 1)))
    grad = grad.resize((S, S))

    # mascara com cantos arredondados
    radius = 40
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([4, 4, S - 5, S - 5], radius=radius, fill=255)

    img.paste(grad, (0, 0), mask)

    # borda escura fina
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, S - 5, S - 5], radius=radius,
                        outline=(18, 38, 74), width=6)


def thick_polyline(draw, pts, width, fill):
    """Desenha uma polilinha grossa com juntas/pontas arredondadas."""
    r = width // 2
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=fill, width=width)
    for (x, y) in pts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def desenhar_carrinho(draw, cor, dx=0, dy=0):
    w = 34  # espessura do traco

    def P(pts):
        return [(x + dx, y + dy) for (x, y) in pts]

    # Cabo (hook) + trilho superior da cesta
    frame = P([(60, 152), (60, 120), (88, 120), (120, 160), (446, 160)])
    thick_polyline(draw, frame, w, cor)

    # Contorno da cesta (trapezio, oco)
    cesta = P([(120, 160), (446, 160), (404, 306), (182, 306), (120, 160)])
    thick_polyline(draw, cesta, w, cor)

    # Pernas ate as rodas
    thick_polyline(draw, P([(220, 306), (220, 336)]), w - 6, cor)
    thick_polyline(draw, P([(372, 306), (372, 336)]), w - 6, cor)

    # Rodas (circulos cheios)
    for cx, cy in P([(218, 366), (372, 366)]):
        rr = 36
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=cor)


def main():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fundo(img)

    # Sombra suave do carrinho
    sombra = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sombra)
    desenhar_carrinho(sd, (10, 26, 55, 150), dx=7, dy=9)
    sombra = sombra.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img, sombra)

    # Carrinho branco
    d = ImageDraw.Draw(img)
    desenhar_carrinho(d, (250, 250, 252, 255))

    # Salva PNG grande
    img.save("icone_carrinho.png")

    # Gera ICO multi-tamanho (downscale com anti-aliasing)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    frames[-1].save("icone_carrinho.ico", format="ICO",
                    sizes=[(s, s) for s in sizes])
    print("Gerado: icone_carrinho.ico e icone_carrinho.png")


if __name__ == "__main__":
    main()
