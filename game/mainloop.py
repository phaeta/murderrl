#!/usr/bin/env python
"""
The main game loop, where all components come together.
"""

import curses, random

from builder import builder, manor
from library import viewport, pathfind
from library.coord import *
from library.feature import *
from library.random_util import *
from interface import console, menu
from interface.features import *
from interface.output import *
from suspects import person, randname

class Command (object):
    """
    The representation of a command.
    """
    def __init__ (self, key, action, description, key_suffix=""):
        """
        Initialise a new command.

        :``key``: The character to trigger the command. *Required*.
        :``action``: The command method that is executed when the key is pressed. *Required*.
        :``description``: The command's description in the command help. *Required*.
        :``key_suffix``: A description that's suffixed to the key in the command help. *Default none*.
        """
        self.key         = key
        self.action      = action
        self.description = description
        self.key_suffix  = key_suffix

    def describe_command (self):
        """
        Returns the command's description, including the key.
        """
        return "%s%s: %s\n" % (self.key, self.key_suffix, self.description)

    def execute_command (self):
        self.action()

screen = console.select()

# The message line.
# Following lines may get used for debugging output.
MAP_OFFSET = coord.Coord(1, 2)
MSG_LINE   = 23
MSG_START  = coord.Coord(0, MSG_LINE)

MAX_COLUMNS = 70
MAX_ROWS    = 20

NUM_SUSPECTS = 10

