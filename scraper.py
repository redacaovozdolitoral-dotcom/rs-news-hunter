import requests
import feedparser
import newspaper
from newspaper import Config
from datetime import datetime
import os
import gc
import random
import time
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SEUS SITES ---
RSS_FEEDS = {
    "https://www.grandepremio.com.br/feed/": "Fórmula 1",
    "https://nautica.com.br/feed/": "Náutica",
    "https://www.tuasaude.com/feed/": "Saúde",
    "https://ge.globo.com/rss/ge/futebol/xml": "Esporte", # Exemplo RSS GE
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
# CONFIG
BASE_URL = "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php"
TOKEN = "R1c4rd0_Au70m4c40_2026"
TARGET_API = f"{BASE_URL}?token={TOKEN}"

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

def tarefa_agendada():
    """Roda a cada 15 minutos em loop infinito"""
    while True:
        print(f"\n--- Iniciando Ciclo Automático: {datetime.now()} ---")
        
        # 1. RSS (Leve)
        print("📡 Lendo RSS...")
        for url, categoria in RSS_FEEDS.items():
            lista_rss = []
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:2]:
                    try:
                        article = newspaper.Article(entry.link, config=config)
                        article.download()
                        article.parse()
                        img = article.top_image
                        if img and len(article.text) > 100:
                            lista_rss.append({
                                "h1": article.title,
                                "img": img,
                                "p": article.text,
                                "url": entry.link,
                                "category": categoria,
                                "source": "RSS"
                            })
                    except: continue
                enviar_pacote(lista_rss)
            except: pass
            gc.collect()

        # 2. Sem Feed (Um por vez)
        if SITES_SEM_FEED:
            url, cat = random.choice(list(SITES_SEM_FEED.items()))
            print(f"🕵️ Varrendo: {url}")
            try:
                paper = newspaper.build(url, config=config, memoize_articles=False)
                lista_manual = []
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
                                "category": cat,
                                "source": "Web"
                            })
                            count += 1
                    except: continue
                enviar_pacote(lista_manual)
            except: pass
        
        print("💤 Dormindo 15 minutos...")
        time.sleep(900) # 900 segundos = 15 minutos

# Servidor Web Falso para o Render não reclamar
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Estou vivo e rodando!")

def rodar_servidor():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Inicia a tarefa em background
    t = Thread(target=tarefa_agendada)
    t.start()
    
    # Inicia o servidor web (trava o script aqui para não sair)
    print("🌐 Servidor Web iniciado na porta 10000")
    rodar_servidor()
