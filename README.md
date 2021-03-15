# Joadia

### Gym Interface
Joadia has an OpenAI Gym interface (core/gym.py) that can be used to implement learning agents. Examples of several 
different agents are provided in 'ai/gym_ai.py'.

#### Training and Evaluating Agents
The script 'run_gym.py' provides an example of how the interface can be used to train and evaluate an agent on Joadia.

Various run parameters can be set in the constructor of the ExperimentRunner class, including parameters relating to
both the scenario and learning agent.

One special parameter of note is the 'actionable_entities'. Any entities that are included in this list will be
considered part of the learning problem and the number of decisions that a learning agent must make over the course of
a game will be based on this 'actionable_entities' list. Any entities that are part of 'all_entities' but NOT part of
'actionable_entities' will be automatically controlled through support heuristics, which are described in the following
section.

#### Support Heuristics
The full game of Joadia has very large action and observation spaces. To make it feasible to train agents to play
Joadia in a reasonable amount of time, various parts of the action and observation spaces are simplified through the 
use of support heuristics. 

These support heuristics include performing the following actions automatically:
- Performing appropriate airdrops with the C130 on turns 1-2
- Evacuating civilians with the C130 on turns 3-7
- Loading an appropriate number of supplies when leaving a FOB with MotCoys and OPVs.
- Unloading the maximum number of supplies when arriving at a non-FOB with MotCoys and OPVs.
- Loading the maximum number of civilians when leaving a non-FOB with MotCoys, OPVs and the MRH.
- Unloading the maximum number of civilians when arriving at a FOB with MotCoys, OPVs and the MRH.
- Moving MotCoys, OPVs and the MRH back to a FOB on every even turn.

These support heuristics are based on known strategies for playing Joadia, discovered through human analysis of the
game combined with the use of hill climbing optimisation. Although these support heuristics assist in forming good
strategies for playing Joadia, by themselves they do not lead to optimal play.

In future work, it is possible to turn off any support heuristic and extend the Joadia action and observation spaces
accordingly. This will make the problem computationally harder, but will mean that a larger part of the full
Joadia problem is being explored and learnt by the agent.
