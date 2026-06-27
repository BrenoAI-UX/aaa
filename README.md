# Trading Bots - Paper Trading Simulation 🤖📈

Três bots de trading simples implementados em Python com Pandas para backtesting e simulação em papel.

## 📋 Bots Implementados

### 1. **Grid Trading Bot** (`bot_grid.py`)
Coloca ordens em múltiplos níveis de preço, criando um "grid" que captura pequenos movimentos.

**Características:**
- Ordens BUY abaixo do preço atual
- Ordens SELL acima do preço atual
- Recria ordens após execução
- Ideal para mercados lateralizados (ranging)

**Parâmetros:**
```python
bot = GridTradingBot(
    symbol='BTC/USD',
    capital=10000.0,          # Capital inicial
    grid_levels=10,           # Número de níveis
    lower_price=95.0,         # Preço mínimo do grid
    upper_price=105.0         # Preço máximo do grid
)
```

**Saída:**
- Valor do portfólio em tempo real
- PnL em USD e %
- Ordens pendentes
- Histórico de trades com profit/loss

---

### 2. **DCA Bot** (`bot_dca.py`)
Dollar Cost Averaging - Investe uma quantidade fixa em intervalos regulares, reduzindo o impacto da volatilidade.

**Características:**
- Compras automáticas em intervalos regulares
- Insensível a movimentos de curto prazo
- Acumula posição gradualmente
- Ideal para investidores de longo prazo

**Parâmetros:**
```python
bot = DCABot(
    symbol='ETH/USD',
    amount_per_purchase=100.0,  # Valor por compra
    period=DCAPeriod.DAILY,     # Intervalo
    start_date=datetime(2024, 1, 1)
)
```

**Períodos disponíveis:**
- `DCAPeriod.HOURLY` - A cada hora
- `DCAPeriod.DAILY` - Diariamente
- `DCAPeriod.WEEKLY` - Semanalmente
- `DCAPeriod.MONTHLY` - Mensalmente

**Saída:**
- Preço médio de entrada
- Valor total investido
- PnL e retorno %
- Histórico com média acumulada

---

### 3. **Hybrid Grid + DCA Bot** (`bot_hybrid.py`)
Combina Grid Trading com DCA para otimizar tanto as entradas quanto as saídas.

**Características:**
- Grid contínuo para capturar volatilidade
- DCA periódico para acumular em crises
- Adapta-se ao modo de mercado (uptrend/downtrend/ranging)
- DCA mais agressivo em downtrends

**Modos de Operação:**
- 🟢 **UPTREND**: Favorece vendas (>5% de alta)
- 🔴 **DOWNTREND**: Favorece compras DCA acelerado (<-5% de queda)
- 🟡 **RANGING**: Balanceado (volatilidade normal)

**Parâmetros:**
```python
bot = HybridGridDCABot(
    symbol='BTC/USD',
    capital=15000.0,
    grid_levels=8,
    lower_price=95.0,
    upper_price=105.0,
    dca_amount=500.0,         # Valor por DCA
    dca_interval_days=7       # Intervalo DCA
)
```

**Saída:**
- Modo de operação atual
- Contadores separados: Grid buys, Grid sells, DCA buys
- Estatísticas completas de performance
- Histórico de trades com fontes

---

## 🚀 Como Usar

### Instalação
```bash
pip install -r requirements.txt
```

### Exemplo básico
```python
from bot_grid import GridTradingBot
from datetime import datetime

# Criar bot
bot = GridTradingBot(
    symbol='BTC/USD',
    capital=10000.0,
    grid_levels=10,
    lower_price=95.0,
    upper_price=105.0
)

# Criar grid inicial
current_price = 100.0
bot.create_grid_orders(current_price)

# Simular preços
for price in [99.5, 99.0, 100.2, 101.0]:
    trades = bot.process_price(price)
    pnl = bot.get_pnl(price)
    print(f"Preço: ${price} | Portfolio: ${pnl['portfolio_value']:.2f}")

# Obter relatórios
df = bot.get_trades_df()
print(df)
```

