import os
import requests
from datetime import datetime, timedelta
import pytz
import re
import traceback
import logging
import sys
import random
import time
import schedule
from dotenv import load_load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def buscar_pedidos(data):
    pedidos = []
    url = f"https://{os.getenv('SHOP_NAME')}/admin/api/2023-01/orders.json?created_at_min={data}T00:00:00Z&created_at_max={data}T23:59:59Z&status=any&limit=250"
    headers = {
        "X-Shopify-Access-Token": os.getenv('ACCESS_TOKEN')
    }
    
    while url:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if 'orders' in data:
                pedidos.extend(data['orders'])
            else:
                logger.warning(f"Não foram encontrados pedidos para a data {data}")
            
            url = response.links.get('next', {}).get('url')
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar pedidos: {str(e)}")
            break

    return pedidos

def extrair_dados_clientes(pedidos):
    clientes = {}
    for pedido in pedidos:
        if not isinstance(pedido, dict):
            logger.warning(f"Pedido inválido encontrado: {pedido}")
            continue
        
        email = pedido.get('email', 'Email não disponível')
        if email not in clientes:
            shipping_address = pedido.get('shipping_address') or {}
            nome = shipping_address.get('name', 'Nome não disponível')
            telefone = formatar_telefone(shipping_address.get('phone', ''))
            clientes[email] = {
                'nome': nome,
                'email': email,
                'telefone': telefone,
                'data_ultimo_pedido': pedido.get('created_at', 'Data não disponível')
            }
    return list(clientes.values())

def formatar_telefone(telefone):
    if not telefone:
        return ''
    numeros = re.sub(r'\D', '', telefone)
    if not numeros.startswith('55'):
        numeros = '55' + numeros
    if len(numeros) < 12:
        return ''
    return numeros[:13]

def calcular_datas_busca():
    hoje = datetime.now(pytz.UTC).date()
    return {
        30: (hoje - timedelta(days=30)).strftime('%Y-%m-%d'),
        60: (hoje - timedelta(days=60)).strftime('%Y-%m-%d'),
        90: (hoje - timedelta(days=90)).strftime('%Y-%m-%d'),
        180: (hoje - timedelta(days=180)).strftime('%Y-%m-%d'),
        365: (hoje - timedelta(days=365)).strftime('%Y-%m-%d')
    }

def buscar_clientes_por_datas():
    datas_busca = calcular_datas_busca()
    clientes_por_periodo = {}
    
    for dias, data in datas_busca.items():
        pedidos = buscar_pedidos(data)
        if pedidos:
            clientes = extrair_dados_clientes(pedidos)
            clientes_por_periodo[dias] = clientes
        else:
            logger.info(f"Nenhum pedido encontrado para o período de {dias} dias atrás.")
    
    return clientes_por_periodo

def gerar_cupom(nome, telefone, dias):
    nome_limpo = re.sub(r'[^a-zA-Z]', '', nome)
    prefixo = nome_limpo[:3].upper()
    sufixo = telefone[-5:] if len(telefone) >= 5 else telefone.zfill(5)
    
    if dias <= 30:
        desconto = 10
    elif dias <= 60:
        desconto = 12
    elif dias <= 90:
        desconto = 14
    elif dias <= 180:
        desconto = 17
    else:
        desconto = 20
    
    cupom = f"{prefixo}{sufixo}OFF{desconto}"
    
    return cupom, desconto

def calcular_data_validade():
    return datetime.now() + timedelta(days=1)

def gerar_mensagem_personalizada(nome, cupom, desconto, dias):
    data_validade = calcular_data_validade().strftime("%d/%m/%Y às %H:%M")
    mensagem = f"""🌟 Olá, {nome}! 🌟
🎉 Já faz *{dias} dias* que você não compra nada na Fiber! A gente sente sua falta! Para te dar boas-vindas de volta, temos um presentão pra você!
🎁 *Use o cupom:* *{cupom}* e ganhe *{desconto}% de desconto* na sua próxima compra! 
🛒 Dá uma olhada nos nossos novos produtos e aproveita essa oferta incrível. Só presta atenção para não deixar esta oportunidade escapar, o cupom é válido somente até *{data_validade}*!
👉 *Como usar:* Na hora de finalizar a compra, insira o código *{cupom}* no campo de cupom de desconto.
Estamos doidos pra te ver de novo! Se precisar de qualquer coisa, é só chamar! 😊

⚠️ Este número de WhatsApp é apenas para notificações sobre ofertas. Para dúvidas ou suporte, por favor, utilize o número: 5199692122"""
    return mensagem

