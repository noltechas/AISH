class GameState:
    def __init__(self, num_players):
        self.num_players = num_players
        self.player_roles = ['Unknown'] * num_players  # Roles are hidden except for the AI itself
        self.enacted_liberal_policies = 0
        self.enacted_fascist_policies = 0
        self.failed_elections_count = 0
        self.previous_governments = []  # List of tuples (president, chancellor)
        self.alive_players = [True] * num_players
        self.veto_power_active = False
        self.known_policy_deck = {'Liberal': 6, 'Fascist': 11}  # Initial known policy deck composition
        self.investigation_results = {}  # Dict of player id to 'Liberal' or 'Fascist' if investigated
        self.special_election_called = False
        self.chancellor_eligibility = [True] * num_players
        self.player_actions = []  # List of player actions, can be extended with more details
        self.player_interactions = []  # List of interactions between players
        self.current_president = None
        self.current_chancellor = None
        self.last_government = (None, None)

    def update_roles(self, ai_player_id, ai_role):
        # AI knows its own role
        self.player_roles[ai_player_id] = ai_role

    def update_after_election(self, president_id, chancellor_id, election_succeeded):
        self.previous_governments.append((president_id, chancellor_id, election_succeeded))
        self.last_government = (president_id, chancellor_id)
        if not election_succeeded:
            self.failed_elections_count += 1
        else:
            # Reset failed election count after a successful election
            self.failed_elections_count = 0
            # Update current government
            self.current_president = president_id
            self.current_chancellor = chancellor_id
            # Update eligibility for chancellorship
            self.chancellor_eligibility = [i not in self.last_government for i in range(self.num_players)]

    def update_after_legislation(self, policy_type):
        if policy_type == 'Liberal':
            self.enacted_liberal_policies += 1
            self.known_policy_deck['Liberal'] -= 1
        elif policy_type == 'Fascist':
            self.enacted_fascist_policies += 1
            self.known_policy_deck['Fascist'] -= 1
        # Consider reshuffling if the policy deck is empty

    def update_after_investigation(self, investigator_id, investigated_id, party_membership):
        self.investigation_results[investigated_id] = party_membership

    def update_after_special_election(self, special_president_id):
        self.special_election_called = True
        self.current_president = special_president_id

    def update_veto_power(self, veto_power_state):
        self.veto_power_active = veto_power_state

    def player_killed(self, player_id):
        self.alive_players[player_id] = False

    def update_policy_deck(self, liberal_count, fascist_count):
        self.known_policy_deck['Liberal'] = liberal_count
        self.known_policy_deck['Fascist'] = fascist_count

    def reshuffle_policy_deck(self):
        # Typically the exact composition of the policy deck is unknown
        # but we can reset the count based on total policies minus enacted ones
        total_liberal_policies = 6
        total_fascist_policies = 11
        self.known_policy_deck['Liberal'] = total_liberal_policies - self.enacted_liberal_policies
        self.known_policy_deck['Fascist'] = total_fascist_policies - self.enacted_fascist_policies

    def add_player_action(self, player_id, action):
        self.player_actions.append((player_id, action))

    def add_player_interaction(self, player1_id, player2_id, interaction_type):
        self.player_interactions.append((player1_id, player2_id, interaction_type))

    def calculate_reward(previous_state, current_state, action, outcome):
        """
        Calculate the reward for an action taken by the AI player based on the outcome.

        :param previous_state: GameState object before the action was taken
        :param current_state: GameState object after the action was taken
        :param action: The action that was taken by the AI player
        :param outcome: The outcome of the action (e.g., whether it succeeded)
        :return: The numerical reward for the action taken
        """
        reward = 0

        # Assign a large positive reward for winning the game
        if current_state.game_ended and current_state.winner == 'Liberals' and current_state.player_roles[current_state.ai_player_id] == 'Liberal':
            reward += 100
        elif current_state.game_ended and current_state.winner == 'Fascists' and (current_state.player_roles[current_state.ai_player_id] == 'Fascist' or current_state.player_roles[current_state.ai_player_id] == 'Hitler'):
            reward += 100

        # Assign a large negative reward for losing the game
        if current_state.game_ended and current_state.winner != 'Liberals' and current_state.player_roles[current_state.ai_player_id] == 'Liberal':
            reward -= 100
        elif current_state.game_ended and current_state.winner != 'Fascists' and (current_state.player_roles[current_state.ai_player_id] == 'Fascist' or current_state.player_roles[current_state.ai_player_id] == 'Hitler'):
            reward -= 100

        # Assign intermediate rewards or penalties based on actions taken
        if action[0] == 'Enact' and outcome:
            # Positive reward for enacting a policy of your own faction
            if (action[1] == 'Liberal' and current_state.player_roles[current_state.ai_player_id] == 'Liberal') or \
                    (action[1] == 'Fascist' and (current_state.player_roles[current_state.ai_player_id] == 'Fascist' or current_state.player_roles[current_state.ai_player_id] == 'Hitler')):
                reward += 10
            else:
                reward -= 10

        # Punish the AI for picking actions that are not sensible, like investigating a dead player
        if action[0] == 'Investigate' and not previous_state.alive_players[action[1]]:
            reward -= 20

        # Additional rules can be added based on the intricacies of the game

        return reward
