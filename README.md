# Customer Rewards System

This project is a Python-based system designed to track customer orders and send personalized discount coupons via WhatsApp to customers who haven't made a purchase in a while. It integrates with the Shopify API to retrieve order data and uses the Evolution API to send messages.

## Features

- Connects to Shopify API to retrieve customer orders based on specific date ranges.
- Extracts customer data from orders.
- Generates unique discount coupons based on the time since the last purchase.
- Sends personalized messages with discount coupons via WhatsApp.
- Logs all activities for monitoring and debugging.

## Requirements

- Python 3.x
- `requests` library
- `pytz` library
- `schedule` library
- `python-dotenv` library
- Access to Shopify API
- Access to WhatsApp messaging API

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required packages:
   ```bash
   pip install requests pytz schedule python-dotenv
   ```

3. Create a `.env` file in the project root and add the following environment variables:
   ```plaintext
   SHOP_NAME=<your-shop-name>
   ACCESS_TOKEN=<your-access-token>
   EVOLUTION_ENDPOINT=<your-evolution-endpoint>
   EVOLUTION_INSTANCE=<your-evolution-instance>
   EVOLUTION_API_KEY=<your-evolution-api-key>
   ```

## Usage

Run the script to start the customer rewards system:
```bash
python customer_rewards_system.py
```

The script will check for customer orders, generate discount coupons for eligible customers, and send WhatsApp messages. It is scheduled to run daily at 08:00 AM (São Paulo timezone).

## Logging

All activities are logged into the console and can be monitored for any errors or information regarding the execution of the script.

## Functions

- `buscar_pedidos(data_inicio, data_fim)`: Retrieves orders from Shopify within the specified date range.
- `extrair_dados_clientes(pedidos)`: Extracts customer data from the retrieved orders.
- `formatar_telefone(telefone)`: Formats the phone number to a standard format.
- `calcular_datas_busca()`: Calculates the date ranges for customer searches.
- `buscar_clientes_por_datas()`: Retrieves customers based on their last purchase date.
- `gerar_cupom(nome, telefone, dias)`: Generates a discount coupon based on the number of days since the last purchase.
- `calcular_data_validade()`: Calculates the expiration date for the discount coupon.
- `gerar_mensagem_personalizada(nome, cupom, desconto, dias)`: Creates a personalized message for the customer.
- `criar_cupom_shopify(nome_cupom, cupom, desconto, data_validade)`: Creates a discount coupon in Shopify.
- `send_whatsapp_message(number, message)`: Sends a WhatsApp message to the specified number.
- `processar_cliente(cliente, dias)`: Processes the customer data and sends the discount coupon.
- `imprimir_dados_clientes(clientes_por_periodo)`: Prints customer data for each period and processes them.
- `executar()`: Executes the main process of the rewards system.
- `agendar_proxima_execucao()`: Schedules the next execution of the script.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