### Executar testes
```bash
python bot_grid.py
python bot_dca.py
python bot_hybrid.py
```

---

## 📊 Estrutura de Dados

### GridOrder (Grid Bot)
```python
GridOrder:
  - order_id: ID único
  - price: Preço da ordem
  - quantity: Quantidade
  - side: 'BUY' ou 'SELL'
  - status: 'PENDING', 'FILLED', 'CANCELLED'
  - created_at: Timestamp de criação
  - filled_at: Timestamp de execução
  - filled_price: Preço de execução real
```

### DCAPurchase (DCA Bot)
```python
DCAPurchase:
  - purchase_id: ID único
  - timestamp: Momento da compra
  - amount_usd: Valor investido
  - price: Preço naquele momento
  - quantity: Quantidade comprada
  - total_cost: Custo total
```

### HybridTrade (Hybrid Bot)
```python
HybridTrade:
  - trade_id: ID único
  - timestamp: Momento do trade
  - side: 'BUY' ou 'SELL'
  - price: Preço de execução
  - quantity: Quantidade
  - source: 'GRID' ou 'DCA'
  - portfolio_value: Valor do portfólio no momento
  - pnl: PnL no momento
```

---

## 📈 Métricas Principales

### PnL (Profit and Loss)
```python
pnl = {
    'portfolio_value': Valor total em USD
    'pnl': Lucro/Prejuízo em USD
    'pnl_percentage': Lucro/Prejuízo em %
}
```

### Estatísticas do Grid
```python
stats = {
    'total_trades': Total de trades executados
    'grid_buys': Compras do grid
    'grid_sells': Vendas do grid
    'average_entry_price': Preço médio de entrada
    'coin_holdings': Quantidade de moeda
}
```

---

## 💡 Casos de Uso

| Cenário | Bot Recomendado |
|---------|----------|
| Mercado lateral (20-30% range) | Grid Trading ✅ |
| Longo prazo, média baixa | DCA ✅ |
| Alto risco, compra na queda | Hybrid ✅ |
| Scalping rápido | Grid (ajustado) |
| Acumular durante bear market | DCA + Hybrid |

---

## ⚙️ Configuração Recomendada

### Para iniciantes
```python
# Grid simples
GridTradingBot(capital=5000, grid_levels=5, lower_price=95, upper_price=105)

# DCA conservador
DCABot(amount_per_purchase=100, period=DCAPeriod.WEEKLY)
```

### Para traders intermediários
```python
# Grid mais agressivo
GridTradingBot(capital=10000, grid_levels=10, lower_price=90, upper_price=110)

# DCA + Grid
HybridGridDCABot(capital=15000, grid_levels=8, dca_amount=500, dca_interval_days=7)
```

### Para traders avançados
```python
# Grid fino + DCA agressivo
HybridGridDCABot(
    capital=50000,
    grid_levels=20,
    lower_price=80,
    upper_price=120,
    dca_amount=2000,
    dca_interval_days=3
)
```

---

## 📝 Notas Importantes

⚠️ **Papel Trading**: Este código simula trades em papel. Não executa em exchanges reais.

💰 **Riscos**:
- Grid trading pode deixar sem liquidez em mercados em tendência forte
- DCA é ineficaz se o preço nunca sobe
- Hybrid pode gerar custos de transação altos

✅ **Próximos passos**:
- [ ] Integração com API TradingView (dados reais)
- [ ] Backtesting histórico
- [ ] Análise de fees e slippage
- [ ] Alerts e notificações
- [ ] Dashboard em tempo real

---

## 📚 Referências

- [Grid Trading Strategy](https://www.binance.com/en/blog/en-trading/what-is-grid-trading-and-how-can-it-improve-returns-421499412684900640)
- [Dollar Cost Averaging](https://www.investopedia.com/terms/d/dollarcostaveraging.asp)
- [Pandas Documentation](https://pandas.pydata.org/)

---

**Criado com ❤️ para trading em papel**
