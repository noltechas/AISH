import random

from GameState import GameState
from Player import Player


class SecretHitlerGame:
    def __init__(self, num_players=7):
        self.hitler_assassinated = False
        self.discarded_policies = []
        self.policy_deck = []
        self.president = None
        self.chancellor = None
        self.num_players = num_players
        self.players = []
        self.fascist_policies_enacted = 0
        self.liberal_policies_enacted = 0
        self.election_tracker = 0
        self.game_ended = False  # Add a game state flag
        self.state = GameState(num_players)  # Create an instance of GameState
        self.initialize_game()

    def initialize_game(self):
        self.state = GameState(self.num_players)  # Re-initialize GameState
        roles = ['Liberal'] * 4 + ['Fascist'] * 2 + ['Hitler']
        random.shuffle(roles)

        for i in range(self.num_players):
            player = Player(i)
            player.role = roles[i]
            player.is_hitler = (roles[i] == 'Hitler')
            player.is_alive = True
            self.players.append(player)

        self.policy_deck = ['Liberal'] * 6 + ['Fascist'] * 11
        random.shuffle(self.policy_deck)

    def reshuffle_policy_deck(self):
        # This should only be called when the policy_deck has fewer than 3 cards
        print(f"Reshuffling the policy deck with discarded policies: {self.discarded_policies}")  # Debug print
        if not self.discarded_policies:
            print("Warning: Attempted to reshuffle with no discarded policies.")
        self.policy_deck.extend(self.discarded_policies)
        random.shuffle(self.policy_deck)
        self.discarded_policies = []

    def start_game(self):
        while not self.game_ended:  # Check the game state flag instead of self.is_game_over()
            self.conduct_election()
            if self.president and self.chancellor and not self.game_ended:  # Check the flag here too
                enacted_policy = self.execute_legislative_session()
                if enacted_policy:
                    self.execute_executive_action(enacted_policy)

    def is_game_over(self):
        if self.liberal_policies_enacted >= 5:
            print("Liberals win by enacting 5 Liberal Policies!")
            self.game_ended = True
            return True
        if self.fascist_policies_enacted >= 6:
            print("Fascists win by enacting 6 Fascist Policies!")
            self.game_ended = True
            return True
        if self.fascist_policies_enacted >= 3 and self.chancellor and self.chancellor.is_hitler:
            print("Fascists win by electing Hitler as Chancellor!")
            self.game_ended = True
            return True
        if self.hitler_assassinated:
            print("Liberals win by assassinating Hitler!")
            self.game_ended = True  # Set the game state flag
            return True
        return False

    def conduct_election(self):
        # Nominate the next Presidential candidate
        self.president = self.get_next_presidential_candidate()

        # The President nominates a Chancellor. This could be random or based on some strategy.
        # For simplicity, we're choosing the next player who isn't the President.
        chancellor_candidates = [p for p in self.players if p != self.president]
        self.chancellor = random.choice(chancellor_candidates)

        # All players vote
        votes = [player.vote(self.president, self.chancellor) for player in self.players]

        # Count the 'Yes' votes
        yes_votes = votes.count('Yes')

        # Check if the majority is in favor
        if yes_votes > self.num_players / 2:
            # Government is elected
            print(
                f"Government elected with President {self.president.player_id} and Chancellor {self.chancellor.player_id}")
            self.election_tracker = 0  # Reset the election tracker
        else:
            # Government is not elected, increment the election tracker
            print("Government not elected.")
            self.election_tracker += 1

            # If the election tracker reaches 3, a policy is enacted automatically
            if self.election_tracker == 3:
                self.enact_policy(self.policy_deck.pop())
                self.election_tracker = 0  # Reset the election tracker

        self.state.update_after_election(self.president.player_id, self.chancellor.player_id, yes_votes > self.num_players / 2)

    def get_next_presidential_candidate(self):
        # This method should return the next player in line to be the Presidential candidate.
        # For simplicity, let's just return the next player in the list.
        current_president_index = self.players.index(self.president) if self.president else -1
        next_president_index = (current_president_index + 1) % self.num_players
        return self.players[next_president_index]

    def execute_legislative_session(self):
        # Make sure you have enough cards to draw
        if len(self.policy_deck) < 3:
            self.reshuffle_policy_deck()

        # Draw three policies
        drawn_policies = [self.policy_deck.pop() for _ in range(3)]

        # President discards one policy
        discarded_policy = self.president.discard_policy(drawn_policies)
        self.discarded_policies.append(discarded_policy)

        # Remaining policies for the Chancellor to enact one
        # After discarding, drawn_policies should have only 2 policies left
        remaining_policies = drawn_policies
        print(f"Remaining policies after discarding: {remaining_policies}")  # Debug print

        if len(remaining_policies) != 2:
            raise Exception(f"Incorrect number of policies for the Chancellor to enact. Expected 2, got {len(remaining_policies)}.")

        # Chancellor enacts one of the two remaining policies
        enacted_policy = self.chancellor.enact_policy(remaining_policies)
        remaining_policies.remove(enacted_policy)
        self.discarded_policies.append(remaining_policies[0])
        print(f"Enacted policy: {enacted_policy}")  # Debug print

        self.enact_policy(enacted_policy)
        self.state.update_after_legislation(enacted_policy)
        return enacted_policy

    def enact_policy(self, policy):
        if policy == 'Liberal':
            self.liberal_policies_enacted += 1
        elif policy == 'Fascist':
            self.fascist_policies_enacted += 1

        # Check if the game has been won after enacting a policy
        self.is_game_over()

    def execute_executive_action(self, policy):
        # Ensure this function is only called after a Fascist policy is enacted
        if policy != 'Fascist':
            return

        # Executive actions based on the number of Fascist policies enacted
        if self.fascist_policies_enacted == 2:
            player_to_investigate = self.president.choose_player_to_investigate(self.players)
            result = self.president.investigate_player(player_to_investigate)
            self.state.update_after_investigation(self.president.player_id, player_to_investigate.player_id, result)

        elif self.fascist_policies_enacted == 3:
            # For the third Fascist policy, the President picks the next Presidential candidate
            self.president.pick_next_president(self.players)

        elif self.fascist_policies_enacted == 4 or self.fascist_policies_enacted == 5:
            # For the fourth and fifth Fascist policies, the President must kill a player
            player_to_kill = self.president.choose_player_to_kill(self.players)
            self.kill_player(player_to_kill)
            if player_to_kill.is_hitler:
                self.hitler_assassinated = True  # Game will end

        # Some actions might end the game, so check if the game is still ongoing
        if self.is_game_over():
            self.end_game()

    def end_game(self):
        # Log the end state of the game for analysis
        winner = 'Liberals' if self.liberal_policies_enacted >= 5 or self.hitler_assassinated else 'Fascists'
        print(f"Game over. The {winner} have won.")

        # Collect data from the game
        game_data = {
            'winner': winner,
            'liberal_policies': self.liberal_policies_enacted,
            'fascist_policies': self.fascist_policies_enacted,
            'hitler_assassinated': self.hitler_assassinated,
            # Include other relevant metrics here
        }
        self.collect_data(game_data)

        # Reset the game state to play again
        self.reset_game_state()

    def collect_data(self, game_data):
        # Append the game data to a list, save to a file, or send to a database
        # This will depend on your data storage strategy
        pass

    def reset_game_state(self):
        # Reset all the necessary attributes to their initial state
        # You might want to keep some historical data for analysis
        self.hitler_assassinated = False
        self.discarded_policies = []
        self.policy_deck = []
        self.president = None
        self.chancellor = None
        self.fascist_policies_enacted = 0
        self.liberal_policies_enacted = 0
        self.election_tracker = 0
        #self.initialize_game()  # Re-initialize the game

    def kill_player(self, player):
        # Marks the player as dead and checks if the player is Hitler
        player.is_alive = False
        if player.is_hitler:
            self.hitler_assassinated = True
        self.state.player_killed(player.player_id)  # Update the game state when a player is killed
