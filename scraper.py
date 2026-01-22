import requests
import newspaper
from newspaper import Config
from datetime import datetime
import os
import gc
import random # Importante para sortear

# --- LISTA COMPLETA ---
ALL_SITES = {
    "https://radarlitoral.com.br": "Regional",
    "https://www.litoralnoticias.com.br": "Regional",
    "https://www.tamoiosnews.com.br": "Regional",
    "https://novaimprensa.com": "Regional",
    "https://www.portalr3.com.br": "Regional",
    "https://costanorte.com.br": "Regional",
    "https://litoralnorteweb.com.br": "Regional",
    "https://ge.globo.com/sp/futebol/": "Esporte",
    "https://www.gazetaesportiva.com": "Esporte",
    "https://www.grandepremio.com.br": "Fórmula 1",
    "https://almanautica.com.br": "Náutica",
    "https://www.minhavida.com.br": "Saúde",
    "https://noticias.uol.com.br/loterias/": "Loterias"
}

# --- CONFIGURAÇÃO ---
BASE_URL = "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php"
TOKEN = "R1c4rd0_Au70m4c40_2026"
TARGET_API = f"{BASE_URL}?token={TOKEN}"

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10
config.fetch_images = True
config.memoize_articles = False
config.keep_article_html = False

def buscar_fatiado():
    print(f"--- Iniciando Varredura Fatiada: {datetime.now()} ---")
    
    # ESTRATÉGIA ANTI-MEMÓRIA CHEIA:
    # Escolhe apenas 4 sites aleatórios desta lista gigante para processar AGORA.
    # Na próxima execução (daqui a 10 min), ele escolherá outros 4.
    sites_items = list(ALL_SITES.items())
    sites_da_vez = dict(random.sample(sites_items, 4)) # Pega só 4
    
    print(f"🎲 Sorteados para esta rodada: {list(sites_da_vez.keys())}")

    for url, categoria in sites_da_vez.items():
        print(f"🌍 Visitando: {url} [{categoria}]")
        lista_envio = []
        
        try:
            paper = newspaper.build(url, config=config, memoize_articles=False)
            
            count = 0
            for article in paper.articles:
                if count >= 2: break
                
                try:
                    article.download()
                    article.parse()
                    
                    img = article.top_image
                    if not img and article.images:
                         for i in article.images:
                            if "http" in i and len(i) > 60: 
                                img = i
                                break
                    
                    if not img: continue
                    if not article.title: continue
                    if len(article.text) < 100: continue

                    dados = {
                        "h1": article.title,
                        "img": img,
                        "p": article.text,
                        "url": article.url,
                        "category": categoria,
                        "source": paper.brand or "Web"
                    }
                    lista_envio.append(dados)
                    print(f"   ✅ OK: {article.title[:30]}...")
                    count += 1

                except:
                    continue
            
            if lista_envio:
                try:
                    requests.post(TARGET_API, json=lista_envio, timeout=10)
                    print(f"   🚀 Enviadas {len(lista_envio)} notícias")
                except Exception as e:
                    print(f"   ⚠️ Erro envio: {e}")
            
        except Exception as e:
            print(f"   ⚠️ Erro site: {e}")
        
        del paper
        gc.collect()

    print("🏁 Ciclo finalizado (Memória preservada).")

if __name__ == "__main__":
    buscar_fatiado()
