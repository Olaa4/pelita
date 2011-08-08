# -*- coding: utf-8 -*-

""" The controller """

import copy
import random
from pelita.containers import TypeAwareList

from pelita import datamodel
from pelita.viewer import AbstractViewer

__docformat__ = "restructuredtext"

class PlayerTimeout(Exception):
    pass

class PlayerDisconnected(Exception):
    pass

class GameMaster(object):
    """ Controller of player moves and universe updates.

    This object coordinates the moves of the player implementations with the
    updating of the universe.

    Parameters
    ----------
    universe : Universe
        the game state
    game_time : int
        the total permitted number of rounds
    number_bots : int
        the total number of bots
    player_teams : the participating player teams
    player_teams_bots : stores for each player_team index which bots it has
    viewers : list of subclasses of AbstractViewer
        the viewers that are observing this game

    """
    def __init__(self, layout, number_bots, game_time):
        self.universe = datamodel.create_CTFUniverse(layout, number_bots)
        self.game_time = game_time
        self.number_bots = number_bots
        self.player_teams = []
        self.viewers = []

    def register_team(self, team):
        """ Register a client TeamPlayer class.

        Parameters
        ----------
        team : class which calculates a new move for
            each Bot of the team.
        """
        self.player_teams.append(team)

        # map a player_team to a universe.team 1:1
        team_idx = len(self.player_teams) - 1
        # the respective bot ids in the universe
        bot_ids = self.universe.teams[team_idx].bots

        # tell the team about these bot_ids
        team._set_bot_ids(bot_ids)
        team._set_initial(self.universe.copy())

    def register_viewer(self, viewer):
        """ Register a viewer to display the game state as it progresses.

        Parameters
        ----------
        viewer : subclass of AbstractViewer

        """
        if (viewer.__class__.observe.__func__ ==
                AbstractViewer.observe.__func__):
            raise TypeError("Viewer %s does not override 'observe()'."
                    % viewer.__class__)
        viewer.set_initial(self.universe.copy())
        self.viewers.append(viewer)

    # TODO the game winning detection should be refactored

    def play(self):
        """ Play a whole game. """
        if len(self.player_teams) != len(self.universe.teams):
            raise IndexError(
                "Universe uses %i teams, but only %i are registered."
                % (len(self.player_teams), len(self.universe.teams)))
        for gt in range(self.game_time):
            if not self.play_round(gt):
                return

    def play_round(self, current_game_time):
        """ Play only a single round.

        A single round is defined as all bots moving once.

        Parameters
        ----------
        current_game_time : int
            the number of this round

        """
        for i, bot in enumerate(self.universe.bots):
            player_team = self.player_teams[bot.team_index]
            try:
                move = player_team._get_move(bot.index, self.universe.copy())
                events = self.universe.move_bot(i, move)
            except (uni.IllegalMoveException, PlayerTimeout):
                moves = self.universe.get_legal_moves(bot.current_pos).keys()
                moves.remove(datamodel.stop)
                if not moves:
                    moves = [datamodel.stop]

                move = random.choice(moves)
                events = self.universe.move_bot(i, move)
                events.append(datamodel.TimeoutEvent(bot.team_index))
            except PlayerDisconnected:
                other_team_idx = not bot.team_index

                events = TypeAwareList(base_class=datamodel.UniverseEvent)
                events.append(datamodel.TeamWins(other_team_idx))

            for timeout_event in events.filter_type(datamodel.TimeoutEvent):
                team = self.universe.teams[timeout_event.team_index]
                # team.score -= 1

            for v in self.viewers:
                v.observe(current_game_time, i, self.universe.copy(), copy.deepcopy(events))
            if datamodel.TeamWins in events:
                return False
        return True
