import sys
import os
import time
import random
from collections import Counter
from itertools import combinations
from pyfiglet import Figlet

# Constants for the game
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
HAND_RANKINGS = {
    9: "Royal Flush",
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "Pair",
    0: "High Card"
}

f1 = Figlet(font='contessa')
clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.rank_value = RANKS.index(rank)
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return self.__str__()

class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        self.shuffle()
        
    def shuffle(self):
        random.shuffle(self.cards)
        
    def deal(self, count=1):
        if count > len(self.cards):
            return None
        cards = self.cards[:count]
        self.cards = self.cards[count:]
        return cards if count > 1 else cards[0]

class Player:
    def __init__(self, name, chips=1000, is_ai=False):
        self.name = name
        self.chips = chips
        self.hand = []
        self.is_active = True
        self.is_ai = is_ai
        self.current_bet = 0
        
    def add_cards(self, cards):
        if isinstance(cards, list):
            self.hand.extend(cards)
        else:
            self.hand.append(cards)
            
    def clear_hand(self):
        self.hand = []
        self.current_bet = 0
        self.is_active = True
    
    def place_bet(self, amount):
        if amount > self.chips:
            amount = self.chips
        self.chips -= amount
        self.current_bet += amount
        return amount
    
    def fold(self):
        self.is_active = False
        
    def __str__(self):
        return f"{self.name} ({self.chips} chips)"

# Hand evaluation functions
def evaluate_hand(cards):
    """Evaluate the best 5-card poker hand from the given cards.
    Returns a tuple (hand_rank, tie_breakers)"""
    
    if len(cards) < 5:
        return (0, [card.rank_value for card in sorted(cards, key=lambda c: c.rank_value, reverse=True)])
    
    # Get all 5-card combinations if more than 5 cards
    if len(cards) > 5:
        all_combinations = combinations(cards, 5)
        return max((evaluate_hand(list(combo)) for combo in all_combinations), key=lambda x: (x[0], x[1]))
    
    ranks = [card.rank_value for card in cards]
    suits = [card.suit for card in cards]
    
    # Check for flush
    is_flush = len(set(suits)) == 1
    
    # Check for straight
    rank_count = Counter(ranks)
    rank_values = sorted(set(ranks))
    
    # Handle Ace as low
    if set(rank_values) == {0, 9, 10, 11, 12}:  # A, 10, J, Q, K
        is_straight = True
        straight_high = 12  # Ace high
    else:
        # Regular straight check
        is_straight = (len(rank_values) == 5 and (max(rank_values) - min(rank_values) == 4))
        straight_high = max(rank_values) if is_straight else 0
    
    # Royal flush
    if is_flush and set(ranks) == {8, 9, 10, 11, 12}:  # 10, J, Q, K, A
        return (9, [])
    
    # Straight flush
    if is_flush and is_straight:
        return (8, [straight_high])
    
    # Four of a kind
    if 4 in rank_count.values():
        four_rank = [r for r, count in rank_count.items() if count == 4][0]
        kicker = [r for r in ranks if r != four_rank][0]
        return (7, [four_rank, kicker])
    
    # Full house
    if 3 in rank_count.values() and 2 in rank_count.values():
        three_rank = [r for r, count in rank_count.items() if count == 3][0]
        two_rank = [r for r, count in rank_count.items() if count == 2][0]
        return (6, [three_rank, two_rank])
    
    # Flush
    if is_flush:
        return (5, sorted(ranks, reverse=True))
    
    # Straight
    if is_straight:
        return (4, [straight_high])
    
    # Three of a kind
    if 3 in rank_count.values():
        three_rank = [r for r, count in rank_count.items() if count == 3][0]
        kickers = sorted([r for r in ranks if r != three_rank], reverse=True)
        return (3, [three_rank] + kickers)
    
    # Two pair
    if list(rank_count.values()).count(2) == 2:
        pairs = sorted([r for r, count in rank_count.items() if count == 2], reverse=True)
        kicker = [r for r in ranks if rank_count[r] == 1][0]
        return (2, pairs + [kicker])
    
    # Pair
    if 2 in rank_count.values():
        pair_rank = [r for r, count in rank_count.items() if count == 2][0]
        kickers = sorted([r for r in ranks if r != pair_rank], reverse=True)
        return (1, [pair_rank] + kickers)
    
    # High card
    return (0, sorted(ranks, reverse=True))

