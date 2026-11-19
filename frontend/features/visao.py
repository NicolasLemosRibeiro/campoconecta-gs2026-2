"""Interface do módulo de triagem visual."""
from io import BytesIO

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

from providers import api_client
from ui.mensagens import mostrar_erro


def desenhar(imagem, caixas):
    desenho = ImageDraw.Draw(imagem)
    escala = max(1, round(imagem.width / 360))
    fonte = ImageFont.load_default(size=12 * escala)
    for caixa in caixas:
        x, y = int(caixa["x"]), int(caixa["y"])
        largura, altura = int(caixa["largura"]), int(caixa["altura"])
        legenda = f'Buraco {caixa["confianca"]:.0%}'
        desenho.rectangle((x, y, x + largura, y + altura), outline="#35f2b1", width=2 * escala)
        topo = max(0, y - 19 * escala)
        texto_largura = int(desenho.textlength(legenda, font=fonte)) + 8 * escala
        esquerda = min(x, max(0, imagem.width - texto_largura))
        desenho.rectangle((esquerda, topo, esquerda + texto_largura, topo + 17 * escala), fill="#12362d")
        desenho.text((esquerda + 3 * escala, topo + 1), legenda, fill="white", font=fonte)
    return imagem


def tela():
    st.subheader("Análise de pavimentação")
    st.caption("Triagem de possíveis buracos. A decisão de vistoria cabe à equipe responsável.")
    with st.form("visao_form"):
        arquivo = st.file_uploader("Imagem da via (JPG ou PNG, até 12 MB)", type=["jpg", "jpeg", "png"])
        enviar = st.form_submit_button("Analisar imagem", type="primary")
    if not enviar:
        return
    if arquivo is None:
        st.warning("Selecione uma imagem para análise.")
        return
    conteudo = arquivo.getvalue()
    if len(conteudo) > 12 * 1024 * 1024:
        st.warning("A imagem ultrapassa o limite de 12 MB.")
        return
    try:
        with st.spinner("Analisando a imagem..."):
            resultado = api_client.analisar_imagem(arquivo.name, conteudo, arquivo.type)
        if not resultado["disponivel"]:
            st.warning(resultado.get("mensagem") or "A análise está indisponível.")
            return
        with Image.open(BytesIO(conteudo)) as origem:
            imagem = ImageOps.exif_transpose(origem).convert("RGB")
        caixas = resultado["caixas"]
        st.image(desenhar(imagem, caixas), caption="Resultado da triagem visual")
        st.write(resultado["mensagem"])
        st.caption(f'{len(caixas)} sinalização(ões) · {resultado["latencia_ms"]:.0f} ms na API')
        if caixas:
            st.table([{"Dano": c["classe"], "Confiança do modelo": f'{c["confianca"]:.1%}'} for c in caixas])
    except Exception as erro:
        mostrar_erro(erro)
