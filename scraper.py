import requests
import newspaper
from newspaper import Config
from datetime import datetime
import os

# --- 1. LISTA DE SITES (VARREDURA DIRETA) ---
# Funciona para sites COM ou SEM feed.
SITES_CONFIG = {
    # REGIONAIS (Litoral Norte)
    "https://radarlitoral.com.br": "Regional",
    "https://www.litoralnoticias.com.br": "Regional",
    "https://www.tamoiosnews.com.br": "Regional",
    "https://novaimprensa.com": "Regional",
    "https://www.portalr3.com.br": "Regional",
    "https://costanorte.com.br": "Regional",
    "https://litoralnorteweb.com.br": "Regional",

    # ESPORTES
    "https://ge.globo.com/sp/futebol/": "Esporte",
    "https://www.gazetaesportiva.com": "Esporte",
    
    # AUTOMOBILISMO & VELA
    "https://www.grandepremio.com.br": "Fórmula 1",
    "https://almanautica.com.br": "Náutica",
    
    # SAÚDE & BEM ESTAR
    "https://www.minhavida.com.br": "Saúde",

    # LOTERIAS (UOL Loterias - Matérias)
    "https://noticias.uol.com.br/loterias/": "Loterias"
}

# --- 2. CONFIGURAÇÃO DE ENVIO (Hostinger) ---
BASE_URL = "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php"
TOKEN = "R1c4rd0_Au70m4c40_2026"

# Monta a URL completa de destino: .../index.php?token=SENHA
TARGET_API = f"{BASE_URL}?token={TOKEN}"

# --- 3. CONFIGURAÇÃO DO ROBÔ ---
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 20
config.fetch_images = True
config.memoize_articles = False # Sempre checa tudo (Render reinicia)

def buscar_tudo():
    lista_envio = []
    print(f"--- Iniciando Varredura Manual: {datetime.now()} ---")
    
    for url, categoria in SITES_CONFIG.items():
        print(f"🌍 Visitando Home: {url} [{categoria}]")
        try:
            # newspaper.build() varre a home e acha links de notícias
            paper = newspaper.build(url, config=config)
            
            # Pega apenas as 2 notícias mais novas da Home
            count_site = 0
            
            for article in paper.articles:
                if count_site >= 2: break 
                
                try:
                    article.download()
                    article.parse()
                    
                    # --- FILTROS ---
                    
                    # 1. IMAGEM (Tenta achar qualquer uma válida)
                    img_final = article.top_image
                    if not img_final and article.images:
                        for i in article.images:
                            if "http" in i and len(i) > 60: 
                                img_final = i
                                break
                    
                    # Se não tem imagem, ignora (regra da TV)
                    if not img_final: continue

                    # 2. CONTEÚDO
                    if not article.title: continue
                    if len(article.text) < 100: continue 

                    dados = {
                        "h1": article.title,
                        "img": img_final,
                        "p": article.text,
                        "url": article.url,
                        "category": categoria,
                        "source": paper.brand or "Web"
                    }
                    
                    lista_envio.append(dados)
                    print(f"   ✅ Capturada: {article.title[:40]}...")
                    count_site += 1
                    
                except Exception:
                    continue 
                    
        except Exception as e:
            print(f"   ⚠️ Erro ao acessar {url}: {e}")

    # ENVIO
    if lista_envio:
        print(f"🚀 Enviando {len(lista_envio)} notícias...")
        try:
            # Envia POST direto para a URL com Token
            r = requests.post(TARGET_API, json=lista_envio)
            print("Resposta Hostinger:", r.text)
        except Exception as e:
            print("Erro envio:", e)
    else:
        print("💤 Nada novo capturado agora.")

if __name__ == "__main__":
    buscar_tudo()
