import os
import cv2
import yt_dlp
import matplotlib.pyplot as plt
import time
import csv

# =====================================================================
# FUNÇÕES AUXILIARES DO PIPELINE
# =====================================================================

def normalizar_url_youtube(url):
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    if "watch?v=" in url:
        video_id = url.split("watch?v=")[1].split("&")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def obter_stream_youtube(url):
    url = normalizar_url_youtube(url)
    ydl_opts = {
        "quiet": True,
        # Otimização: força uma resolução menor (ex: até 480p) para economizar banda e processamento
        "format": "worst[ext=mp4]/best[height<=480]",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "tv_embedded"]
            }
        },
        "geo_bypass": True,
    }

    try:
        print(f"\nObtendo stream: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        stream_url = info["url"]
        print("-> Stream obtido com sucesso!")
        return stream_url
    except Exception as e:
        print(f"Erro ao obter stream: {e}")
        return None


def classificar_nivel_estimulo(lista_similaridades, intervalo_segundos):
    if not lista_similaridades:
        return "Indefinido", 0, 0

    media_similaridade = sum(lista_similaridades) / len(lista_similaridades)
    limiar_corte = 0.60
    total_cortes = sum(1 for sim in lista_similaridades if sim < limiar_corte)

    tempo_total_segundos = len(lista_similaridades) * intervalo_segundos
    tempo_total_minutos = tempo_total_segundos / 60
    if tempo_total_minutos == 0:
        tempo_total_minutos = 1 / 60

    cortes_por_minuto = total_cortes / tempo_total_minutos

    if cortes_por_minuto > 18 or media_similaridade < 0.75:
        classificacao = "HIPERESTIMULANTE"
    elif cortes_por_minuto < 4 and media_similaridade > 0.94:
        classificacao = "BAIXO ESTÍMULO"
    else:
        classificacao = "ESTÍMULO MODERADO"

    return classificacao, media_similaridade, cortes_por_minuto


def gerar_histogramas(stream_url, intervalo_segundos=5, pasta_saida="histogramas", salvar_graficos=False):
    if stream_url is None:
        print("Nenhum stream válido.")
        return None

    if salvar_graficos:
        os.makedirs(pasta_saida, exist_ok=True)

    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("Erro ao abrir vídeo.")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 24

    frame_intervalo = max(1, int(fps * intervalo_segundos))
    hist_count = 0
    valores_similaridade = []
    hists_anteriores = None

    print(f"Iniciando análise do stream ({fps:.2f} FPS)")

    while True:
        # OTIMIZAÇÃO: Avança o cursor do vídeo para o próximo frame de interesse pulando a leitura lenta
        cap.set(cv2.CAP_PROP_POS_FRAMES, hist_count * frame_intervalo)

        ret, frame = cap.read()
        if not ret:
            break

        if hist_count >= 240:
            print(f"-> Limite de 240 histogramas atingido.")
            break

        if frame is None or frame.size == 0:
            hist_count += 1
            continue

        # OTIMIZAÇÃO: Redimensiona para acelerar o cálculo do histograma
        frame_pequeno = cv2.resize(frame, (320, 240))
        frame_rgb = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

        hists_atuais = {}
        correlacoes_canais = []

        for i, cor in enumerate(["red", "green", "blue"]):
            hist = cv2.calcHist([frame_rgb], [i], None, [256], [0, 256])
            cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
            hists_atuais[cor] = hist

            if hists_anteriores is not None:
                correlacao = cv2.compareHist(hists_anteriores[cor], hist, cv2.HISTCMP_CORREL)
                correlacoes_canais.append(correlacao)

        if correlacoes_canais:
            similaridade_final = sum(correlacoes_canais) / len(correlacoes_canais)
            valores_similaridade.append(similaridade_final)

        # OTIMIZAÇÃO: Condiciona a lentidão do matplotlib apenas se explicitamente solicitado
        if salvar_graficos:
            plt.figure(figsize=(14, 6))
            plt.subplot(1, 2, 1)
            plt.imshow(frame_rgb)
            plt.axis("off")

            plt.subplot(1, 2, 2)
            for cor in ["red", "green", "blue"]:
                plt.plot(hists_atuais[cor], color=cor)
            plt.xlim([0, 256])

            nome_saida = os.path.join(pasta_saida, f"histograma_{hist_count:03d}.png")
            plt.tight_layout()
            plt.savefig(nome_saida, dpi=150)
            plt.close()

        hists_anteriores = hists_atuais
        hist_count += 1

    cap.release()

    classificacao, media_sim, cortes_min = classificar_nivel_estimulo(valores_similaridade, intervalo_segundos)

    return {
        "classificacao": classificacao,
        "media_similaridade": media_sim,
        "cortes_por_minuto": cortes_min,
        "total_histogramas": hist_count
    }


# =====================================================================
# CONFIGURAÇÃO DA EXECUÇÃO EM LOTE COM BASE NO CSV
# =====================================================================

caminho_csv = "GuardianANY_dataset.csv"
lista_de_videos = []

try:
    with open(caminho_csv, mode='r', encoding='utf-8') as file:
        leitor_csv = csv.DictReader(file)
        for linha in leitor_csv:
            if linha.get('Link'):
                lista_de_videos.append({
                    "titulo": linha.get('Título', 'Sem Título'),
                    "url": linha.get('Link'),
                    "classificacao_original": linha.get('Classificaçao', 'NÃO INFORMADO').strip().upper()
                })
except Exception as e:
    print(f"Erro ao ler o arquivo CSV: {e}")

intervalo_segundos = 0.5
pasta_raiz_resultados = "resultados_lote"
relatorio_final = {}

print(f"=== INICIANDO PROCESSAMENTO EM LOTE ({len(lista_de_videos)} VÍDEOS DO CSV) ===")

acertos = 0
total_processados = 0

for indice, item in enumerate(lista_de_videos, start=1):
    url = item["url"]
    titulo = item["titulo"]
    class_original = item["classificacao_original"]

    start_time = time.time()
    print(f"\n--------------------------------------------------")
    print(f"PROCESSANDO VÍDEO {indice}/{len(lista_de_videos)}: {titulo}")
    print(f"--------------------------------------------------")

    pasta_video_atual = os.path.join(pasta_raiz_resultados, f"video_{indice}")
    stream = obter_stream_youtube(url)

    if stream:
        # ALTERADO: salvar_graficos definido como False para máxima velocidade
        metricas = gerar_histogramas(
          stream_url=stream,
          intervalo_segundos=intervalo_segundos,
          pasta_saida=pasta_video_atual,
          salvar_graficos=False
        )

        if metricas:
            class_algoritmo = metricas["classificacao"]
            metricas["classificacao_original"] = class_original
            metricas["titulo"] = titulo

            if class_algoritmo == class_original:
                metricas["resultado_comparacao"] = "CORRETO (Bateu com o CSV)"
                acertos += 1
            else:
                metricas["resultado_comparacao"] = "DIVERGENTE"

            relatorio_final[url] = metricas
            total_processados += 1
    else:
        
        relatorio_final[url] = {
            "titulo": titulo,
            "classificacao": "ERRO NO DOWNLOAD",
            "classificacao_original": class_original,
            "media_similaridade": 0,
            "cortes_por_minuto": 0,
            "total_histogramas": 0,
            "resultado_comparacao": "FALHA"
        }

    end_time = time.time()
    print(f"Tempo de processamento para o Vídeo {indice}: {end_time - start_time:.2f} segundos")

# =====================================================================
# IMPRESSÃO DO DASHBOARD / RELATÓRIO FINAL COMPARATIVO
# =====================================================================
print("\n" + "="*80)
print("             RELATÓRIO COMPARATIVO FINAL (CSV vs ALGORITMO)")
print("="*80)
for url, dados in relatorio_final.items():
    print(f"\n> Vídeo: {dados['titulo']}")
    print(f"  [Link]: {url}")
    print(f"  [Classificação Original (CSV)]: {dados['classificacao_original']}")
    print(f"  [Classificação Algoritmo]:      {dados['classificacao']}")
    print(f"  [Status da Comparação]:         {dados['resultado_comparacao']}")
    print(f"  [Média de Sim. Visual]: {dados['media_similaridade']:.4f}")
    print(f"  [Frequência de Cortes]: {dados['cortes_por_minuto']:.2f} cortes/min")
print("="*80)

if total_processados > 0:
    acuracia = (acertos / total_processados) * 100
    print(f"MÉTRICA GLOBAL: O algoritmo acertou {acuracia:.2f}% das classificações do CSV ({acertos}/{total_processados}).")
print("="*80)


import json

lista_exportacao = []

for url, dados in relatorio_final.items():

    lista_exportacao.append({
        "titulo": dados["titulo"],
        "url": url,

        # classificação obtida pelo algoritmo
        "classificacao_algoritmo": dados["classificacao"],

        # classificação existente no CSV
        "classificacao_csv": dados["classificacao_original"],

        # informações extras
        "resultado": dados["resultado_comparacao"],
        "media_similaridade": dados["media_similaridade"],
        "cortes_por_minuto": dados["cortes_por_minuto"],
        "total_histogramas": dados["total_histogramas"]
    })

with open("dataset_front.json", "w", encoding="utf-8") as f:
    json.dump(lista_exportacao, f, ensure_ascii=False, indent=4)

print("\nArquivo dataset_front.json gerado com sucesso!")