def calculate_win_probability(player_hand, community_cards, num_players, iterations=1000):
    """
    Calculate the probability of winning using Monte Carlo simulation.
    Returns win probability as a percentage.
    """
    wins = 0
    
    # Create a new deck without the known cards
    all_known_cards = player_hand + community_cards
    available_cards = [Card(rank, suit) for suit in SUITS for rank in RANKS 
                      if not any(card.rank == rank and card.suit == suit for card in all_known_cards)]
    
    for _ in range(iterations):
        # Shuffle the available cards
        random.shuffle(available_cards)
        
        # Complete the community cards if needed
        remaining_community = 5 - len(community_cards)
        simulated_community = community_cards + available_cards[:remaining_community]
        
        # Deal cards to opponents
        idx = remaining_community
        opponent_hands = []
        for _ in range(num_players - 1):
            opponent_hands.append(available_cards[idx:idx+2])
            idx += 2
            
        # Evaluate player's hand
        player_score = evaluate_hand(player_hand + simulated_community)
        
        # Check if player wins
        player_wins = True
        for opp_hand in opponent_hands:
            opp_score = evaluate_hand(opp_hand + simulated_community)
            if opp_score > player_score:
                player_wins = False
                break
        
        if player_wins:
            wins += 1
    
    return (wins / iterations) * 100

