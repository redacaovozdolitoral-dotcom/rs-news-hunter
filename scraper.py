import feedparser
import requests
import json
from newspaper import Article, Config
from datetime import datetime
import time
import os

# --- LISTA DE SITES ALVO (FEEDS DIRETOS) ---
# Adicione ou remova sites aqui. A maioria dos sites aceita "/feed" no final.
DEFAULT_FEEDS = [
    "https://g1.globo.com/dynamo/sp/vale-do-paraiba-regiao/rss2.xml", # G1 Vale/Litoral
    "https://www.tamoiosnews.com.br/feed/", # Tamoios News
    "https://radarlitoral.com.br/feed/",    # Radar Litoral
    "https://novaimprensa.com/feed/",       # Nova Imprensa
    "https://jornalilhabella.com.br/feed/"  # Jornal Ilhabela (se existir, se não, removemos)
]

# Pega feeds extras das variáveis de ambiente se houver
ENV_FEEDS = os.environ.get("TARGET_FEEDS", "")
if ENV_FEEDS:
    FEEDS = ENV_FEEDS.split(",")
else:
    FEEDS = DEFAULT_FEEDS

HOSTINGER_API = os.environ.get("HOSTINGER_API", "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php")
API_TOKEN = os.environ.get("API_TOKEN", "R1c4rd0_Au70m4c40_2026")

# Configuração do "Navegador"
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 20

def buscar_noticias_direto():
    lista_envio = []
    print(f"--- Iniciando Busca Direta: {datetime.now()} ---")
    
    for rss_url in FEEDS:
        print(f"📡 Lendo Feed: {rss_url}")
        
        try:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                print("   ⚠️ Feed vazio ou erro de leitura.")
                continue
        except Exception as e:
            print(f"   ⚠️ Erro ao abrir feed: {e}")
            continue
        
        # Pega as 3 notícias mais recentes de cada site
        for entry in feed.entries[:3]:
            try:
                url_real = entry.link
                print(f"   > Processando: {entry.title[:30]}...")
                
                # Newspaper entra no link e raspa tudo
                article = Article(url_real, config=config)
                article.download()
                article.parse()
                
                h1 = article.title
                img = article.top_image
                texto = article.text
                
                # --- FILTROS DE QUALIDADE ---
                # 1. Tem imagem? 
                # 2. Texto é longo o suficiente (> 300 chars)?
                # 3. Ignora se for só video (G1 costuma ter links só de video)
                if img and len(texto) > 300 and "http" in img:
                    dados = {
                        "h1": h1,
                        "img": img,
                        "p": texto, 
                        "url": url_real,
                        "source": feed.feed.title if 'title' in feed.feed else "Portal de Notícias"
                    }
                    lista_envio.append(dados)
                    print(f"     ✅ SUCESSO! Capturado ({len(texto)} chars).")
                else:
                    print(f"     ❌ Ignorada (Sem img ou texto muito curto/vídeo).")
                    
            except Exception as e:
                print(f"     ⚠️ Erro ao raspar artigo: {e}")
                continue

    # Envio para Hostinger
    if lista_envio:
        print(f"🚀 Enviando {len(lista_envio)} notícias para Hostinger...")
        headers = {'HTTP_X_API_TOKEN': API_TOKEN}
        try:
            r = requests.post(HOSTINGER_API, json=lista_envio, headers=headers)
            print("Resposta do Servidor:", r.text)
        except Exception as e:
            print("FATAL: Erro de conexão com Hostinger:", e)
    else:
        print("💤 Nada novo ou relevante encontrado nos sites.")

if __name__ == "__main__":
    buscar_noticias_direto()
