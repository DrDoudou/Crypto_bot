"""
Module de notifications Telegram
Envoie des alertes formatées pour les signaux de trading
"""

import requests
from datetime import datetime

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        """
        Initialise le notifier Telegram
        
        Args:
            bot_token: Token du bot Telegram
            chat_id: ID du chat Telegram
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        if bot_token and chat_id:
            self.send_startup_message()
    
    def send_startup_message(self):
        """Envoie un message de démarrage"""
        message = (
            "🤖 <b>BOT CRYPTO DÉMARRÉ</b>\n\n"
            "✅ Surveillance active 24/7\n"
            "⏰ Scan toutes les 30 minutes\n"
            "🔔 Vous recevrez des alertes pour chaque setup valide\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_message(message)
    
    def send_message(self, message):
        """
        Envoie un message Telegram
        
        Args:
            message: Texte du message
        """
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram non configuré, message non envoyé")
            return
        
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✅ Message Telegram envoyé")
            else:
                print(f"❌ Erreur Telegram: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi Telegram: {e}")
    
    def send_signal(self, signal):
        """
        Formate et envoie un signal de trading
        
        Args:
            signal: Dict contenant les infos du signal
        """
        # Emoji selon le type
        emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
        
        # Calculer le potentiel de gain
        if signal['type'] == 'LONG':
            gain_pct = (signal['take_profit'] - signal['entry_price']) / signal['entry_price'] * 100
        else:
            gain_pct = (signal['entry_price'] - signal['take_profit']) / signal['entry_price'] * 100
        
        # Formater le message
        message = (
            f"{emoji} <b>{signal['type']} SIGNAL</b> {emoji}\n\n"
            f"💎 <b>{signal['symbol']}</b>\n"
            f"⏰ Timeframe: {signal['timeframe']}\n"
            f"📊 Score: {signal['score']}/10\n\n"
            f"💰 <b>PRIX</b>\n"
            f"Entry: {signal['entry_price']}\n"
            f"Stop: {signal['stop_loss']} (-3%)\n"
            f"Target: {signal['take_profit']} (+{gain_pct:.1f}%)\n"
            f"R/R: 1:{signal['risk_reward']}\n\n"
            f"📈 <b>RSI</b>\n"
        )
        
        if signal['rsi_1h']:
            message += f"1h: {signal['rsi_1h']}\n"
        message += f"4h: {signal['rsi_4h']}\n"
        if signal['rsi_1d']:
            message += f"1d: {signal['rsi_1d']}\n"
        
        message += f"\n✅ <b>RAISONS</b>\n"
        for reason in signal['reasons']:
            message += f"• {reason}\n"
        
        message += f"\n⏰ {signal['timestamp']}"
        
        # Ajouter warning si proche FOMC
        message += "\n\n⚠️ <i>FOMC dans 5 jours - Position sizing réduit recommandé</i>"
        
        self.send_message(message)
    
    def send_error(self, error_message):
        """
        Envoie une notification d'erreur
        
        Args:
            error_message: Message d'erreur
        """
        message = (
            f"❌ <b>ERREUR BOT</b>\n\n"
            f"{error_message}\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_message(message)
    
    def send_daily_summary(self, stats):
        """
        Envoie un résumé quotidien
        
        Args:
            stats: Dict avec les statistiques
        """
        message = (
            f"📊 <b>RÉSUMÉ QUOTIDIEN</b>\n\n"
            f"Signaux détectés: {stats.get('total_signals', 0)}\n"
            f"• LONG: {stats.get('long_signals', 0)}\n"
            f"• SHORT: {stats.get('short_signals', 0)}\n\n"
            f"Top coins:\n"
        )
        
        for coin in stats.get('top_coins', [])[:5]:
            message += f"• {coin}\n"
        
        message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_message(message)