class Game (object):
    """
    The module to handle the main game loop.
    """
    def __init__ (self, type = None):
        """
        Initialise the manor, viewport and other objects and parameters.

        :``type``: The manor layout type. One of B (base), L, U, H, R (random).
                   *Default random*.
        """
        # First, build the manor.
        self.base_manor = manor.ManorCollection(builder.builder_by_type(type, min_rooms=NUM_SUSPECTS + 2))

        # Add doors and windows, etc.
        self.base_manor.add_features()

        self.add_suspects()

        self.add_alibis()
        self.init_suspect_positions()
        self.suspect_list.add_hair_colours()
        self.add_victim_body()

        # Combine the room shapes into a canvas.
        self.canvas = self.base_manor.combine()

        # Draw features on canvas.
        for pos in coord.RectangleIterator(self.canvas.size()):
            feat = self.base_manor.get_feature(pos)
            if feat != NOTHING and feat != WALL and feat != FLOOR:
                self.canvas.__setitem__(pos, feat.glyph())

        # Initialise the view port.
        self.vp = viewport.ViewPort(buffer=self.canvas,
                                    width =min(self.canvas.size().width, MAX_COLUMNS),
                                    height=min(self.canvas.size().height, MAX_ROWS))

        # Initialise a couple of other variables.
        self.initialise_parameters()

    def add_suspects (self):
        """
        Initialise the suspect list, generate bedrooms.
        """
        self.suspect_list = person.SuspectList(NUM_SUSPECTS)

        sl = self.suspect_list
        self.manor_name = sl.get_suspect(0).last
        owner_list = sl.get_id_name_tuples()
        self.base_manor.init_room_names(owner_list)

    def add_alibi_for_suspect(self, sid, rids):
        """
        Generates an alibi for a given suspect in the form of an unoccupied room.

        :``sid``: The suspect id. *Required*.
        :``rids``: Room ids of rooms that are still unoccupied. *Required*.
        """
        # The murderer always picks a room adjacent to one of the corridors,
        # so they don't have to meet any people.
        force_adj_corr = (sid == self.suspect_list.murderer)
        r = self.base_manor.pick_room_for_suspect(rids, sid, None, force_adj_corr)

        if r == None:
            return None

        if sid in self.base_manor.room_props[r].owners:
            rname = "my bedroom"
        else:
            rname = self.base_manor.room_props[r].room_name(True)
        self.suspect_list.get_suspect(sid).set_alibi(r, rname)
        return r

    def add_alibis (self):
        """
        Picks the murder room and assigns alibis (in the form of a room and,
        sometimes, a witness) for all suspects.
        """
        # Shortcuts for commonly used variables.
        sl = self.suspect_list
        m  = self.base_manor
        rprops = m.room_props

        # Try up to 5 times to assign alibis to each of the suspects.
        for i in range(5):
            print("%s. attempt at setting alibis" % (i+1))

            # Reset alibis.
            for s in sl.suspects:
                s.alibi = None

            # Rooms that are not used in an alibi yet. To begin with, all of them.
            rids = m.rooms[:]

            # First, pick the murder room (stored as victim's "alibi").
            r = self.add_alibi_for_suspect(sl.victim, rids)
            if r == None:
                print("Found no murder room! Exit early.")
                return False

            print("Murder room: %s (%s, Victim: %s)" % (rprops[r].name, r, sl.get_victim().get_name()))
            rids.remove(r)
            for adj in rprops[r].adj_rooms:
                if rprops[adj].is_corridor:
                    continue
                print("block adjoining room %s (%s)" % (rprops[adj].name, adj))
                rids.remove(adj)

            r = self.add_alibi_for_suspect(sl.murderer, rids)
            if r != None:
                print("Alibi room for murderer: %s (%s, %s)" % (rprops[r].name, r, sl.get_murderer().get_name()))
                if sl.murderer in rprops[r].owners:
                    rname = "my bedroom"
                else:
                    rname = rprops[r].room_name(True)
                sl.get_murderer().set_alibi(r, rname)
                rids.remove(r)
            else:
                print("Found no alibi room for murderer (%s)" % sl.get_murderer().get_name())
                continue
            murderer_room = r

            # Suspects that don't have an alibi yet.
            sids = list(range(0, sl.no_of_suspects()))
            sids.remove(sl.victim)
            sids.remove(sl.murderer)

            N = len(sids)
            PAIRS = max(1, random.randint((N+1)//5, (N+1)//3))
            need_reroll = False
            for i in range(0, PAIRS):
                idx1 = random.choice(sids)
                sids.remove(idx1)
                p1 = sl.get_suspect(idx1)

                # If this person has relatives, it is highly likely one of them
                # was the witness.
                if coinflip() and len(p1.rel) > 0:
                    rel  = random.choice(p1.rel)
                    idx2 = rel[0]
                    p2   = sl.get_suspect(idx2)
                    if idx2 in sids:
                        sids.remove(idx2)
                        r = m.pick_room_for_suspect(rids, idx1, idx2)
                        if r == None:
                            return False
                        print("%s (%s) for %s and %s" % (rprops[r].name, r, sl.get_suspect(idx1).get_name(), sl.get_suspect(idx2).get_name()))
                        sl.create_paired_alibi(idx1, idx2, r, rprops[r])
                        rids.remove(r)
                        continue

                idx2 = random.choice(sids)
                sids.remove(idx2)
                r = m.pick_room_for_suspect(rids, idx1, idx2)
                if r != None:
                    print("%s (%s) for %s and %s" % (rprops[r].name, r, sl.get_suspect(idx1).get_name(), sl.get_suspect(idx2).get_name()))
                    rids.remove(r)
                    sl.create_paired_alibi(idx1, idx2, r, rprops[r])
                else:
                    print("Found no alibi room for %s and %s" % (sl.get_suspect(idx1).get_name(), sl.get_suspect(idx2).get_name()))
                    need_reroll = True
                    break

            if need_reroll:
                continue

            # Shuffle the remaining list.
            random.shuffle(sids)

            # The remaining suspects don't have a witness.
            for s in sids:
                r = self.add_alibi_for_suspect(s, rids)
                if r != None:
                    print("%s (%s) for %s" % (rprops[r].name, r, sl.get_suspect(s).get_name()))
                    rids.remove(r)
                    if s in rprops[r].owners:
                        rname = "my bedroom"
                    else:
                        rname = rprops[r].room_name(True)
                    sl.get_suspect(s).set_alibi(r, rname)
                else:
                    print("Found no alibi room for %s" % sl.get_suspect(s).get_name())
                    need_reroll = True
                    break

            if need_reroll:
                continue
            break

    def set_suspect_path (self, idx, rid = None):
        """
        Picks an appropriate room for a given suspect and calculates and
        returns a path to it.

        :``idx``: Index of the suspect list. *Required*.
        """
        s = self.suspect_list.get_suspect(idx)
        if rid == None:
            rid = self.base_manor.pick_room_for_suspect(self.base_manor.rooms, idx)
        target_pos = self.base_manor.get_random_pos_in_room(rid)
        path = pathfind.Pathfind(self.base_manor.features, s.pos, target_pos).get_path()
        if path != None:
            s.path = path
            rp = self.base_manor.room_props[rid]
            if self.suspect_list.murderer == idx:
                name = "The murderer (%s)" % s.get_name()
            else:
                name = "%s" % s.get_name()
            print("%s is heading for %s." % (name, rp.room_name(True)))

    def init_suspect_positions (self):
        """
        Initialises the suspects' location to a random position in their
        bedroom or, if that doesn't exist, a random room in the manor..
        """
        sl = self.suspect_list
        rooms = []
        for s in range(sl.no_of_suspects()):
            rooms.append(None)

        manor = self.base_manor
        for r in manor.rooms:
            for i in manor.room_props[r].owners:
                rooms[i] = r

        for i in range(sl.no_of_suspects()):
            if i == sl.victim:
                continue

            if rooms[i] == None:
                rooms[i] = random.choice(manor.rooms)

            s = sl.get_suspect(i)
            s.pos = manor.get_random_pos_in_room(rooms[i])

            if one_chance_in(5):
                self.set_suspect_path(i)

    def describe_body (self, p):
        """
        Returns a flavourful description of the victim's body.

        :``p``: The victim's Person object. *Required*.
        """
        if coinflip():
            name = p.get_name()
            if one_chance_in(4):
                return "%s has been viciously stabbed." % name
            elif one_chance_in(3):
                return "%s's throat has been sliced cleanly." % name
            elif coinflip():
                return "%s has been strangled." % name
            else:
                return "%s's head has been bashed into a bloody pulp." % name
        else:
            pronoun = "he"
            if p.gender == 'f':
                pronoun = "she"
            if one_chance_in(3):
                return "Unseeing eyes wide open, %s is staring at you accusingly." % pronoun
            elif coinflip():
                return "Despite the gaping chest wound, %s looks surprisingly peaceful." % pronoun
            else:
                return "If it weren't for all the blood, you might think %s was sleeping." % pronoun

    def add_victim_body (self):
        sl = self.suspect_list
        murder_room = sl.get_victim().alibi.rid
        free_places = self.base_manor.get_pos_list_within_room(murder_room)

        candidates = []
        for c in free_places:
            if feature_is_floor(self.base_manor.get_feature(c)):
                candidates.append(c)

        assert(len(candidates) > 0)

        victim_name  = sl.get_victim().get_name()
        name         = "the mangled body of %s" % victim_name
        description  = self.describe_body(sl.get_victim())
        description  = description[0].upper() + description[1:]
        feat = BODY.derived_feature(name, description, has_article=True)

        self.body_pos       = random.choice(candidates)
        sl.get_victim().pos = self.body_pos
        self.base_manor.features.__setitem__(self.body_pos, feat)
        rp = self.base_manor.room_props[murder_room]

        features = self.base_manor.get_nearby_interesting_feature(self.body_pos)

        nearby_feat = ""
        if len(features) > 0:
            if CLOSED_DOOR in features or OPEN_DOOR in features:
                if len(rp.adj_rooms) > 1:
                    nearby_feat = "one of the doors"
                else:
                    nearby_feat = "the door"
            elif WINDOW_V in features or WINDOW_H in features:
                nearby_feat = "the window"
            else:
                nearby_feat = "the %s" % features[0].name(False)
            nearby_feat = " near %s" % nearby_feat

        rp.description += "You see here %s%s." % (feat.name(), nearby_feat)

    def initialise_parameters (self):
        """
        Initialise the simple parameters.
        """
        # Initially place the player in the centre of the entrance hall.
        manor = self.base_manor
        self.player_pos = manor.get_random_pos_in_room(manor.entrance_hall)

        self.init_command_list()
        self.game_start   = True    # Game just started.
        self.debugging    = False   # debugging mode
        self.message      = None    # A message displayed for one turn.
        self.dir_running  = DIR_NOWHERE # Direction we are running (if any).
        self.travel_path  = []
        self.quit_game    = False
        self.wait_for_key = True # If false, handle NPC movement without waiting for player key.
        self.turns        = 0
        self.init_command_parameters()

    def init_command_parameters (self):
        """
        (Re)initialises parameters pertaining to movement and other commands
        to their default values.
        """
        self.last_move        = DIR_NOWHERE # the last step taken by the player
        self.move_was_blocked = False       # bumped into an obstacle
        self.did_move         = True        # actually took a step
        self.tried_move_feat  = NOTHING     # The feature the player tried to move on.
        self.was_running      = (self.dir_running != DIR_NOWHERE)
        self.did_switch       = False       # switched to debug mode
        self.time_passed      = False

    def get_welcome_message (self):
        """
        Returns the message that is printed at game start.
        """
        return "Welcome to %s! To view the list of commands, press 'h'." % randname.get_random_manor_name(self.manor_name)

    def get_time (self):
        """
        Translates the turn counter into a time statement and returns.
        """
        hours   = 8 + self.turns / 60
        if hours < 10:
            hours = "0%s" % hours
        minutes = self.turns % 60
        if minutes < 10:
            minutes = "0%s" % minutes
        return "%s:%s" % (hours, minutes)

    def draw_header (self):
        """
        Writes some header information above the map.
        """
        curr = self.get_current_room()
        name = curr.room_name(True)
        print_line("%s%s." % (name[0].upper(), name[1:]))
        print_line("T: %s" % self.get_time(), coord.Coord(MAX_COLUMNS-10, 0))

    def draw_canvas (self):
        """
        Draws the section of the viewport that's currently visible onto the screen.
        """
        for pos, char in self.sect:
            col = Colours.LIGHTGRAY
            if char == None:
                char = " "
            elif char != "#" and char != ".":
                real_coord = pos + coord.Coord(self.vp._left, self.vp._top)
                col = self.base_manor.get_feature(real_coord).colour()
            screen.put(char, pos + MAP_OFFSET, col)

    def draw_suspects (self):
        """
        Draws all suspects at their current position onto the screen.
        """
        sl = self.suspect_list
        for i in range(len(sl.suspects)):
            if sl.victim == i:
                continue
            p = sl.get_suspect(i)
            pos = p.pos
            if not self.vp.pos_in_section(pos):
                continue
            canvas_pos = coord.Coord(pos.x - self.vp._left, pos.y - self.vp._top)
            screen.put(p.glyph, canvas_pos + MAP_OFFSET, Colours.WHITE)

    def draw_viewport (self):
        """
        Draws the game map, including the player glyph, onto the screen.
        """
        # The currently visible section of the viewport, centered on the player.
        self.vp.centre(self.player_pos, self.canvas.size())
        self.sect = self.vp.sect()
        self.draw_canvas()

        # Draw player and suspects.
        canvas_pos = coord.Coord(self.player_pos.x - self.vp._left, self.player_pos.y - self.vp._top)
        screen.put("@", canvas_pos + MAP_OFFSET, Colours.YELLOW)
        self.draw_suspects()

    def get_current_room_id (self, pos = None):
        """
        Returns the room id a given position belongs to.

        :``pos``: A coordinate in the manor. If none, the player position is used. 
                  *Default None*.
        """
        if pos == None:
            pos = self.player_pos

        # Get the current room/corridor id.
        id = self.base_manor.get_room_index(pos)
        if id == None:
            id = self.base_manor.get_corridor_index(pos)
        return id

    def get_current_room (self, pos = None):
        """
        Returns the RoomProps object matching a given position.

        :``pos``: A coordinate in the manor. If none, the player position is used. 
                  *Default None*.
        """
        if pos == None:
            pos = self.player_pos

        # Get the current room/corridor id.
        id = self.get_current_room_id(pos)
        return self.base_manor.get_roomprop(id)

    def print_message (self, text):
        """
        Prints a message in the customary message line.

        :``text``: The message to be printed.
        """
        print_text(text, MSG_START, MAX_COLUMNS)

    def print_debugging_messages (self):
        """
        Prints a variety of parameters in the message area. (Only in debug mode.)
        """
        # Get the current room/corridor id.
        id = self.base_manor.get_corridor_index(self.player_pos)
        type = "corridor"
        if id == None:
            id   = self.base_manor.get_room_index(self.player_pos)
            type = "room"
        room_desc = self.base_manor.get_roomprop(id)

        print_line("Sect size : %s, Start coord: %s, Stop coord: %s, %s" % (self.sect.size(), coord.Coord(self.vp._left, self.vp._top), coord.Coord(self.vp._left + self.vp._width, self.vp._top + self.vp._height), room_desc), coord.Coord(0, MSG_LINE+1))

        print_line("Manor size: %s, Player coord: %s, last_move: %s, %s id: %s" % (self.canvas.size(), self.player_pos, self.last_move, type, id), coord.Coord(0, MSG_LINE+2))

    def draw_messages (self):
        """
        Writes game messages into the message area.
        """
        if self.message != None:
            self.print_message(self.message)
            self.message = None
        elif self.game_start:
            self.print_message(self.get_welcome_message())
            self.game_start = False
        elif self.move_was_blocked:
            self.print_message("Ouch! You bump into a %s!" % self.tried_move_feat.name())
        elif self.did_switch:
            mode = "canvas view"
            if self.debugging:
                mode = "debug mode"
            print_line("Switched to %s." % mode, MSG_START)
        elif self.did_move:
            oldrooms = self.base_manor.get_room_indices(self.player_pos - self.last_move)
            newrooms = self.base_manor.get_room_indices(self.player_pos)
            curr_rid = None
            for r in newrooms:
                if r not in oldrooms:
                    curr_rid = r
                    break
            if len(newrooms) == 0:
                curr_rid = self.base_manor.get_corridor_index(self.player_pos)
                old_corr = self.base_manor.get_corridor_index(self.player_pos - self.last_move)
                if len(oldrooms) == 0:
                    curr_rid = None
                else:
                    desc = "You step out into"
            else:
                desc = "You enter"

            oldcorrs = self.base_manor.get_corridor_indices(self.player_pos - self.last_move)
            newcorrs = self.base_manor.get_corridor_indices(self.player_pos)
            # print "oldrooms: %s, newrooms: %s, oldcorrs: %s, newcorrs: %s, curr_rid: %s" % (oldrooms, newrooms, oldcorrs, newcorrs, curr_rid)
            if curr_rid != None:
                self.print_message("%s %s." % (desc, self.base_manor.get_roomprop(curr_rid).room_name(True)))
            else:
                feat = self.base_manor.get_feature(self.player_pos)
                if feature_is_door(feat):
                    self.print_message("You see here a door.")
                elif not feature_is_floor(feat):
                    self.print_message("You see here %s." % feat.name(True))

        if self.debugging:
            # Debugging information.
            self.print_debugging_messages()

    def update_screen (self):
        """
        Updates game map and message area.
        """
        # Note: Currently the screen gets cleared completely. Splitting that
        #       for map/message area could be useful. (jpeg)
        screen.clear(" ")
        self.draw_header()
        self.draw_viewport()
        self.draw_messages()

    def cmd_describe_room (self, pos = None):
        """
        Describes the room a given position belongs to.

        :``pos``: A coordinate in the manor. If none, the player position is used. 
                  *Default None*.
        """
        if pos == None:
            pos = self.player_pos

        room = self.get_current_room(pos)

        persons = []
        curr_room = self.get_current_room()
        sl = self.suspect_list
        for sid in range(sl.no_of_suspects()):
            if sid == sl.victim:
                continue
            p = sl.get_suspect(sid)
            if self.get_current_room(p.pos) == curr_room:
                persons.append(p.get_fullname())

        room.describe(persons)

    def cmd_describe_feature (self, pos = None):
        """
        Describes the room a given position belongs to.

        :``pos``: A coordinate in the manor. If none, the player position is used. 
                  *Default None*.
        """
        if pos == None:
            pos = self.player_pos

        feat = self.base_manor.get_feature(pos)
        self.message = feat.description()
        sl = self.suspect_list
        if pos == self.body_pos and not sl.get_victim().have_seen:
            self.message += "\nYou find an alien %s hair!" % sl.get_murderer().hair
            sl.get_victim().have_seen = True

    def pos_in_travel_room (self, pos):
        """
        A helper method to check whether travel has reached the target room.

        :``pos``: A coordinate along the path. *Required*.
        """
        curr_room = self.get_current_room_id(pos)
        return curr_room == self.travel_target_room

    def start_travel (self, room_id):
        """
        Calculate a path to another room and store it, so travel can then
        follow it.

        :``room_id``: The room id of the target room. *Required*.
        """
        if self.get_current_room_id() == room_id:
            self.message = "You are already here."
            return

        self.travel_target_room = room_id
        path = pathfind.Pathfind(self.base_manor.features, self.player_pos, None, self.pos_in_travel_room).get_path()
        if path != None:
            self.travel_path = path
        else:
            self.message = "The requested path couldn't be found."

    def cmd_travel_menu (self):
        """
        Offers the player a choice of rooms within the manor. Picking one
        of them initialises travel.
        """
        m = menu.ScrollMenu("Travel where?", False)
        rprops  = self.base_manor.room_props
        curr_id = self.get_current_room_id()
        keyval  = ord('a')
        rlist   = self.base_manor.get_room_corridors()[:]
        rlist.sort(cmp=lambda a, b: cmp(rprops[a].name, rprops[b].name))
        for i in rlist:
            key = chr(keyval)
            name = rprops[i].name
            if i == curr_id:
                name += " (current location)"
            e = menu.Entry(key, name, self.start_travel, i)
            m.add_entry(e)

            if key == 'z':
                keyval = ord('A')
            else:
                keyval += 1
        m.do_menu()
        # self.update_screen()

    def question_suspect (self, idx):
        """
        Get a suspect's alibi statement.

        :``idx``: Suspect index of the suspect list. *Required*.
        """
        sl  = self.suspect_list
        s   = sl.get_suspect(idx)
        rid = self.get_current_room_id(s.pos)
        self.message = "%s says, %s" % (s.get_name(), sl.get_alibi_statement(idx, rid))
        s.have_seen  = True
        self.time_passed = True

    def cmd_question_suspect (self):
        """
        Get the nearest suspect's alibi statement.
        Prompt the player if there are several suspects within range.
        """
        candidates = []
        sl = self.suspect_list
        rm = self.get_current_room_id()
        for idx in range(sl.no_of_suspects()):
            if idx == sl.victim:
                continue

            s = sl.get_suspect(idx)
            if s.pos.dist(self.player_pos) > 3:
                continue

            rid = self.get_current_room_id(s.pos)
            if rid != rm and s.pos.dist(self.player_pos) > 1:
                continue

            candidates.append(idx)

        if len(candidates) == 0:
            self.message = "There's no one here to question!"
            return

        if len(candidates) > 1:
            m  = menu.Menu("Question whom?", False)
            sl = self.suspect_list
            candidates.sort(cmp=lambda a, b: cmp(sl.get_suspect(a).first, sl.get_suspect(b).first))
            for i in candidates:
                if not sl.is_victim(i):
                    p = sl.get_suspect(i)
                    e = menu.Entry(p.first[0].lower(), p, self.question_suspect, i)
                    m.add_entry(e)
            m.do_menu()
        else:
            self.question_suspect(candidates[0])

    def cmd_display_suspect_list (self):
        """
        Display the suspects in a menu. Choosing one of them displays a
        description.
        """
        m  = menu.Menu("List of suspects")
        sl = self.suspect_list
        e  = menu.Entry('x', "Victim: " + sl.get_victim().get_name(), sl.describe_suspect, sl.victim, sl.get_victim().first[0].lower(), colour=Colours.BROWN)
        m.add_entry(e)

        # Sort the list by name.
        list = list(range(0, sl.no_of_suspects()))
        list.sort(cmp=lambda a, b: cmp(sl.get_suspect(a).first, sl.get_suspect(b).first))
        for i in list:
            if not sl.is_victim(i):
                p = sl.get_suspect(i)
                e = menu.Entry(p.first[0].lower(), p, sl.describe_suspect, i, colour=highlight_colour(p.suspicious))
                m.add_entry(e)
        m.do_menu()

    def cmd_accuse_murderer (self):
        """
        Display a list of suspects in a menu to accuse one of them as the murderer.
        """
        m = menu.Menu("Accuse whom?", False)
        sl = self.suspect_list
        # Sort the list by name.
        list = list(range(0, sl.no_of_suspects()))
        list.sort(cmp=lambda a, b: cmp(sl.get_suspect(a).first, sl.get_suspect(b).first))
        for i in list:
            if not sl.is_victim(i):
                p = sl.get_suspect(i)
                e = menu.Entry(p.first[0].lower(), p, self.accuse_suspect, i, colour=highlight_colour(p.suspicious))
                m.add_entry(e)
        m.do_menu()

    def accuse_suspect (self, sidx):
        """
        Check whether a given suspect index matches that of a murderer and
        ends the game.

        :``sidx``: Suspect index. *Required*.
        """
        if sidx == self.suspect_list.murderer:
            self.message = "Congratulations! You've found the murderer!"
        else:
            self.message = "Sorry, you picked the wrong person."
        self.update_screen()
        screen.get(block=True)
        self.quit_game = True

    def init_command_list (self):
        """
        Initialise the list of commands.
        """
        self.commands = []
        self.commands.append(Command("r", self.cmd_start_running, "start running in that direction\n", " followed by a direction"))
        self.commands.append(Command("a", self.cmd_accuse_murderer, "accuse a suspect of being the murderer and end the game"))
        self.commands.append(Command("d", self.cmd_describe_room, "describe current room"))
        self.commands.append(Command("h", self.cmd_display_command_help, "display this screen"))
        self.commands.append(Command("q", self.cmd_question_suspect, "question the nearest suspect"))
        self.commands.append(Command("s", self.cmd_display_suspect_list, "display the list of suspects"))
        self.commands.append(Command("t", self.cmd_travel_menu, "travel to another room"))
        self.commands.append(Command("x", self.cmd_describe_feature, "examine current feature"))
        self.commands.append(Command("D", self.cmd_toggle_debug_mode, "toggle between normal and debug mode"))

    def cmd_display_command_help (self):
        """
        Returns a string of command keys and their explanation.
        """
        help  = "Command help\n\n"
        help += "Use the arrow keys for movement.\n\n"
        for cmd in self.commands:
            help += cmd.describe_command()
        help += "\nAny other key exits the program."

        print_screen(help)

    def cmd_toggle_debug_mode (self):
        # Toggle debugging mode on and off.
        self.debugging  = not self.debugging
        self.did_switch = True

    def handle_movement_keys (self, ch):
        """
        Checks whether a given keypress matches any of the movement keys
        and, if so, returns the matching directional coordinate.

        :``ch``: The key pressed by the player. *Required*.
        """
        if ch == curses.KEY_UP:
            return DIR_NORTH
        if ch == curses.KEY_DOWN:
            return DIR_SOUTH
        if ch == curses.KEY_LEFT:
            return DIR_WEST
        if ch == curses.KEY_RIGHT:
            return DIR_EAST

        return DIR_NOWHERE

    def cmd_start_running (self):
        """
        Prompts for a direction key and starts moving the player in that
        direction until we run into an obstacle or reach an adjacent door.
        """
        ch = screen.get(block=True)
        self.dir_running = self.handle_movement_keys(ch)
        self.was_running = True
        if self.dir_running != DIR_NOWHERE:
            self.last_move = self.dir_running
            self.did_move  = True

    def handle_movement_commands (self):
        """
        Check whether the planned move is valid. If so, actually move the
        player. Otherwise, change a few parameters.
        """
        next_pos = self.player_pos + self.last_move
        if (next_pos.x < 0 or next_pos.y < 0
        or next_pos.x >= self.base_manor.size().x or next_pos.y >= self.base_manor.size().y):
            self.move_was_blocked = True
        else:
            self.tried_move_feat = self.base_manor.get_feature(next_pos)
            if not self.debugging and not self.tried_move_feat.traversable():
                self.move_was_blocked = True
            else:
                self.player_pos = next_pos
                if self.dir_running != DIR_NOWHERE:
                    # check whether we need to stop
                    if (feature_is_door(self.base_manor.get_feature(self.player_pos))
                    or self.debugging and not self.tried_move_feat.traversable()):
                        self.dir_running = DIR_NOWHERE
                    else:
                        in_corr = (self.base_manor.get_corridor_index(self.player_pos) != None)
                        dirs = (DIR_NORTH, DIR_SOUTH, DIR_WEST, DIR_EAST)
                        for d in dirs:
                            if d == self.dir_running or DIR_NOWHERE - d == self.dir_running:
                                continue
                            if (in_corr and self.base_manor.get_feature(self.player_pos + d) == FLOOR
                            or feature_is_door(self.base_manor.get_feature(self.player_pos + d))):
                                self.dir_running = DIR_NOWHERE
                                break

        if self.move_was_blocked:
            # Reset last_move.
            self.last_move = DIR_NOWHERE
            self.did_move  = False
            if self.was_running or len(self.travel_path) > 0:
                # No running into wall messages.
                self.move_was_blocked = False
                self.dir_running      = DIR_NOWHERE
                self.travel_path      = []
        else:
            for s in self.suspect_list.suspects:
                if s.pos == self.player_pos:
                    s.pos = s.pos - self.last_move
                    break

            self.did_move    = True
            self.time_passed = True

    def handle_commands (self):
        """
        Wait for a keypress and execute the corresponding action.
        Returns true if the game loop should continue, and false if we
        want to exit the loop.
        """
        curr_pos = self.player_pos
        if len(self.travel_path) > 0:
            next_pos = self.travel_path.pop()
            self.last_move = next_pos - curr_pos
        elif self.dir_running == DIR_NOWHERE:
            # Get a key.
            ch = screen.get(block=self.wait_for_key)

            if ch > 0 and ch <= 256:
                self.did_move = False
                found_key = False
                # Try for a command with a matching key.
                for cmd in self.commands:
                    if chr(ch) == cmd.key:
                        found_key = True
                        cmd.execute_command()

                if not found_key:
                    # exit the game
                    return False
            else:
                # Move the player (@) via the arrow keys.
                # If we haven't reached the manor boundaries yet, scroll in that direction.
                # Otherwise, take a step unless it would make us leave the manor.
                self.last_move = self.handle_movement_keys(ch)
        else:
            self.last_move = self.dir_running

        # Actually move the player, if the new position is valid.
        if self.last_move != DIR_NOWHERE:
            self.handle_movement_commands()

        return True

    def move_suspect (self, i):
        sl = self.suspect_list
        s  = sl.get_suspect(i)
        if len(s.path) == 0:
            if s.duration > 0:
                s.duration -= 1
            elif one_chance_in(30):
                self.set_suspect_path(i)

        manor = self.base_manor
        if len(s.path) > 0:
            if self.player_pos == s.path[-1]:
                return

            new_pos = s.path.pop()
            if len(s.path) == 0:
                rp = manor.room_props[manor.get_room_index(new_pos)]
                if i in rp.owners:
                    if s.gender == 'f':
                        pronoun = "her"
                    else:
                        pronoun = "his"
                    room_name = "%s bedroom" % pronoun

                    if self.turns > 780:
                       s.duration = 500
                else:
                    room_name = rp.room_name(True)
                print("%s has reached %s." % (s.get_name(), room_name))
        else:
            valid_moves = []
            for pos in AdjacencyIterator(s.pos):
                if pos == self.player_pos:
                    continue
                if not manor.get_feature(pos).traversable():
                    continue
                # Don't leave the room yet.
                if s.duration > 0 and manor.get_room_index(pos) != manor.get_room_index(s.pos):
                    continue

                valid_moves.append(pos)

            if len(valid_moves) == 0:
                return

            new_pos = random.choice(valid_moves)

        # If we walk into another suspect, swap positions.
        for s2 in sl.suspects:
            if s != s2 and new_pos == s2.pos:
                s2.pos = s.pos
                break

        # Set the new position.
        s.pos = new_pos

    def move_suspects (self):
        """
        Handle suspect movement: Randomly picks a free adjacent position.
        """
        sl    = self.suspect_list
        manor = self.base_manor
        for i in range(len(sl.suspects)):
            if sl.victim == i:
                continue

            self.move_suspect(i)

    def handle_time (self):
        """
        A turn has passed: Increase turn counter, move suspects.
        """
        self.move_suspects()
        self.turns += 1

    def do_loop (self):
        """
        Run the actual game loop. Returns if we encounter an invalid keypress.
        """
        while True:
            if self.dir_running == DIR_NOWHERE and len(self.travel_path) == 0:
                self.update_screen()

            # Reinitialise the relevant variables.
            self.init_command_parameters()

            if not self.handle_commands():
                return

            if self.quit_game:
                return

            if not self.wait_for_key or self.time_passed:
                self.handle_time()
