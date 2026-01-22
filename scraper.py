import requests
import newspaper
from newspaper import Config
from datetime import datetime
import os
import gc # Garbage Collector (para limpar a memória)

# --- 1. LISTA DE SITES ---
SITES_CONFIG = {
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

# --- 2. CONFIGURAÇÃO DE ENVIO ---
BASE_URL = "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php"
TOKEN = "R1c4rd0_Au70m4c40_2026"
TARGET_API = f"{BASE_URL}?token={TOKEN}"

# --- 3. CONFIGURAÇÃO LEVE ---
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10
config.fetch_images = True
config.memoize_articles = False # Desliga cache para economizar RAM
config.keep_article_html = False # Não salva HTML bruto

def buscar_tudo_leve():
    print(f"--- Iniciando Varredura Leve: {datetime.now()} ---")
    
    # Processa um site de cada vez e envia IMEDIATAMENTE para liberar memória
    for url, categoria in SITES_CONFIG.items():
        print(f"🌍 Visitando: {url} [{categoria}]")
        lista_envio = []
        
        try:
            # OTIMIZAÇÃO: Varre apenas a estrutura inicial, sem aprofundar
            paper = newspaper.build(url, config=config, memoize_articles=False)
            
            # Pega só as 2 primeiras notícias encontradas
            count = 0
            for article in paper.articles:
                if count >= 2: break
                
                try:
                    article.download()
                    article.parse()
                    
                    # Filtros Rápidos
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
            
            # ENVIA O LOTE DESTE SITE E LIMPA A LISTA
            if lista_envio:
                try:
                    requests.post(TARGET_API, json=lista_envio, timeout=10)
                    print(f"   🚀 Enviadas {len(lista_envio)} notícias de {url}")
                except Exception as e:
                    print(f"   ⚠️ Erro envio: {e}")
            
        except Exception as e:
            print(f"   ⚠️ Erro site: {e}")
        
        # LIMPEZA DE MEMÓRIA CRÍTICA
        del paper # Apaga o objeto pesado da memória
        gc.collect() # Força o Python a limpar a RAM agora
        print("   🧹 Memória limpa.")

    print("🏁 Ciclo finalizado.")

if __name__ == "__main__":
    buscar_tudo_leve()
