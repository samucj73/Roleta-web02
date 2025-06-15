import streamlit as st
import requests
import random
from collections import Counter
from datetime import datetime

def capturar_ultimos_resultados(qtd=250):
    url_base = "https://loteriascaixa-api.herokuapp.com/api/lotofacil/"
    concursos = []
    try:
        resp = requests.get(url_base)
        dados = resp.json()
        ultimo = dados[0] if isinstance(dados, list) else dados
        numero_atual = int(ultimo.get("concurso"))
        dezenas = sorted([int(d) for d in ultimo.get("dezenas")])
        data_concurso = ultimo.get("data")
        concursos.append((numero_atual, data_concurso, dezenas))

        for i in range(1, qtd):
            concurso_numero = numero_atual - i
            resp = requests.get(f"{url_base}{concurso_numero}")
            if resp.status_code == 200:
                data = resp.json()[0] if isinstance(resp.json(), list) else resp.json()
                numero = int(data.get("concurso"))
                dezenas = sorted([int(d) for d in data.get("dezenas")])
                data_concurso = data.get("data")
                concursos.append((numero, data_concurso, dezenas))
            else:
                break
    except Exception as e:
        st.error(f"Erro ao acessar API: {e}")
    return concursos

def calcular_frequencia(concursos):
    todas_dezenas = [dez for _, _, lista in concursos for dez in lista]
    contagem = Counter(todas_dezenas)
    mais = [item[0] for item in contagem.most_common(12)]
    menos = [item[0] for item in contagem.most_common()[-13:]]
    return mais, menos

numeros_primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}

def tem_equilibrio_par_impar(jogo):
    pares = len([n for n in jogo if n % 2 == 0])
    return abs(pares - (len(jogo) - pares)) <= 3

def tem_qtd_primos_aceitavel(jogo):
    return len([n for n in jogo if n in numeros_primos]) >= 3

def evitar_bolas_1_15(jogo):
    return not ({1, 2, 3} <= set(jogo) or {22, 23, 24} <= set(jogo))

def evitar_sequencias_longas(jogo, limite=4):
    count = 1
    for i in range(1, len(jogo)):
        if jogo[i] == jogo[i-1] + 1:
            count += 1
            if count > limite:
                return False
        else:
            count = 1
    return True

def distribuicao_em_linhas_colunas(jogo):
    linhas = set((n - 1) // 5 for n in jogo)
    colunas = set((n - 1) % 5 for n in jogo)
    return len(linhas) >= 4 and len(colunas) >= 4

def evitar_grupos_completos(jogo):
    linhas = [(1,2,3,4,5), (6,7,8,9,10), (11,12,13,14,15), (16,17,18,19,20), (21,22,23,24,25)]
    colunas = [(1,6,11,16,21), (2,7,12,17,22), (3,8,13,18,23), (4,9,14,19,24), (5,10,15,20,25)]
    for grupo in linhas + colunas:
        if all(n in jogo for n in grupo):
            return False
    return True

def usar_dezenas_repetidas(jogo, ultimo_resultado, min_rept=6, max_rept=10):
    qtd = len(set(jogo) & set(ultimo_resultado))
    return min_rept <= qtd <= max_rept

def gerar_jogo_base(mais, menos, qtd_numeros):
    base_pool = list(set(mais + menos))
    if len(base_pool) < qtd_numeros:
        base_pool = list(set(range(1, 26)))
    return sorted(random.sample(base_pool, qtd_numeros))

def gerar_jogos_filtrados(mais, menos, qtd_jogos, qtd_numeros, ultimo_resultado, filtros):
    jogos = []
    tentativas = 0
    while len(jogos) < qtd_jogos and tentativas < 10000:
        jogo = gerar_jogo_base(mais, menos, qtd_numeros)
        if (
            (not filtros["pares_impares"] or tem_equilibrio_par_impar(jogo)) and
            (not filtros["primos"] or tem_qtd_primos_aceitavel(jogo)) and
            (not filtros["bolas_1_15"] or evitar_bolas_1_15(jogo)) and
            (not filtros["sequencias"] or evitar_sequencias_longas(jogo)) and
            (not filtros["distribuicao"] or distribuicao_em_linhas_colunas(jogo)) and
            (not filtros["grupos_completos"] or evitar_grupos_completos(jogo)) and
            (not filtros["repetidos"] or usar_dezenas_repetidas(jogo, ultimo_resultado))
        ):
            jogos.append(jogo)
        tentativas += 1
    return jogos

def conferir_jogos(jogos, resultado_oficial):
    return [(jogo, len(set(jogo) & set(resultado_oficial))) for jogo in jogos]

st.set_page_config(page_title="Gerador Estratégico Lotofácil", layout="centered")

st.title("🔢 Gerador Estratégico de Jogos - Lotofácil")

st.markdown("Este app gera jogos com base em **estratégias estatísticas** e confere com o último resultado da Lotofácil.")

qtd_concursos = st.slider("📊 Quantos concursos deseja analisar?", 10, 250, 150)
qtd_jogos = st.slider("🎰 Quantos cartões deseja gerar?", 1, 50, 10)
qtd_numeros = st.radio("🔢 Quantos números por cartão?", [15, 16, 18], index=0)

st.markdown("### 🧠 Filtros Estratégicos")
filtros = {
    "pares_impares": st.checkbox("✅ Equilíbrio entre pares e ímpares", value=True),
    "primos": st.checkbox("✅ Incluir ao menos 3 números primos", value=True),
    "bolas_1_15": st.checkbox("✅ Evitar padrões nas bolas 1 e 15", value=True),
    "sequencias": st.checkbox("✅ Evitar sequências longas (5+)", value=True),
    "distribuicao": st.checkbox("✅ Distribuição equilibrada em linhas/colunas", value=True),
    "grupos_completos": st.checkbox("✅ Evitar grupos completos (linhas/colunas)", value=True),
    "repetidos": st.checkbox("✅ Incluir 6 a 10 números do último resultado", value=True),
}

if st.button("🎯 Gerar Jogos Estratégicos"):
    with st.spinner("Gerando jogos e consultando API..."):
        concursos = capturar_ultimos_resultados(qtd_concursos)
        if concursos:
            mais, menos = calcular_frequencia(concursos)
            ultimo_resultado = concursos[0][2]
            data_ultimo = concursos[0][1]
            jogos = gerar_jogos_filtrados(mais, menos, qtd_jogos, qtd_numeros, ultimo_resultado, filtros)
            conferidos = conferir_jogos(jogos, ultimo_resultado)

            st.success(f"{len(jogos)} jogos gerados com base em {qtd_concursos} concursos anteriores.")

            for i, (jogo, acertos) in enumerate(conferidos, 1):
                st.markdown(f"**Jogo {i}**: {jogo} — 🎯 **{acertos} acertos**")

            txt_content = "=== JOGOS GERADOS ===\n\n"
            for i, jogo in enumerate(jogos, 1):
                txt_content += f"Jogo {i}: {sorted(jogo)}\n"
            txt_content += f"\n=== Conferência ===\nResultado oficial {data_ultimo}: {ultimo_resultado}\n"
            for i, (_, acertos) in enumerate(conferidos, 1):
                txt_content += f"Jogo {i}: {acertos} acertos\n"
            txt_content += f"\n=== Rodapé ===\nSistema automatizado baseado em estatísticas reais da Lotofácil.\n"
            txt_content += f"Geração em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"

            st.download_button(
                label="📥 Baixar jogos em .TXT",
                data=txt_content,
                file_name="jogos_lotofacil.txt",
                mime="text/plain"
            )
        else:
            st.error("Não foi possível acessar os resultados da API.")
