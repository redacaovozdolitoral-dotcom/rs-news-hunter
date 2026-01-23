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

# --- 1. LISTA DE SITES DE NOTÍCIAS ---
RSS_FEEDS = {
    "https://www.grandepremio.com.br/feed/": "Fórmula 1",
    "https://nautica.com.br/feed/": "Náutica",
    "https://www.tuasaude.com/feed/": "Saúde",
    "https://ge.globo.com/rss/ge/futebol/": "Esporte",
    "https://www.gazetaesportiva.com/feed/": "Esporte",
    "https://www.tamoiosnews.com.br/feed/": "Regional",
    "https://novaimprensa.com/feed/": "Regional",
    "https://www.litoralnoticias.com.br/feed/": "Regional",
    "https://costanorte.com.br/feed/": "Regional",
    "https://litoralnorteweb.com.br/feed/": "Regional"
}

SITES_SEM_FEED = {
    "https://radarlitoral.com.br": "Regional"
}

# --- CONFIGURAÇÕES ---
BASE_URL = "https://darkseagreen-nightingale-543295.hostingersite.com/automacao-news/index.php"
TOKEN = "R1c4rd0_Au70m4c40_2026"
TARGET_API = f"{BASE_URL}?token={TOKEN}"

# Imagens padrão para Loterias (Use links que não expirem)
IMG_MEGA = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Mega-Sena_logo.svg/1200px-Mega-Sena_logo.svg.png"
IMG_LOTOFACIL = "https://logodownload.org/wp-content/uploads/2018/10/lotofacil-logo.png"

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10
config.fetch_images = True
config.keep_article_html = False

# --- LIMPEZA DE TEXTO ---
def limpar_texto_avancado(texto_bruto):
    if not texto_bruto: return ""
    lixo_keywords = ["leia também", "leia mais", "saiba mais", "veja também", "confira", "clique aqui", "entre no grupo", "siga nosso", "siga o", "inscreva-se", "compartilhe", "publicidade", "anúncio", "continua após", "foto:", "crédito:", "divulgação", "reprodução", "imagem ilustrativa", "fonte:", "assista", "vídeo"]
    linhas_limpas = []
    for linha in texto_bruto.split('\n'):
        linha = linha.strip()
        if len(linha) < 40: continue
        if any(termo in linha.lower() for termo in lixo_keywords): continue
        if "http" in linha.lower() and " " not in linha: continue
        if linha.isupper() and len(linha) > 10: continue
        linhas_limpas.append(linha)
    return "\n\n".join(linhas_limpas)

def enviar_pacote(lista):
    if not lista: return
    try:
        requests.post(TARGET_API, json=lista, timeout=10)
        print(f"   🚀 Enviadas {len(lista)} notícias.")
    except Exception as e:
        print(f"   ⚠️ Erro envio: {e}")

# --- NOVA FUNÇÃO: LOTERIAS ---
def buscar_loterias():
    print("🍀 Buscando Loterias...")
    lista_loterias = []
    
    # Jogos para buscar: 'megasena', 'lotofacil'
    jogos = [
        ('megasena', 'Mega-Sena', IMG_MEGA),
        ('lotofacil', 'Lotofácil', IMG_LOTOFACIL)
    ]
    
    for jogo_api, nome_jogo, img_url in jogos:
        try:
            # Usa a API gratuita da GUBI ou similar
            url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{jogo_api}"
            # Como a API da Caixa é chata e bloqueia, vamos usar uma API proxy pública mais simples:
            # API Alternativa (Loterias API) - Muito mais estável
            r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{jogo_api}", timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                
                # Formata os dados
                concurso = data['concurso']
                data_sorteio = data['data']
                dezenas = ", ".join(data['dezenas'])
                
                # Monta o texto bonitinho para a TV
                titulo = f"Resultado {nome_jogo}: Confira os números do concurso {concurso}"
                
                # Verifica se acumulou
                if data['acumulou']:
                    premio_texto = f"ACUMULOU! Próximo prêmio estimado: R$ {data['proximoConcurso']['valorEstimado'] if 'proximoConcurso' in data else '???'}"
                else:
                    # Pega o premio da faixa principal
                    premio = "---"
                    # A estrutura pode variar, então tratamos com cuidado
                    if 'premiacoes' in data and len(data['premiacoes']) > 0:
                         premio = f"R$ {data['premiacoes'][0]['premio']}"
                    premio_texto = f"Prêmio principal: {premio}"

                corpo_noticia = f"""
                Saiu o resultado da {nome_jogo} pelo concurso {concurso}, realizado em {data_sorteio}.
                
                Confira as dezenas sorteadas:
                {dezenas}
                
                {premio_texto}
                
                Confira seu bilhete em uma casa lotérica oficial.
                """
                
                lista_loterias.append({
                    "h1": titulo,
                    "img": img_url, # Usa a imagem padrão do logo
                    "p": corpo_noticia,
                    "url": f"https://loterias.caixa.gov.br/{jogo_api}/{concurso}", # Link fake único para não duplicar
                    "category": "Loterias",
                    "source": "Caixa Econômica"
                })
        except Exception as e:
            print(f"   ⚠️ Erro ao buscar {nome_jogo}: {e}")
    
    enviar_pacote(lista_loterias)

# --- LOOP AUTOMÁTICO ---
def tarefa_agendada():
    while True:
        print(f"\n--- Ciclo Iniciado: {datetime.now()} ---")
        
        # 1. Busca Loterias (Rápido)
        buscar_loterias()
        gc.collect()

        # 2. Busca RSS
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
            gc.collect()

        # 3. Busca Manual
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

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sistema Online")

def rodar_servidor():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

if __name__ == "__main__":
    t = Thread(target=tarefa_agendada)
    t.start()
    print("🌐 Servidor Web iniciado na porta 10000")
    rodar_servidor()
