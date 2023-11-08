import random

import numpy as np


class Player:
    def __init__(self, player_id, model=None):
        self.player_id = player_id
        self.role = None  # This will be 'Liberal', 'Fascist', or 'Hitler'
        self.is_hitler = False
        self.is_alive = True
        self.veto_power = False
        self.investigated_players = set()  # Track investigated players
        self.model = model  # The trained model

    def preprocess_state(self, game_state):
        """
        Convert the game state into a numerical format that the model can process.
        """
        # Example features - these should be aligned with how the model was trained
        features = []

        # Encode the number of enacted policies as a fraction of total policies
        features.append(game_state.enacted_liberal_policies / 6)
        features.append(game_state.enacted_fascist_policies / 11)

        # Encode the election tracker
        features.append(game_state.failed_elections_count / 3)

        # Encode player alive status (1 for alive, 0 for dead)
        features.extend([1 if is_alive else 0 for is_alive in game_state.alive_players])

        # Encode veto power active status
        features.append(1 if game_state.veto_power_active else 0)

        # Encode known policy deck composition
        total_policies = game_state.known_policy_deck['Liberal'] + game_state.known_policy_deck['Fascist']
        features.append(game_state.known_policy_deck['Liberal'] / total_policies)
        features.append(game_state.known_policy_deck['Fascist'] / total_policies)

        # One-hot encode player roles if known (AI's own role would be known)
        roles_encoded = [0] * 3  # Assuming the order is [Liberal, Fascist, Hitler]
        if self.role == 'Liberal':
            roles_encoded[0] = 1
        elif self.role == 'Fascist':
            roles_encoded[1] = 1
        elif self.role == 'Hitler':
            roles_encoded[2] = 1
        features.extend(roles_encoded)

        # Normalize and convert to numpy array
        normalized_features = np.array(features, dtype=np.float32)

        return normalized_features

    def postprocess_action(self, predicted_action, possible_actions):
        """
        Convert the model's output into an executable action in the game.
        """
        # If the model outputs a discrete action index, map it to an action
        if isinstance(predicted_action, int):
            action = possible_actions[predicted_action]
        # If the model outputs a probability distribution, sample an action
        elif isinstance(predicted_action, np.ndarray):
            action_idx = np.random.choice(len(possible_actions), p=predicted_action)
            action = possible_actions[action_idx]
        else:
            raise ValueError("Model output format not recognized")

        return action

    def make_decision(self, game_state):
        if not self.model:
            # Fall back to random decision making if no model is provided
            return random.choice(self.possible_actions(game_state))

        preprocessed_state = self.preprocess_state(game_state)
        predicted_action = self.model.predict(preprocessed_state)
        return self.postprocess_action(predicted_action)

    def vote(self, president, chancellor):
        # Placeholder for player voting logic. This could be a random vote or based on AI strategy.
        # In a real game, you'd collect input from the player or AI decision-making process.
        # For example:
        return 'Yes' if random.choice([True, False]) else 'No'

    def discard_policy(self, drawn_policies):
        # This method should remove and return exactly one policy from the drawn_policies list.
        policy_to_discard = random.choice(drawn_policies)
        drawn_policies.remove(policy_to_discard)  # This will remove only the first occurrence of the policy_to_discard
        return policy_to_discard

    def enact_policy(self, remaining_policies):
        # Placeholder for player policy enacting logic.
        # The player should enact one policy from the remaining_policies.
        # For simplicity, randomly choose one to enact for now.
        return random.choice(remaining_policies)

    def choose_player_to_investigate(self, players):
        # Exclude self and already investigated players from the list of investigable players
        investigable_players = [p for p in players if p.player_id != self.player_id and p.is_alive and p.player_id not in self.investigated_players]
        player_to_investigate = random.choice(investigable_players)
        self.investigated_players.add(player_to_investigate.player_id)  # Mark this player as investigated
        return player_to_investigate

    def investigate_player(self, player_to_investigate):
        # Print party membership for the player being investigated
        # In an AI, this information would update the AI's knowledge base
        if player_to_investigate.is_alive:
            party = player_to_investigate.role
            print(f"Player {self.player_id} investigates Player {player_to_investigate.player_id} and discovers they are a {party}.")

    def pick_next_president(self, players):
        # Placeholder for logic to pick the next President.
        # This would only be used by the President after certain fascist policies are enacted.
        # For simplicity, choose a random player.
        return random.choice(players)

    def choose_player_to_kill(self, players):
        # Placeholder for logic to choose a player to kill.
        # This would only be used by the President after certain fascist policies are enacted.
        # For simplicity, choose a random player.
        return random.choice(players)

    def use_veto_power(self):
        # Placeholder for logic to use veto power.
        # This would only be used by the Chancellor after the fifth fascist policy is enacted.
        # For simplicity, randomly decide whether to use it or not.
        return random.choice([True, False])

    def possible_actions(self, game_state):
        """
        Determine the possible actions for a player based on the current game state.
        This method returns a list of actions that the AI can choose from.
        """
        actions = []

        if game_state.phase == 'Election':
            # If the player is the president, nominate a chancellor
            if game_state.current_president == self.player_id:
                for player_id in range(game_state.num_players):
                    if game_state.is_eligible_for_chancellor(player_id):
                        actions.append(('Nominate', player_id))

            # All players vote on the proposed government
            actions.append(('Vote', 'Yes'))
            actions.append(('Vote', 'No'))

        if game_state.phase == 'Legislative':
            # If the player is the president, discard a policy
            if game_state.current_president == self.player_id:
                actions.extend([('Discard', policy) for policy in game_state.drawn_policies])

            # If the player is the chancellor, enact a policy
            if game_state.current_chancellor == self.player_id:
                actions.extend([('Enact', policy) for policy in game_state.remaining_policies])

            # If veto power is active, the chancellor may veto the agenda
            if self.veto_power and game_state.current_chancellor == self.player_id:
                actions.append(('Veto',))

        if game_state.phase == 'Executive':
            # President investigates a player, calls a special election, or chooses a player to kill
            if game_state.current_president == self.player_id:
                if game_state.fascist_policies_enacted in [2, 3]:  # Investigate or call special election
                    for player_id in range(game_state.num_players):
                        if player_id not in self.investigated_players:
                            actions.append(('Investigate', player_id))

                if game_state.fascist_policies_enacted in [4, 5]:  # Kill a player
                    for player_id in range(game_state.num_players):
                        if game_state.is_player_alive(player_id):
                            actions.append(('Kill', player_id))

        return actions
