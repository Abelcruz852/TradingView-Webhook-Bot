# send_alert.py
from binance.client import Client
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)

# Ruta del archivo de capital virtual
CAPITAL_FILE = "capital_virtual.json"

# Función para cargar y actualizar capital virtual
def manejar_capital(resultado_trade=None):
    if not os.path.exists(CAPITAL_FILE):
        # Si no existe el archivo, crear uno con capital inicial por defecto
        with open(CAPITAL_FILE, 'w') as f:
            json.dump({"capital": 80}, f)

    with open(CAPITAL_FILE, 'r') as f:
        datos = json.load(f)

    capital = datos.get("capital", 80)

    # Si se proporciona un resultado, actualizar capital
    if resultado_trade is not None:
        capital += resultado_trade
        datos["capital"] = round(capital, 2)
        with open(CAPITAL_FILE, 'w') as f:
            json.dump(datos, f)

    return capital

def send_alert(data):
    try:
        symbol = data['symbol']
        side = data['side']
        entry_price = float(data['entry'])
        sl_price    = float(data['sl'])
        tp_price    = float(data['tp'])

        leverage     = int(data.get('leverage', 20))
        riesgo_pct   = float(data.get('riesgo_pct', 0.01))

        # Usar capital virtual automatizado
        capital = manejar_capital()

        # Calcular riesgo por precio
        distancia_sl = abs(entry_price - sl_price)
        if distancia_sl == 0:
            raise ValueError("Distancia SL no puede ser cero")

        riesgo_dolares = capital * riesgo_pct * leverage
        quantity = round(riesgo_dolares / distancia_sl, 3)

        if side == "BUY":
            exit_side = "SELL"
        else:
            exit_side = "BUY"

        # Configurar apalancamiento y margen
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        client.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')

        # Ejecutar orden de mercado
        print("📤 Ejecutando orden de mercado...")
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity
        )

        # Colocar TP (limit)
        client.futures_create_order(
            symbol=symbol,
            side=exit_side,
            type="LIMIT",
            price=str(round(tp_price, 4)),
            quantity=quantity,
            timeInForce="GTC",
            reduceOnly=True
        )

        # Colocar SL (stop market)
        client.futures_create_order(
            symbol=symbol,
            side=exit_side,
            type="STOP_MARKET",
            stopPrice=str(round(sl_price, 4)),
            closePosition=True,
            reduceOnly=True
        )

        print("✅ Operación colocada con éxito en Binance Futures")

        # Estimar resultado y actualizar capital virtual
        potencial_riesgo = distancia_sl * quantity
        potencial_ganancia = abs(tp_price - entry_price) * quantity

        # Supongamos que todas las alertas resultan en SL (para ser conservadores):
        manejar_capital(resultado_trade=-potencial_riesgo)

    except Exception as e:
        print(f"❌ ERROR: {e}")
