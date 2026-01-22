import feedparser
import requests
import json
from newspaper import Article, Config
from datetime import datetime
import time
import os
from googlenewsdecoder import gnewsdecoder

# --- CONFIGURAÇÕES ---
KEYWORDS_STRING = os.environ.get("KEYWORDS", "Litoral Norte SP,Ilhabela,São Sebastião")
KEYWORDS = [k.strip() for k in KEYWORDS_STRING.split(",")]

HOSTINGER_API = os.environ.get("HOSTINGER_API", "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php")
API_TOKEN = os.environ.get("API_TOKEN", "R1c4rd0_Au70m4c40_2026")

# Config do Newspaper (Falso Navegador)
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 20

def buscar_noticias():
    lista_envio = []
    print(f"--- Iniciando Busca: {datetime.now()} ---")
    
    for kw in KEYWORDS:
        print(f"🔍 Buscando por: {kw}")
        encoded_kw = kw.replace(" ", "%20")
        rss_url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"Erro ao baixar RSS: {e}")
            continue
        
        # Pega as 3 primeiras
        for entry in feed.entries[:3]:
            try:
                print(f"   > Link Encontrado: {entry.title[:30]}...")
                
                # --- A MÁGICA ACONTECE AQUI ---
                # Decodifica a URL do Google para a URL Real
                try:
                    resultado_decode = gnewsdecoder(entry.link)
                    if resultado_decode.get("status"):
                        url_real = resultado_decode["decoded_url"]
                        print(f"     🔓 URL Decodificada: {url_real}")
                    else:
                        print(f"     ⚠️ Falha ao decodificar: {entry.link}")
                        continue
                except Exception as e:
                    print(f"     ⚠️ Erro no decoder: {e}")
                    # Tenta usar o link original se o decoder falhar (fallback)
                    url_real = entry.link

                # Agora baixamos a notícia real
                article = Article(url_real, config=config)
                article.download()
                article.parse()
                
                h1 = article.title
                img = article.top_image
                texto = article.text
                
                # Filtros de Qualidade
                if img and len(texto) > 250 and "http" in img:
                    dados = {
                        "h1": h1,
                        "img": img,
                        "p": texto, 
                        "url": url_real,
                        "source": entry.source.title if 'source' in entry else "Google News"
                    }
                    lista_envio.append(dados)
                    print(f"     ✅ SUCESSO! Texto com {len(texto)} caracteres.")
                else:
                    print(f"     ❌ Ignorada (Sem img ou texto curto: {len(texto)})")
                    
            except Exception as e:
                print(f"     ⚠️ Erro ao ler noticia: {e}")
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
        print("💤 Nenhuma notícia válida encontrada nesta rodada.")

if __name__ == "__main__":
    buscar_noticias()
