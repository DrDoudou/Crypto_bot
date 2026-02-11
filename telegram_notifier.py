"""
Module de notifications Telegram pour signaux Claude AI
Formate les signaux intelligents avec raisonnement détaillé
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
            "🧠 <b>CLAUDE AI ANALYST - DÉMARRÉ</b>\n\n"
            "✅ Analyse IA active 24/7\n"
            "⏰ Scan toutes les 30 minutes\n"
            "🎯 Détection LONG et SHORT\n"
            "💡 Raisonnement contextualisé\n\n"
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
            print("⚠️ Telegram non configuré, message non envoyé")
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
    
    def send_claude_signal(self, signal):
        """
        Formate et envoie un signal analysé par Claude
        
        Args:
            signal: Dict contenant l'analyse de Claude
        """
        # Emoji selon le type
        if signal['signal'] == 'LONG':
            emoji = "🟢"
            color = "GREEN"
        else:  # SHORT
            emoji = "🔴"
            color = "RED"
        
        # Calculer le potentiel
        entry = signal['entry']
        target = signal['take_profit']
        stop = signal['stop_loss']
        
        if signal['signal'] == 'LONG':
            gain_pct = (target - entry) / entry * 100
            loss_pct = (entry - stop) / entry * 100
        else:
            gain_pct = (entry - target) / entry * 100
            loss_pct = (stop - entry) / entry * 100
        
        # Type de trade
        trade_type_emoji = {
            'scalp': '⚡',
            'swing': '📊',
            'position': '🎯'
        }
        type_emoji = trade_type_emoji.get(signal.get('trade_type', 'swing'), '📊')
        
        # Formater le message
        message = (
            f"{emoji} <b>{signal['signal']} SIGNAL</b> {emoji}\n\n"
            f"💎 <b>{signal['symbol']}</b>\n"
            f"⏰ Timeframe: {signal['timeframe']}\n"
            f"🎯 Confidence: {signal['confidence']}/10\n"
            f"{type_emoji} Type: {signal.get('trade_type', 'swing').upper()}\n\n"
            f"💰 <b>PRIX</b>\n"
            f"Entry: ${entry:,.2f}\n"
            f"Stop: ${stop:,.2f} (-{loss_pct:.1f}%)\n"
            f"Target: ${target:,.2f} (+{gain_pct:.1f}%)\n"
            f"R/R: 1:{signal['risk_reward']:.1f}\n\n"
        )
        
        # Confluence
        confluence = signal.get('confluence_factors', 0)
        if confluence >= 5:
            message += f"⭐ <b>CONFLUENCE: {confluence}/7</b> (Excellent)\n\n"
        elif confluence >= 3:
            message += f"✅ <b>CONFLUENCE: {confluence}/7</b> (Bon)\n\n"
        else:
            message += f"⚠️ <b>CONFLUENCE: {confluence}/7</b> (Faible)\n\n"
        
        # Contexte macro
        if 'context' in signal:
            message += f"🌍 <b>CONTEXTE</b>\n{signal['context']}\n\n"
        
        # Raisonnement
        message += f"🧠 <b>ANALYSE CLAUDE</b>\n"
        for i, reason in enumerate(signal['reasoning'], 1):
            message += f"  {i}. {reason}\n"
        
        message += f"\n⏰ {signal['timestamp']}"
        
        # Avertissement si faible confidence
        if signal['confidence'] < 6:
            message += "\n\n⚠️ <i>Confidence modérée - Réduire la taille de position</i>"
        
        self.send_message(message)
    
    def send_daily_summary(self, stats):
        """
        Envoie un résumé quotidien
        
        Args:
            stats: Dict avec les statistiques
        """
        message = (
            f"📊 <b>RÉSUMÉ QUOTIDIEN - CLAUDE AI</b>\n\n"
            f"🔍 Analyses effectuées: {stats.get('total_analyses', 0)}\n"
            f"📡 Signaux détectés: {stats.get('total_signals', 0)}\n"
            f"  • LONG: {stats.get('long_signals', 0)}\n"
            f"  • SHORT: {stats.get('short_signals', 0)}\n\n"
            f"🎯 Confidence moyenne: {stats.get('avg_confidence', 0):.1f}/10\n"
            f"⭐ Confluence moyenne: {stats.get('avg_confluence', 0):.1f}/7\n\n"
            f"💎 Top coins analysés:\n"
        )
        
        for coin in stats.get('top_coins', [])[:5]:
            message += f"  • {coin}\n"
        
        message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
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
    
    def send_no_signals(self, analyzed_count):
        """
        Envoie une notification quand aucun signal n'est détecté
        (Optionnel - peut être désactivé si trop verbeux)
        
        Args:
            analyzed_count: Nombre de coins analysés
        """
        message = (
            f"💤 <b>SCAN TERMINÉ</b>\n\n"
            f"🔍 {analyzed_count} coins analysés\n"
            f"📊 Aucun setup valide détecté\n\n"
            f"✅ Claude reste vigilant\n"
            f"⏰ Prochain scan dans 30 min\n\n"
            f"💡 <i>Pas de signal = Protection du capital</i>"
        )
        self.send_message(message)
