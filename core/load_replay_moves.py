
class LoadedReplay():
    def __init__(self, parent_app, replay):
        self.parent = parent_app
        self.engine = self.parent.engine
        self.turns = []
        self.phase2num = {'DAWN': 0, 'DAY': 1, 'DUSK': 2, 'NIGHT': 3}
        self.num2phase = ['DAWN', 'DAY', 'DUSK', 'NIGHT']
        self.current_turn = 1
        self.current_phase = 0
        self.current_move = 0

        for turn_num in replay:
            if turn_num == '0':
                continue
            turn_phases = replay[turn_num]
            self.turns.append(ReplayTurn(turn_num, turn_phases))

    def reset(self):
        self.turns.clear()
        self.current_turn = 1
        self.current_phase = 0
        self.current_move = 0

    def num_turns(self):
        return len(self.turns)
        
    def available_phases(self, turn_num):
        return self.turns[turn_num].available_phases()

    def current_turn_num(self):
        return self.current_turn

    def current_phase_name(self):
        return self.num2phase[self.current_phase]
    
    
    def step_phase(self):
        if self.current_turn - 1 >= len(self.turns):
            print("Replay data end")
        else:
            replay_turn = self.turns[self.current_turn - 1]
            if self.current_phase >= len(replay_turn.phases):
                self._goto_next_phase()
            else:
                replay_phase = replay_turn.phases[self.current_phase]
            
                if self.current_move >= len(replay_phase.moves):
                    self._goto_next_phase()
                else:
                    #similar to the algorithm below but we play through all the
                    #moves in a phase instead of just one move
                    while self.current_move < len(replay_phase.moves):
                        replay_move = replay_phase.moves[self.current_move].get_move()
                        print(replay_move)
                        self.engine.current_player.execute_move(replay_move[0], replay_move[1], replay_move[2])
                        self.current_move += 1
            
    def step_move(self):
        if self.current_turn - 1 >= len(self.turns):
            print("Replay data end")
        else:
            replay_turn = self.turns[self.current_turn - 1]
            if self.current_phase >= len(replay_turn.phases):
                self._goto_next_phase()
            else:
                replay_phase = replay_turn.phases[self.current_phase]
            
                if self.current_move >= len(replay_phase.moves):
                    self._goto_next_phase()
                else:
                    replay_move = replay_phase.moves[self.current_move].get_move()
                    print(replay_move)
                    self.engine.current_player.execute_move(replay_move[0], replay_move[1], replay_move[2])
                    self.current_move += 1
            
            
    def _goto_next_phase(self):
        self.engine.current_player.phase_done = True
        self.engine.next_phase()
        self.current_phase = self.phase2num[self.engine.game.phase]
        self.current_turn = self.engine.game.turn_num
        self.current_move = 0
                
    def go_to(self, turn_num, phase):
        #TODO: call execute_move() up until turn_num and phase
        return


class ReplayTurn():
    def __init__(self, turn_num, turn_phases):
        self.number = turn_num
        self.phases = []

        for phase_name in turn_phases:
            phase_moves = turn_phases[phase_name]
            self.phases.append(ReplayPhase(phase_name, phase_moves))

    def reset(self):
        self.phases.clear()

    def num_phases(self):
        return len(self.phases)

    def available_phases(self):
        phase_list = []
        for phase in self.phases:
            phase_list.append(phase.name)


class ReplayPhase():
    def __init__(self, phase_name, phase_moves):
        self.name = phase_name
        self.moves = []

        for move in phase_moves:
            self.moves.append(ReplayMove(move))

    def reset(self):
        self.moves.clear()

    def num_moves(self):
        return len(self.moves)


class ReplayMove():
    def __init__(self, move):
        self.entity_name = move['entity_name']
        self.move_label = move['move_label']
        self.extra = move['extra']

    def get_move(self):
        return [self.entity_name, self.move_label, self.extra]
