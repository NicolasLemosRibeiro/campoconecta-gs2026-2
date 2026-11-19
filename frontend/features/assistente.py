"""Conversa com a Defesa Civil no mesmo aplicativo dos relatos rurais."""
import streamlit as st

from providers import api_client
from ui.mensagens import mostrar_erro

ESTADO = "conversa_defesa_civil"
MODOS = {
    "llm": "Fonte selecionada por IA local",
    "extrativo": "Fonte selecionada por busca",
    "emergencia": "Orientação imediata",
}


def _limpar_conversa() -> None:
    st.session_state.pop(ESTADO, None)


@st.fragment
def tela() -> None:
    st.subheader("Orientações sobre chuvas e alagamentos")
    st.caption("Consulte orientações da Defesa Civil antes, durante e depois de uma enchente. "
               "Para informações atualizadas, consulte os canais oficiais do seu município.")
    st.warning("Risco imediato ou necessidade de resgate? Ligue 193 (Bombeiros). Defesa Civil 199.",
               icon="⚠️")
    st.caption("Evite informar nome, documentos, telefone ou endereço. A conversa fica nesta sessão.")
    st.button("Limpar conversa", key="limpar_defesa_civil", on_click=_limpar_conversa)
    turnos = st.session_state.setdefault(ESTADO, [])
    mensagens = st.container()
    pergunta = st.chat_input("Digite sua pergunta sobre chuvas e enchentes", key="pergunta_defesa_civil",
                             max_chars=500)
    if pergunta is not None:
        pergunta = pergunta.strip()
        if len(pergunta) < 3:
            st.info("Digite pelo menos 3 caracteres.")
        else:
            historico = [{"role": "user", "content": t["pergunta_exibida"]} for t in turnos[-4:]]
            try:
                with st.spinner("Consultando as orientações…"):
                    saida = api_client.perguntar(pergunta, historico)
                if saida.get("disponivel"):
                    turnos.append(saida)
                    del turnos[:-12]
                else:
                    st.error("O assistente está indisponível. Tente novamente em instantes.")
            except Exception as erro:
                mostrar_erro(erro)

    with mensagens:
        if not turnos:
            st.caption("Experimente perguntar «Posso passar de carro por uma rua alagada?»")
        for turno in turnos:
            with st.chat_message("user"):
                st.text(turno["pergunta_exibida"])
            with st.chat_message("assistant"):
                st.write(turno["resposta"])
                if turno.get("abstencao"):
                    st.caption("Orientação específica indisponível")
                elif turno.get("modo") in MODOS:
                    st.caption(MODOS[turno["modo"]])
                for fonte in turno.get("fontes", []):
                    with st.expander(f"Fonte · {fonte['titulo']}"):
                        st.caption(f"{fonte['secao']} · Consultado em {fonte['consultado_em']}")
                        st.write(fonte["trecho"])
                        st.link_button("Abrir fonte oficial", fonte["url"])