def criar_cupom_shopify(nome_cupom, cupom, desconto, data_validade):
    price_rule_data = {
        "price_rule": {
            "title": nome_cupom,
            "target_type": "line_item",
            "target_selection": "all",
            "allocation_method": "across",
            "value_type": "percentage",
            "value": f"-{desconto}.0",
            "customer_selection": "all",
            "starts_at": datetime.now().isoformat(),
            "ends_at": data_validade.isoformat()
        }
    }
    try:
        response = requests.post(
            f"https://{os.getenv('SHOP_NAME')}/admin/api/2023-01/price_rules.json",
            json=price_rule_data,
            headers={"X-Shopify-Access-Token": os.getenv('ACCESS_TOKEN')}
        )
        response.raise_for_status()
        price_rule = response.json()['price_rule']
        logger.info(f"Regra de preço criada com ID: {price_rule['id']}")
        
        discount_code_data = {
            "discount_code": {
                "code": cupom,
                "price_rule_id": price_rule['id']
            }
        }
        response = requests.post(
            f"https://{os.getenv('SHOP_NAME')}/admin/api/2023-01/price_rules/{price_rule['id']}/discount_codes.json",
            json=discount_code_data,
            headers={"X-Shopify-Access-Token": os.getenv('ACCESS_TOKEN')}
        )
        response.raise_for_status()
        discount_code = response.json()['discount_code']
        logger.info(f"Código de desconto criado na Shopify: {discount_code['code']}")
        return True
    except requests.RequestException as e:
        logger.error(f"Erro ao criar cupom na Shopify: {str(e)}")
        return False

def send_whatsapp_message(number, message):
    url = f"{os.getenv('EVOLUTION_ENDPOINT')}/message/sendText/{os.getenv('EVOLUTION_INSTANCE')}"
    
    payload = {
        "number": number,
        "textMessage": {"text": message},
        "options": {
            "delay": 1000,
            "presence": "composing",
            "linkPreview": True
        }
    }
    headers = {
        "apikey": os.getenv('EVOLUTION_API_KEY'),
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Enviando mensagem de WhatsApp para {number}")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Mensagem de WhatsApp enviada com sucesso para {number}")
        return True
    except requests.RequestException as e:
        logger.error(f"Falha ao enviar mensagem de WhatsApp para {number}. Erro: {str(e)}")
        return False

def imprimir_dados_clientes(clientes_por_periodo):
    for dias, clientes in clientes_por_periodo.items():
        logger.info(f"\n--- Clientes que fizeram o último pedido há {dias} dias ---")
        if not clientes:
            logger.info("Nenhum cliente encontrado para este período.")
        else:
            for cliente in clientes:
                cupom, desconto = gerar_cupom(cliente['nome'], cliente['telefone'], dias)
                nome_cupom = f"Desconto de {desconto}% para {cliente['nome']}"
                data_validade = calcular_data_validade()
                
                cupom_criado = criar_cupom_shopify(nome_cupom, cupom, desconto, data_validade)
                
                mensagem = gerar_mensagem_personalizada(cliente['nome'].split()[0], cupom, desconto, dias)
                
                logger.info(f"Data do último pedido: {cliente['data_ultimo_pedido'][:10]}")
                logger.info(f"Nome: {cliente['nome']}")
                logger.info(f"Email: {cliente['email']}")
                logger.info(f"Telefone: {cliente['telefone']}")
                logger.info(f"Nome do cupom: {nome_cupom}")
                logger.info(f"Código do cupom de desconto: {cupom}")
                logger.info(f"Valor do desconto: {desconto}%")
                logger.info(f"Data de validade do cupom: {data_validade.strftime('%d/%m/%Y às %H:%M')}")
                logger.info(f"Cupom criado na Shopify: {'Sim' if cupom_criado else 'Não'}")
                logger.info("\nMensagem personalizada:")
                logger.info(mensagem)
                
                # Enviar mensagem de WhatsApp
                if send_whatsapp_message(cliente['telefone'], mensagem):
                    logger.info("Mensagem de WhatsApp enviada com sucesso.")
                else:
                    logger.warning("Falha ao enviar mensagem de WhatsApp.")
                
                logger.info("--------------------")
                
                # Intervalo aleatório entre 2 a 5 minutos (120 a 300 segundos)
                intervalo = random.randint(120, 300)
                logger.info(f"Aguardando {intervalo} segundos antes da próxima mensagem...")
                time.sleep(intervalo)

def executar():
    logger.info("Iniciando o processo de busca, criação de cupons e envio de mensagens...")
    clientes_por_periodo = buscar_clientes_por_datas()
    if not clientes_por_periodo:
        logger.warning("Nenhum cliente encontrado em nenhum período.")
    else:
        imprimir_dados_clientes(clientes_por_periodo)
    logger.info("Processo concluído.")

def job():
    try:
        executar()
    except Exception as e:
        logger.error(f"Ocorreu um erro não tratado durante a execução do script: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    schedule.every().day.at("08:00").do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute