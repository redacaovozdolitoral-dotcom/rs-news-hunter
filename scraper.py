import feedparser
import requests
import json
from newspaper import Article
from datetime import datetime
import time
import os

# --- CONFIGURAÇÕES ---
# Pegamos do ambiente ou usamos um padrão para testes locais
KEYWORDS_STRING = os.environ.get("KEYWORDS", "Litoral Norte SP,Ilhabela,São Sebastião")
KEYWORDS = [k.strip() for k in KEYWORDS_STRING.split(",")]

HOSTINGER_API = os.environ.get("HOSTINGER_API", "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php")
API_TOKEN = os.environ.get("API_TOKEN", "R1c4rd0_Au70m4c40_2026") # Senha que definimos no PHP

def buscar_noticias():
    lista_envio = []
    print(f"--- Iniciando Busca: {datetime.now()} ---")
    
    for kw in KEYWORDS:
        print(f"🔍 Buscando por: {kw}")
        # RSS do Google News (Método mais estável que scraping direto da busca)
        encoded_kw = kw.replace(" ", "%20")
        rss_url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"Erro ao baixar RSS para {kw}: {e}")
            continue
        
        # Pega as 3 mais recentes de cada palavra-chave
        for entry in feed.entries[:3]:
            try:
                url_noticia = entry.link
                print(f"   > Processando: {entry.title[:30]}...")
                
                # Newspaper3k faz a mágica da extração
                article = Article(url_noticia)
                article.download()
                article.parse()
                
                h1 = article.title
                img = article.top_image
                texto = article.text
                
                # REGRA DE OURO: Só aceita se tiver Imagem E Texto Decente (>250 chars)
                if img and len(texto) > 250 and "http" in img:
                    dados = {
                        "h1": h1,
                        "img": img,
                        "p": texto, 
                        "url": article.url, # URL final resolvida
                        "source": entry.source.title if 'source' in entry else "Google News"
                    }
                    lista_envio.append(dados)
                    print("     ✅ Capturada!")
                else:
                    print(f"     ❌ Ignorada (Sem img ou texto curto. Tamanho: {len(texto)})")
                    
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
