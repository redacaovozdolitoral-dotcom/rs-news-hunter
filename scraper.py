import requests
import feedparser # Biblioteca leve para RSS
import newspaper
from newspaper import Config
from datetime import datetime
import os
import gc
import random

# --- GRUPO 1: SITES COM RSS (PREFERÊNCIA TOTAL - LEVE) ---
# Coloque aqui todos que tem /feed/. O processamento é instantâneo.
RSS_FEEDS = {
    "https://www.f1mania.net/feed/": "Fórmula 1",
    "https://www.autoracing.com.br/feed/": "Fórmula 1",
    "https://www.grandepremio.com.br/feed/": "Fórmula 1",
    "https://nautica.com.br/feed/": "Náutica",
    "https://perfilnautico.com.br/feed/": "Náutica",
    "https://www.tuasaude.com/feed/": "Saúde",
    "https://ge.globo.com/rss/ge/futebol/times/palmeiras.xml": "Esporte", # Exemplo RSS GE
    "https://www.gazetaesportiva.com/feed/": "Esporte",
    "https://www.tamoiosnews.com.br/feed/": "Regional",
    "https://novaimprensa.com/feed/": "Regional",
    "https://www.litoralnoticias.com.br/feed/": "Regional",
    "https://costanorte.com.br/feed/": "Regional",
    "https://litoralnorteweb.com.br/feed/": "Regional"
}

# --- GRUPO 2: SITES SEM RSS (PESADO - USE POUCOS) ---
# Só coloque aqui quem NÃO tem feed de jeito nenhum.
SITES_SEM_FEED = {
    "https://radarlitoral.com.br": "Regional",
    # "https://outro-site-ruim.com.br": "Categoria"
}

# --- CONFIGURAÇÃO ---
BASE_URL = "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php"
TOKEN = "R1c4rd0_Au70m4c40_2026"
TARGET_API = f"{BASE_URL}?token={TOKEN}"

# Config Newspaper
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10
config.fetch_images = True

def enviar_pacote(lista):
    if not lista: return
    try:
        requests.post(TARGET_API, json=lista, timeout=10)
        print(f"   🚀 Enviadas {len(lista)} notícias.")
    except Exception as e:
        print(f"   ⚠️ Erro envio: {e}")

def buscar_hibrido():
    print(f"--- Iniciando Varredura Híbrida: {datetime.now()} ---")
    
    # 1. PROCESSAR RSS (LEVE) - Pode processar TODOS de uma vez
    print("📡 Processando Feeds RSS...")
    for url, categoria in RSS_FEEDS.items():
        print(f"   > Lendo Feed: {url}")
        lista_rss = []
        try:
            feed = feedparser.parse(url)
            # Pega só as 2 primeiras do feed
            for entry in feed.entries[:2]:
                try:
                    # Newspaper entra só para pegar imagem e texto full
                    article = newspaper.Article(entry.link, config=config)
                    article.download()
                    article.parse()
                    
                    img = article.top_image
                    if not img or len(article.text) < 100: continue

                    dados = {
                        "h1": article.title,
                        "img": img,
                        "p": article.text,
                        "url": entry.link,
                        "category": categoria,
                        "source": feed.feed.title if 'title' in feed.feed else "Web"
                    }
                    lista_rss.append(dados)
                except: continue
            
            enviar_pacote(lista_rss)
            
        except Exception as e:
            print(f"   ⚠️ Erro feed {url}: {e}")
        
        gc.collect() # Limpa memória a cada feed

    # 2. PROCESSAR SEM FEED (PESADO) - Sorteia apenas 1 por vez para não travar
    if SITES_SEM_FEED:
        site_sorteado = random.choice(list(SITES_SEM_FEED.items()))
        url_site, cat_site = site_sorteado
        print(f"🕵️ Varredura Manual (Sorteado): {url_site}")
        
        lista_manual = []
        try:
            paper = newspaper.build(url_site, config=config, memoize_articles=False)
            count = 0
            for article in paper.articles:
                if count >= 2: break
                try:
                    article.download()
                    article.parse()
                    if article.top_image and len(article.text) > 100:
                        lista_manual.append({
                            "h1": article.title,
                            "img": article.top_image,
                            "p": article.text,
                            "url": article.url,
                            "category": cat_site,
                            "source": paper.brand or "Web"
                        })
                        count += 1
                except: continue
            enviar_pacote(lista_manual)
        except Exception as e:
            print(f"   ⚠️ Erro manual: {e}")

    print("🏁 Fim do Ciclo.")

if __name__ == "__main__":
    buscar_hibrido()
