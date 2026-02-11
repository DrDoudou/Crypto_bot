"""
Module d'analyse crypto via Claude AI
Claude analyse les données et détecte LONGS et SHORTS avec intelligence contextuelle
"""

import anthropic
import json
from datetime import datetime

class ClaudeAnalyst:
    def __init__(self, api_key):
        """
        Initialise l'analyste Claude
        
        Args:
            api_key: Clé API Anthropic
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"  # Sonnet 4 - optimal qualité/coût
        
    def analyze_coin(self, symbol, data_1h, data_4h, data_1d, market_context=None):
        """
        Analyse un coin via Claude AI
        
        Args:
            symbol: Ex: BTC/USDT
            data_1h: DataFrame avec données 1h
            data_4h: DataFrame avec données 4h  
            data_1d: DataFrame avec données 1d
            market_context: Contexte macro optionnel
            
        Returns:
            Dict avec signal ou None
        """
        
        # Préparer les données pour Claude
        analysis_data = self._prepare_analysis_data(
            symbol, data_1h, data_4h, data_1d, market_context
        )
        
        # Créer le prompt pour Claude
        prompt = self._create_analysis_prompt(analysis_data)
        
        try:
            # Appeler Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Peu de créativité, beaucoup de rigueur
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parser la réponse
            response_text = message.content[0].text
            signal = self._parse_claude_response(response_text, symbol)
            
            return signal
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse Claude pour {symbol}: {e}")
            return None
    
    def _prepare_analysis_data(self, symbol, data_1h, data_4h, data_1d, market_context):
        """Prépare les données pour l'analyse"""
        
        def get_recent_candles(df, n=10):
            """Récupère les n dernières bougies"""
            if df is None or len(df) < n:
                return None
            
            recent = df.tail(n)
            candles = []
            for _, row in recent.iterrows():
                candles.append({
                    'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'rsi': float(row['rsi']) if 'rsi' in row else None,
                    'ema_9': float(row['ema_9']) if 'ema_9' in row else None,
                    'ema_200': float(row['ema_200']) if 'ema_200' in row else None,
                })
            return candles
        
        # Récupérer les dernières bougies
        candles_1h = get_recent_candles(data_1h, 20) if data_1h is not None else None
        candles_4h = get_recent_candles(data_4h, 15) if data_4h is not None else None
        candles_1d = get_recent_candles(data_1d, 10) if data_1d is not None else None
        
        # Prix actuel et indicateurs
        latest_4h = data_4h.iloc[-1] if data_4h is not None and len(data_4h) > 0 else None
        
        return {
            'symbol': symbol,
            'current_price': float(latest_4h['close']) if latest_4h is not None else None,
            'current_rsi_4h': float(latest_4h['rsi']) if latest_4h is not None and 'rsi' in latest_4h else None,
            'current_ema200_4h': float(latest_4h['ema_200']) if latest_4h is not None and 'ema_200' in latest_4h else None,
            'candles_1h': candles_1h,
            'candles_4h': candles_4h,
            'candles_1d': candles_1d,
            'market_context': market_context or 'Analyse standard',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _create_analysis_prompt(self, data):
        """Crée le prompt pour Claude"""
        
        prompt = f"""Tu es un trader crypto expert. Analyse les données suivantes et détermine s'il y a un setup de trading valide.

**COIN:** {data['symbol']}
**PRIX ACTUEL:** ${data['current_price']:,.2f}
**DATE:** {data['timestamp']}

**DONNÉES TECHNIQUES:**

**Timeframe 1H (20 dernières bougies):**
```json
{json.dumps(data['candles_1h'][-5:], indent=2) if data['candles_1h'] else 'Indisponible'}
```

**Timeframe 4H (15 dernières bougies):**
```json
{json.dumps(data['candles_4h'][-5:], indent=2) if data['candles_4h'] else 'Indisponible'}
```

**Timeframe 1D (10 dernières bougies):**
```json
{json.dumps(data['candles_1d'][-3:], indent=2) if data['candles_1d'] else 'Indisponible'}
```

**INDICATEURS ACTUELS (4H):**
- RSI: {data['current_rsi_4h']:.1f}
- EMA 200: ${data['current_ema200_4h']:,.2f}
- Distance EMA200: {((data['current_price'] - data['current_ema200_4h']) / data['current_ema200_4h'] * 100):+.1f}%

**CONTEXTE MARCHÉ:**
{data['market_context']}

**TA MISSION:**

Analyse ces données en profondeur et détermine s'il y a un setup LONG ou SHORT valide.

**CRITÈRES D'ANALYSE:**

1. **TENDANCE MACRO** (EMA 200, structure des highs/lows)
2. **PATTERNS TECHNIQUES** (H&S, wedges, flags, triangles)
3. **VOLUME PROFILE** (volume en hausse/baisse, climax)
4. **RSI & DIVERGENCES** (oversold/overbought, divergences)
5. **SUPPORT/RÉSISTANCE** (rejets, cassures)
6. **CONFLUENCE** (combien de facteurs alignés)

**RÈGLES STRICTES:**

❌ **PAS DE LONG SI:**
- Prix > 10% sous EMA 200 ET structure downtrend confirmée
- Falling knife actif (-3%+ par bougie sur 5 bougies)
- Volume rouge massif (selling pressure)

❌ **PAS DE SHORT SI:**
- Prix > 10% au-dessus EMA 200 ET structure uptrend forte
- Rallye violent en cours (+3%+ par bougie)
- Momentum haussier intact

✅ **LONG VALIDE SI:**
- Structure haussière OU rebond depuis support majeur
- Confluence de 3+ facteurs techniques
- R/R minimum 1.5:1

✅ **SHORT VALIDE SI:**
- Structure baissière OU rejet depuis résistance
- Confluence de 3+ facteurs techniques
- R/R minimum 1.5:1

**FORMAT DE RÉPONSE:**

Réponds UNIQUEMENT en JSON valide, rien d'autre:

```json
{{
  "signal": "LONG" ou "SHORT" ou "NOTHING",
  "confidence": 1-10,
  "entry": prix_entrée,
  "stop_loss": prix_stop,
  "take_profit": prix_target,
  "risk_reward": ratio,
  "timeframe": "1h" ou "4h" ou "1d",
  "reasoning": [
    "Raison 1 courte et factuelle",
    "Raison 2 courte et factuelle",
    "Raison 3 courte et factuelle"
  ],
  "context": "1-2 phrases expliquant la situation macro",
  "confluence_factors": 3-7,
  "trade_type": "scalp" ou "swing" ou "position"
}}
```

**Si AUCUN setup valide, retourne:**
```json
{{
  "signal": "NOTHING",
  "reasoning": ["Raison pourquoi pas de signal"]
}}
```

**IMPORTANT:** 
- Sois STRICT et PRUDENT
- Privilégie la QUALITÉ sur la quantité
- Explique ton raisonnement de façon CONCISE
- Pas de signal = OK, c'est souvent la meilleure décision
"""
        
        return prompt
    
    def _parse_claude_response(self, response_text, symbol):
        """Parse la réponse de Claude"""
        
        try:
            # Extraire le JSON de la réponse
            # Claude peut entourer le JSON de ```json ... ```
            response_text = response_text.strip()
            
            # Enlever les markdown code blocks si présents
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            # Parser le JSON
            signal_data = json.loads(response_text.strip())
            
            # Valider et retourner
            if signal_data.get('signal') == 'NOTHING':
                return None
            
            if signal_data.get('signal') not in ['LONG', 'SHORT']:
                return None
            
            # Ajouter le symbol
            signal_data['symbol'] = symbol
            signal_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return signal_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON pour {symbol}: {e}")
            print(f"Réponse brute: {response_text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Erreur parsing réponse pour {symbol}: {e}")
            return None