class PokerGame:
    def __init__(self, num_players=4, small_blind=5, big_blind=10):
        self.num_players = num_players
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.players = []
        self.deck = None
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_idx = 0
        self.current_player_idx = 0
        self.setup_game()
    
    def setup_game(self):
        # Create human player
        human_name = input("Enter your name: ")
        self.players.append(Player(human_name))
        
        # Create AI players
        for i in range(1, self.num_players):
            self.players.append(Player(f"AI-{i}", is_ai=True))
        
        print(f"Welcome to Poker! Players: {', '.join(str(p) for p in self.players)}")
    
    def start_new_round(self):
        """Start a new round of poker"""
        clear()
        print(f1.renderText("New Round"))
        time.sleep(1)
        
        # Reset game state
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        
        # Reset players' hands and states
        for player in self.players:
            player.clear_hand()
        
        # Remove players with no chips
        self.players = [p for p in self.players if p.chips > 0]
        
        # If only one player remains, they're the winner
        if len(self.players) == 1:
            print(f"{self.players[0].name} is the last player standing! Game over.")
            return False
        
        # Rotate dealer position
        self.dealer_idx = (self.dealer_idx + 1) % len(self.players)
        print(f"{self.players[self.dealer_idx].name} is the dealer.")
        
        # Deal cards
        for _ in range(2):
            for player in self.players:
                player.add_cards(self.deck.deal())
        
        # Blinds
        sb_idx = (self.dealer_idx + 1) % len(self.players)
        bb_idx = (self.dealer_idx + 2) % len(self.players)
        
        sb = self.players[sb_idx].place_bet(self.small_blind)
        bb = self.players[bb_idx].place_bet(self.big_blind)
        
        self.pot += sb + bb
        self.current_bet = self.big_blind
        
        print(f"{self.players[sb_idx].name} posts small blind: {self.small_blind}")
        print(f"{self.players[bb_idx].name} posts big blind: {self.big_blind}")
        
        # Set starting player (after big blind)
        self.current_player_idx = (bb_idx + 1) % len(self.players)
        
        return True
    
    def display_game_state(self, show_all=False):
        """Display the current game state"""
        clear()
        print(f"\nPot: {self.pot} chips  |  Current bet: {self.current_bet}")
        
        # Show community cards
        if self.community_cards:
            print("\nCommunity cards:", ' '.join(str(card) for card in self.community_cards))
        else:
            print("\nCommunity cards: None")
        
        # Show player info
        print("\nPlayers:")
        for i, player in enumerate(self.players):
            marker = "👉 " if i == self.current_player_idx else "   "
            hand_str = ' '.join(str(card) for card in player.hand) if show_all or not player.is_ai else "** **"
            active_str = "" if player.is_active else "(folded)"
            bet_str = f"Bet: {player.current_bet}" if player.current_bet > 0 else ""
            print(f"{marker}{player.name}: {player.chips} chips | {hand_str} {active_str} {bet_str}")
    
    def betting_round(self, round_name):
        """Handle a round of betting"""
        print(f"\n--- {round_name} Betting Round ---")
        
        # Count active players
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) <= 1:
            return False
        
        # Start with current player
        player_idx = self.current_player_idx
        last_raiser = None
        betting_complete = False
        
        while not betting_complete:
            current_player = self.players[player_idx]
            
            # Skip inactive players
            if not current_player.is_active:
                player_idx = (player_idx + 1) % len(self.players)
                continue
            
            # Check if betting round is complete
            if last_raiser == player_idx:
                betting_complete = True
                break
            
            # Set last_raiser if it's None initially
            if last_raiser is None:
                last_raiser = player_idx
            
            # Handle player decision
            self.current_player_idx = player_idx
            self.display_game_state()
            
            amount_to_call = self.current_bet - current_player.current_bet
            
            # Calculate win probability for human player
            if not current_player.is_ai:
                win_prob = calculate_win_probability(
                    current_player.hand, 
                    self.community_cards, 
                    len(active_players)
                )
                print(f"\n🔹 Win probability: {win_prob:.1f}%")
                print(f"🔹 Current hand: {HAND_RANKINGS[evaluate_hand(current_player.hand + self.community_cards)[0]]}")
            
            if current_player.is_ai:
                action = self.ai_decision(current_player, amount_to_call)
            else:
                action = self.human_decision(current_player, amount_to_call)
            
            # Process action
            if action == "fold":
                current_player.fold()
                print(f"{current_player.name} folds.")
                
                # Check if only one player remains
                active_players = [p for p in self.players if p.is_active]
                if len(active_players) == 1:
                    return False
                    
            elif action.startswith("call"):
                bet_amount = amount_to_call
                bet = current_player.place_bet(bet_amount)
                self.pot += bet
                print(f"{current_player.name} calls {bet_amount}.")
                
            elif action.startswith("check"):
                print(f"{current_player.name} checks.")
                
            elif action.startswith("raise"):
                amount = int(action.split()[1])
                raise_amount = amount_to_call + amount
                bet = current_player.place_bet(raise_amount)
                self.pot += bet
                self.current_bet = current_player.current_bet
                last_raiser = player_idx  # Update the last raiser
                print(f"{current_player.name} raises by {amount} to {self.current_bet}.")
            
            # Move to next player
            player_idx = (player_idx + 1) % len(self.players)
            
        # Update current player for next round
        self.current_player_idx = (self.dealer_idx + 1) % len(self.players)
        return True
    
    def human_decision(self, player, amount_to_call):
        """Get decision from human player"""
        options = []
        
        if amount_to_call == 0:
            options.append("check")
            options.append("raise [amount]")
        else:
            options.append(f"fold")
            
            if player.chips >= amount_to_call:
                options.append(f"call {amount_to_call}")
            
            if player.chips > amount_to_call:
                options.append("raise [amount]")
        
        while True:
            print("\nOptions:", " | ".join(options))
            decision = input(f"{player.name}, your action: ").lower().strip()
            
            if decision == "fold" and "fold" in options:
                return "fold"
            elif decision == "check" and "check" in options:
                return "check"
            elif decision == f"call {amount_to_call}" and f"call {amount_to_call}" in options:
                return "call"
            elif decision.startswith("raise ") and "raise [amount]" in options:
                try:
                    amount = int(decision.split()[1])
                    if amount > 0 and player.chips >= amount_to_call + amount:
                        return f"raise {amount}"
                    else:
                        print("Invalid raise amount.")
                except (IndexError, ValueError):
                    print("Invalid raise format. Use 'raise [amount]'")
            else:
                print("Invalid option. Try again.")
    
    def ai_decision(self, player, amount_to_call):
        """AI player decision making"""
        # Calculate hand strength
        hand_rank, _ = evaluate_hand(player.hand + self.community_cards)
        
        # Basic AI strategy based on hand strength and community cards
        if len(self.community_cards) == 0:  # Pre-flop
            if hand_rank >= 1 or (player.hand[0].rank_value > 9 and player.hand[1].rank_value > 9):
                # Good starting hand
                if amount_to_call == 0:
                    raise_amount = min(player.chips, self.big_blind * 2)
                    return f"raise {raise_amount}"
                elif amount_to_call <= self.big_blind * 3:
                    return "call"
                else:
                    return "fold"
            else:
                # Weak starting hand
                if amount_to_call == 0:
                    return "check"
                elif amount_to_call <= self.big_blind:
                    return "call"
                else:
                    return "fold"
        else:
            # Post-flop strategy
            if hand_rank >= 3:  # Three of a kind or better
                if random.random() < 0.7:  # 70% chance to raise
                    raise_amount = min(player.chips, self.pot // 2)
                    return f"raise {max(self.big_blind, raise_amount)}"
                else:
                    return "call" if amount_to_call > 0 else "check"
            elif hand_rank >= 1:  # Pair or two pair
                if amount_to_call == 0:
                    if random.random() < 0.3:  # 30% chance to raise
                        return f"raise {self.big_blind * 2}"
                    else:
                        return "check"
                elif amount_to_call <= self.big_blind * 3:
                    return "call"
                else:
                    return "fold"
            else:  # High card
                if amount_to_call == 0:
                    return "check"
                elif amount_to_call <= self.big_blind:
                    if random.random() < 0.3:  # Bluff 30% of the time
                        return "call"
                    else:
                        return "fold"
                else:
                    return "fold"
        
    def determine_winners(self):
        """Determine winners and distribute pot"""
        active_players = [p for p in self.players if p.is_active]
        
        # If only one active player, they win
        if len(active_players) == 1:
            winner = active_players[0]
            winner.chips += self.pot
            print(f"\n{winner.name} wins {self.pot} chips!")
            return
        
        # Evaluate hands and find winner(s)
        player_scores = []
        for player in active_players:
            score = evaluate_hand(player.hand + self.community_cards)
            player_scores.append((player, score))
        
        # Sort by score (hand rank and tie breakers)
        player_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Find winners (players with the same highest score)
        winners = [player_scores[0][0]]
        for i in range(1, len(player_scores)):
            if player_scores[i][1] == player_scores[0][1]:
                winners.append(player_scores[i][0])
            else:
                break
        
        # Split pot among winners
        split_amount = self.pot // len(winners)
        remainder = self.pot % len(winners)
        
        for winner in winners:
            winner.chips += split_amount
        
        # Give remainder to the first winner (closest to dealer)
        if remainder > 0:
            winners[0].chips += remainder
        
        # Show winners and their hands
        print("\nShowdown!")
        for player, score in player_scores:
            hand_name = HAND_RANKINGS[score[0]]
            print(f"{player.name}: {' '.join(str(c) for c in player.hand)} - {hand_name}")
        
        if len(winners) == 1:
            print(f"\n{winners[0].name} wins {self.pot} chips with {HAND_RANKINGS[player_scores[0][1][0]]}!")
        else:
            winner_names = ", ".join(w.name for w in winners)
            print(f"\nSplit pot! {winner_names} each win {split_amount} chips with {HAND_RANKINGS[player_scores[0][1][0]]}!")
    
    def play_round(self):
        """Play a complete round of poker"""
        if not self.start_new_round():
            return False
        
        # Pre-flop
        if not self.betting_round("Pre-flop"):
            self.determine_winners()
            return True
        
        # Flop
        self.community_cards.extend(self.deck.deal(3))
        if not self.betting_round("Flop"):
            self.determine_winners()
            return True
        
        # Turn
        self.community_cards.append(self.deck.deal())
        if not self.betting_round("Turn"):
            self.determine_winners()
            return True
        
        # River
        self.community_cards.append(self.deck.deal())
        if not self.betting_round("River"):
            self.determine_winners()
            return True
        
        # Showdown
        self.display_game_state(show_all=True)
        self.determine_winners()
        return True
    
    def play_game(self):
        """Main game loop"""
        while True:
            if not self.play_round():
                break
            
            # Ask to continue
            human_players = [p for p in self.players if not p.is_ai and p.chips > 0]
            if not human_players:
                print("You're out of chips! Game over.")
                break
                
            play_again = input("\nPlay another round? (y/n): ").lower()
            if play_again != 'y':
                break
        
        print("\nFinal chips:")
        for player in sorted(self.players, key=lambda p: p.chips, reverse=True):
            print(f"{player.name}: {player.chips}")
        
        print("\nThanks for playing!")

if __name__ == '__main__':
    print(f1.renderText("QuickSand Poker"))
    print("Welcome to QuickSand Poker - poker with live win probabilities!")
    time.sleep(2)
    clear()
    
    game = PokerGame()
    game.play_game()

