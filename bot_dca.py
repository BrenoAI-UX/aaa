"""
DCA Bot (Dollar Cost Averaging) - Paper Trading
Simula um bot que investe uma quantidade fixa em intervalos regulares
"""

import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum


class DCAPeriod(Enum):
    """Período de compra"""
    HOURLY = timedelta(hours=1)
    DAILY = timedelta(days=1)
    WEEKLY = timedelta(weeks=1)
    MONTHLY = timedelta(days=30)


@dataclass
class DCAPurchase:
    """Representa uma compra DCA"""
    purchase_id: int
    timestamp: datetime
    amount_usd: float
    price: float
    quantity: float
    total_cost: float


class DCABot:
    """Bot de DCA (Dollar Cost Averaging) em papel"""
    
    def __init__(self,
                 symbol: str,
                 amount_per_purchase: float,
                 period: DCAPeriod = DCAPeriod.DAILY,
                 start_date: datetime = None):
        """
        Args:
            symbol: Par de negociação (ex: 'BTC/USD')
            amount_per_purchase: Valor em USD para cada compra
            period: Período entre compras
            start_date: Data de início
        """
        self.symbol = symbol
        self.amount_per_purchase = amount_per_purchase
        self.period = period
        self.start_date = start_date or datetime.now()
        self.last_purchase_time = self.start_date
        
        self.purchases: List[DCAPurchase] = []
        self.purchase_counter = 0
        
        self.portfolio = {
            'USD': 0.0,
            'COIN': 0.0
        }
        
        self.total_invested = 0.0
    
    def should_purchase(self, current_time: datetime) -> bool:
        """Verifica se é hora de fazer uma compra"""
        time_since_last = current_time - self.last_purchase_time
        return time_since_last >= self.period.value
    
    def execute_purchase(self, current_price: float, current_time: datetime) -> DCAPurchase:
        """
        Executa uma compra DCA
        
        Args:
            current_price: Preço atual da moeda
            current_time: Hora atual
            
        Returns:
            DCAPurchase: Objeto com detalhes da compra
        """
        if current_price <= 0:
            raise ValueError("Preço deve ser positivo")
        
        self.purchase_counter += 1
        quantity = self.amount_per_purchase / current_price
        
        purchase = DCAPurchase(
            purchase_id=self.purchase_counter,
            timestamp=current_time,
            amount_usd=self.amount_per_purchase,
            price=current_price,
            quantity=quantity,
            total_cost=self.amount_per_purchase
        )
        
        self.purchases.append(purchase)
        self.portfolio['COIN'] += quantity
        self.total_invested += self.amount_per_purchase
        self.last_purchase_time = current_time
        
        return purchase
    
    def get_portfolio_value(self, current_price: float) -> float:
        """Calcula o valor total do portfólio"""
        return self.portfolio['COIN'] * current_price
    
    def get_average_entry_price(self) -> float:
        """Calcula o preço médio de entrada"""
        if not self.purchases:
            return 0.0
        
        total_quantity = sum(p.quantity for p in self.purchases)
        if total_quantity == 0:
            return 0.0
        
        return self.total_invested / total_quantity
    
    def get_pnl(self, current_price: float) -> Dict:
        """Calcula o PnL"""
        portfolio_value = self.get_portfolio_value(current_price)
        pnl = portfolio_value - self.total_invested
        pnl_percentage = (pnl / self.total_invested * 100) if self.total_invested > 0 else 0
        average_price = self.get_average_entry_price()
        
        return {
            'portfolio_value': portfolio_value,
            'total_invested': self.total_invested,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage,
            'average_entry_price': average_price,
            'current_price': current_price,
            'price_delta': current_price - average_price,
            'coin_holdings': self.portfolio['COIN']
        }
    
    def get_purchases_df(self) -> pd.DataFrame:
        """Retorna histórico de compras como DataFrame"""
        if not self.purchases:
            return pd.DataFrame()
        
        data = [
            {
                'purchase_id': p.purchase_id,
                'timestamp': p.timestamp,
                'price': p.price,
                'quantity': p.quantity,
                'amount_usd': p.amount_usd,
                'cumulative_coin': sum(x.quantity for x in self.purchases[:i+1]),
                'cumulative_invested': sum(x.amount_usd for x in self.purchases[:i+1])
            }
            for i, p in enumerate(self.purchases)
        ]
        
        df = pd.DataFrame(data)
        df['average_price_so_far'] = df['cumulative_invested'] / df['cumulative_coin']
        
        return df
    
    def get_statistics(self, current_price: float) -> Dict:
        """Retorna estatísticas completas do bot"""
        pnl = self.get_pnl(current_price)
        avg_price = self.get_average_entry_price()
        
        return {
            'symbol': self.symbol,
            'total_purchases': len(self.purchases),
            'total_invested': self.total_invested,
            'total_coin_bought': self.portfolio['COIN'],
            'average_entry_price': avg_price,
            'current_price': current_price,
            'portfolio_value': pnl['portfolio_value'],
            'pnl': pnl['pnl'],
            'pnl_percentage': pnl['pnl_percentage'],
            'price_change_from_average': ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
        }


# Exemplo de uso
if __name__ == "__main__":
    # Cria o bot
    bot = DCABot(
        symbol='ETH/USD',
        amount_per_purchase=100.0,
        period=DCAPeriod.DAILY
    )
    
    # Simula compras em diferentes preços
    base_time = datetime(2024, 1, 1)
    prices = [1500, 1480, 1510, 1490, 1520, 1505, 1530, 1500, 1550, 1510]
    
    print(f"DCA Bot - {bot.symbol}")
    print(f"Valor por compra: ${bot.amount_per_purchase}")
    print(f"Período: {bot.period.name}")
    print("=" * 60)
    print()
    
    current_time = base_time
    
    for price in prices:
        if bot.should_purchase(current_time):
            purchase = bot.execute_purchase(price, current_time)
            pnl = bot.get_pnl(price)
            
            print(f"Compra #{purchase.purchase_id} - {purchase.timestamp.strftime('%Y-%m-%d')}")
            print(f"  Preço: ${price:.2f}")
            print(f"  Quantidade: {purchase.quantity:.6f} {bot.symbol.split('/')[0]}")
            print(f"  Preço médio: ${pnl['average_entry_price']:.2f}")
            print(f"  Portfólio: ${pnl['portfolio_value']:.2f}")
            print(f"  PnL: ${pnl['pnl']:.2f} ({pnl['pnl_percentage']:.2f}%)")
            print()
        
        current_time += timedelta(days=1)
    
    # Mostra relatório final
    print("\n=== RELATÓRIO FINAL ===")
    
    current_price = 1600  # Preço final simulado
    stats = bot.get_statistics(current_price)
    
    for key, value in stats.items():
        if isinstance(value, float):
            if 'price' in key.lower() or 'pnl' in key.lower() or 'portfolio' in key.lower():
                print(f"{key}: ${value:.2f}")
            else:
                print(f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")
    
    print("\nHistórico de compras:")
    df = bot.get_purchases_df()
    print(df[['timestamp', 'price', 'quantity', 'average_price_so_far']].to_string(index=False))
