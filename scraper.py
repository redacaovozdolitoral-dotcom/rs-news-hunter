import requests
import newspaper
from newspaper import Config
from datetime import datetime
import os

# --- CENTRAL DE SITES E CATEGORIAS ---
# Adicione ou remova sites conforme necessidade.
SITES_CONFIG = {
    # REGIONAIS (Litoral Norte)
    "https://www.litoralnoticias.com.br": "Regional",
    "https://radarlitoral.com.br": "Regional",
    "https://www.tamoiosnews.com.br": "Regional",
    "https://novaimprensa.com": "Regional",
    "https://www.portalr3.com.br": "Regional",
    

    # ESPORTES (Geral e Futebol)
    "https://ge.globo.com/sp/futebol/": "Esporte",
    "https://www.gazetaesportiva.com": "Esporte",
    
    # AUTOMOBILISMO & VELA
    "https://www.grandepremio.com.br": "Fórmula 1",
    "https://almanautica.com.br": "Náutica",
    
    # SAÚDE
    "https://www.minhavida.com.br": "Saúde",

    # LOTERIAS (Página de notícias de loteria do UOL)
    "https://noticias.uol.com.br/loterias/": "Loterias"
}

# --- CONFIGURAÇÕES DE ENVIO ---
# Tenta pegar das variáveis do Render, se não usa o padrão
HOSTINGER_API = os.environ.get("HOSTINGER_API", "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php")
API_TOKEN = os.environ.get("API_TOKEN", "R1c4rd0_Au70m4c40_2026")

# --- CONFIGURAÇÃO DO NAVEGADOR ---
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 15 # Timeout curto para agilidade
config.fetch_images = True
config.memoize_articles = False # Sempre verifica tudo de novo (Render reinicia a memória)

def buscar_tudo():
    lista_envio = []
    print(f"--- Iniciando Varredura Geral: {datetime.now()} ---")
    
    for url, categoria in SITES_CONFIG.items():
        print(f"🌍 Visitando: {url} [{categoria}]")
        try:
            # Constrói a estrutura do site (varredura da home)
            paper = newspaper.build(url, config=config)
            
            # Limite de segurança: Pega apenas as 2 notícias mais novas de cada site
            # Isso evita que um site com 50 notícias abafe os outros
            limitador = 0
            
            for article in paper.articles:
                if limitador >= 2: break 
                
                try:
                    article.download()
                    article.parse()
                    
                    # --- FILTROS INTELIGENTES ---
                    
                    # 1. IMAGEM (Flexível)
                    img_final = article.top_image
                    # Se não achou a principal, tenta achar qualquer outra no corpo
                    if not img_final and article.images:
                        for i in article.images:
                            if "http" in i and len(i) > 60: # URL válida
                                img_final = i
                                break
                    
                    # Se mesmo assim não tiver imagem, pula (TV precisa de imagem)
                    if not img_final: continue

                    # 2. TÍTULO E TEXTO
                    if not article.title: continue
                    if len(article.text) < 100: continue # Mínimo 100 caracteres

                    # MONTAGEM DO DADOS
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
                    limitador += 1
                    
                except Exception:
                    continue # Se falhar uma notícia, tenta a próxima
                    
        except Exception as e:
            print(f"   ⚠️ Erro ao acessar site {url}: {e}")

    # ENVIO PARA HOSTINGER
    if lista_envio:
        print(f"🚀 Enviando {len(lista_envio)} notícias para a base...")
        try:
            r = requests.post(HOSTINGER_API, json=lista_envio, headers={'HTTP_X_API_TOKEN': API_TOKEN})
            print("Status Servidor:", r.text)
        except Exception as e:
            print("Erro fatal de envio:", e)
    else:
        print("💤 Nenhuma notícia nova encontrada nesta rodada.")

if __name__ == "__main__":
    buscar_tudo()
