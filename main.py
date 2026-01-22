#!/usr/bin/env python3
"""
Bot de trading crypto - Cloud 24/7
Scan automatique toutes les 30 minutes avec support Proxy VPN
"""

import os
import time
import schedule
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
from telegram_notifier import TelegramNotifier
from signal_detector import SignalDetector

class CryptoTradingBot:
    def __init__(self):
        """Initialise le bot avec support Proxy SOCKS5 pour éviter l'erreur 403"""
        
        # Récupération des identifiants NordVPN depuis Railway
        vpn_user = os.getenv('VPN_USER')
        vpn_pass = os.getenv('VPN_PASS')
        
        # Configuration du proxy (On utilise le serveur SOCKS5 Pays-Bas, le plus stable)
        proxy_url = f'socks5://{vpn_user}:{vpn_pass}@nl.socks.nordhold.net:1080'
        
        # Configuration de l'échange Bybit via CCXT
        self.exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
            'proxies': {
                'http': proxy_url,
                'https': proxy_url,
            },
            'urls': {
                'api': {
                    'public': 'https://api.bytick.com',
                    'private': 'https://api.bytick.com',
                }
            }
        })
        
        # Initialisation Telegram
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.notifier = TelegramNotifier(telegram_token, telegram_chat_id)
        
        # Détecteur de signaux
        self.signal_detector = SignalDetector()
        
        # Liste étendue à 25 cryptos
        self.watchlist = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
            'ADA/USDT', 'DOGE/USDT', 'LINK/USDT', 'AVAX/USDT', 'MATIC/USDT',
            'DOT/USDT', 'UNI/USDT', 'LTC/USDT', 'ATOM/USDT', 'ETC/USDT',
            'NEAR/USDT', 'ALGO/USDT', 'ICP/USDT', 'VET/USDT', 'FIL/USDT',
            'APT/USDT', 'OP/USDT', 'ARB/USDT', 'INJ/USDT', 'TIA/USDT'
        ]
        
        self.timeframes = ['1h', '4h', '1d']
        self.sent_signals = {} 

    def fetch_data(self, symbol, timeframe, limit=100):
        """Récupère les données historiques via le proxy"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculs indicateurs (RSI & Bollinger)
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (std * 2)
            df['bb_lower'] = df['bb_middle'] - (std * 2)
            
            # EMA 200
            df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
            
            return df
        except Exception as e:
            print(f"❌ Erreur {symbol} {timeframe}: {e}")
            return None

    def scan_market(self):
        """Analyse tous les coins de la watchlist"""
        print("\n" + "="*60)
        print(f"🔍 SCAN MARCHÉ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        for symbol in self.watchlist:
            print(f"📊 Analyse {symbol}...")
            data = {}
            
            for tf in self.timeframes:
                df = self.fetch_data(symbol, tf)
                if df is not None:
                    data[tf] = df
                time.sleep(0.2) # Éviter le rate limit
            
            if len(data) == len(self.timeframes):
                signal = self.signal_detector.detect_signals(symbol, data)
                if signal:
                    signal_key = f"{symbol}_{signal['type']}_{datetime.now().strftime('%Y%m%d')}"
                    if signal_key not in self.sent_signals:
                        self.notifier.send_signal(signal)
                        self.sent_signals[signal_key] = True
                        print(f"🚀 SIGNAL DÉTECTÉ: {symbol}")
            else:
                print(f"⚠️ Données insuffisantes pour {symbol}")
            
            time.sleep(0.5)

    def run_scheduled_scan(self):
        try:
            self.scan_market()
        except Exception as e:
            print(f"❌ Erreur lors du scan: {e}")
            try:
                self.notifier.send_error(str(e))
            except:
                pass
    
    def start(self):
        print("\n" + "="*60)
        print("🤖 DÉMARRAGE DU BOT CRYPTO (PROXY ACTIF)")
        print("="*60)
        
        self.run_scheduled_scan()
        schedule.every(30).minutes.do(self.run_scheduled_scan)
        
        print("\n✅ Bot en mode surveillance 24/7")
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    if not os.getenv('TELEGRAM_BOT_TOKEN') or not os.getenv('TELEGRAM_CHAT_ID'):
        print("❌ ERREUR: Variables Telegram manquantes dans Railway")
        return
    
    bot = CryptoTradingBot()
    bot.start()

if __name__ == "__main__":
    main()
