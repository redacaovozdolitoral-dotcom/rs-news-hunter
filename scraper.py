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

# --- 1. LISTA DE SITES (EXATA COMO SOLICITADO) ---
RSS_FEEDS = {
    # AUTOMOBILISMO & NÁUTICA
    "https://www.grandepremio.com.br/feed/": "Fórmula 1",
    "https://nautica.com.br/feed/": "Náutica",
    
    # SAÚDE
    "https://www.tuasaude.com/feed/": "Saúde",
    
    # ESPORTE
    "https://ge.globo.com/rss/ge/futebol/": "Esporte", # Corrigi a URL do GE (a /xml estava errada)
    "https://www.gazetaesportiva.com/feed/": "Esporte",
    
    # REGIONAIS (LITORAL NORTE)
    "https://www.tamoiosnews.com.br/feed/": "Regional",
    "https://novaimprensa.com/feed/": "Regional",
    "https://www.litoralnoticias.com.br/feed/": "Regional",
    "https://costanorte.com.br/feed/": "Regional",
    "https://litoralnorteweb.com.br/feed/": "Regional"
}

SITES_SEM_FEED = {
    "https://radarlitoral.com.br": "Regional"
}

# --- 2. CONFIGURAÇÕES ---
BASE_URL = "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php"
TOKEN = "R1c4rd0_Au70m4c40_2026"
TARGET_API = f"{BASE_URL}?token={TOKEN}"

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10
config.fetch_images = True
config.keep_article_html = False

# --- 3. FUNÇÃO DE LIMPEZA DE TEXTO (PARA TV) ---
def limpar_texto_avancado(texto_bruto):
    if not texto_bruto: return ""
    
    # Termos proibidos (propagandas, menus, legendas)
    lixo_keywords = [
        "leia também", "leia mais", "saiba mais", "veja também", "confira",
        "clique aqui", "entre no grupo", "siga nosso", "siga o", "inscreva-se",
        "compartilhe", "publicidade", "anúncio", "continua após",
        "foto:", "crédito:", "divulgação", "reprodução", "imagem ilustrativa",
        "fonte:", "assista", "vídeo"
    ]
    
    linhas_limpas = []
    linhas = texto_bruto.split('\n')
    
    for linha in linhas:
        linha = linha.strip()
        
        # Remove linhas muito curtas (menos de 40 letras)
        if len(linha) < 40: continue
        
        # Remove linhas com termos proibidos
        linha_lower = linha.lower()
        if any(termo in linha_lower for termo in lixo_keywords): continue
        
        # Remove URLs soltas
        if "http" in linha_lower and " " not in linha: continue
        
        # Remove CAIXA ALTA (Geralmente avisos)
        if linha.isupper() and len(linha) > 10: continue

        linhas_limpas.append(linha)
    
    return "\n\n".join(linhas_limpas)

# --- 4. FUNÇÃO DE ENVIO ---
def enviar_pacote(lista):
    if not lista: return
    try:
        # Envia para Hostinger
        requests.post(TARGET_API, json=lista, timeout=10)
        print(f"   🚀 Enviadas {len(lista)} notícias.")
    except Exception as e:
        print(f"   ⚠️ Erro envio: {e}")

# --- 5. LOOP AUTOMÁTICO ---
def tarefa_agendada():
    while True:
        print(f"\n--- Iniciando Ciclo Automático: {datetime.now()} ---")
        
        # A) PROCESSAR RSS (LEVE)
        print("📡 Lendo RSS...")
        for url, categoria in RSS_FEEDS.items():
            lista_rss = []
            try:
                feed = feedparser.parse(url)
                # Pega as 2 mais recentes
                for entry in feed.entries[:2]:
                    try:
                        # Extrai conteúdo completo
                        article = newspaper.Article(entry.link, config=config)
                        article.download()
                        article.parse()
                        
                        # Limpa o texto
                        texto_limpo = limpar_texto_avancado(article.text)
                        
                        img = article.top_image
                        if img and len(texto_limpo) > 100:
                            lista_rss.append({
                                "h1": article.title,
                                "img": img,
                                "p": texto_limpo,
                                "url": entry.link,
                                "category": categoria,
                                "source": "RSS"
                            })
                    except: continue
                enviar_pacote(lista_rss)
            except: pass
            gc.collect() # Limpa memória

        # B) PROCESSAR SEM FEED (RADAR)
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
                        
                        texto_limpo = limpar_texto_avancado(article.text)
                        
                        if article.top_image and len(texto_limpo) > 100:
                            lista_manual.append({
                                "h1": article.title,
                                "img": article.top_image,
                                "p": texto_limpo,
                                "url": article.url,
                                "category": cat,
                                "source": "Web"
                            })
                            count += 1
                    except: continue
                enviar_pacote(lista_manual)
            except: pass
        
        print("💤 Dormindo 15 minutos...")
        time.sleep(900)

# --- 6. SERVIDOR WEB FAKE (PARA RENDER) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sistema Online")

def rodar_servidor():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Inicia o robô em background
    t = Thread(target=tarefa_agendada)
    t.start()
    
    # Inicia o servidor web
    print("🌐 Servidor Web iniciado na porta 10000")
    rodar_servidor()
