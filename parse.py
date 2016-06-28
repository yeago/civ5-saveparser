import FileReader as fr
import pickle

__author__ = "Hussein Kaddoura"
__copyright__ = "Copyright 2013, Hussein Kaddoura"
__credits__ = ["Hussein Kaddoura"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Hussein Kaddoura"
__email__ = "hussein.nawwaf@gmail.com"
__status__ = "Development"


traits = {
    1: "alive",
    3: "human",
    0: "human",
    2: "dead",
}

victories = {
    1: "VICTORY_TIME",
    2: "VICTORY_SPACE_RACE",
    3: "VICTORY_DOMINATION",
    4: "VICTORY_CULTURAL",
    5: "VICTORY_DIPLOMATIC",
}


def parse(filename):
    """ Parses the save file and transforms it to xml    """

    with fr.FileReader(filename) as civ5Save:
        base = parse_base(civ5Save)
        # comp = parse_compressed_payload(civ5Save)


def parse_base(fileReader):
    """
        Parse the general game options
        Code is definitely not optimal. We'll go through a round a refactoring after mapping more information
        Refactoring 1: Remove all localization queries. This will be done on a later note.
    """

    struct = {'version': {}, 'game': {}, 'civilization': {}, 'handicap': {}}
    fileReader.skip_bytes(4)  # always CIV5

    struct['version']['save'] = str(fileReader.read_int())
    struct['version']['game'] = fileReader.read_string()
    struct['version']['build'] = fileReader.read_string()

    struct['game']['currentturn'] = str(fileReader.read_int())

    fileReader.skip_bytes(1)  # TODO: I'll investigate later as to what this byte hold

    struct['civilization']['text'] = fileReader.read_string()

    struct['handicap'] = fileReader.read_string()

    struct['era_start'] = fileReader.read_string()
    struct['era_current'] = fileReader.read_string()

    struct['gamespeed'] = fileReader.read_string()
    struct['worldsize'] = fileReader.read_string()
    struct['mapscript'] = fileReader.read_string()
    struct['dlcs'] = []

    fileReader.skip_bytes(4)  # TODO: an int
    while fileReader.peek_int() != 0:
        fileReader.skip_bytes(16)  # TODO: some binary data
        fileReader.skip_bytes(4)  # TODO: seems to be always 1
        struct['dlcs'].append(fileReader.read_string())

    # #Extract block position (separated by \x40\x00\x00\x00 (@) )
    # #I haven't decoded what each of these blocks mean but I'll extract their position for the time being.

    bb_pos = tuple(fileReader.findall('0x40000000'))
    # 32 blocks have been found. We'll try to map them one at a time.

    # block 1
    fileReader.pos = bb_pos[0] + 32  # remove the delimiter (@)
    block1 = tuple(map(lambda x: x.read(32).intle, fileReader.read_bytes(152).cut(32)))

    # TODO: block2 - seems to only contain Player 1?

    # block3
    # contains the type of civilization - 03 human, 01 alive, 04 missing, 02 dead
    fileReader.pos = bb_pos[2] + 32
    leader_traits = tuple(map(lambda x: x.read(32).intle, fileReader.read_bytes(256).cut(32)))

    # TODO: block4
    # TODO: block5
    # TODO: block6

    # block 7
    # contains the list of civilizations
    civilizations = fileReader.read_strings_from_block(bb_pos[6] + 32, bb_pos[7])

    # block 8
    # contains the list of leaders
    leaders = fileReader.read_strings_from_block(bb_pos[7] + 32, bb_pos[8], True)

    # TODO: block9-18

    # block 19
    # contains the civ states. There seems to be a whole bunch of leading 0s.
    fileReader.forward_to_first_non_zero_byte(bb_pos[18] + 32, bb_pos[19])
    civStates = fileReader.read_strings_from_block(fileReader.pos, bb_pos[19], True)

    # TODO: block 20 - there's a 16 byte long list of 01's
    # TODO: block 21 - seems to be FFs
    # TODO: block 22, 23 - 00s
    # TODO: block 24 - player colors
    # TODO: blocks 25-27

    # block 28
    # the last 5 bytes contain the enabled victory types
    fileReader.pos = bb_pos[28] - 5*8
    victorytypes = (fileReader.read_byte(), fileReader.read_byte(), fileReader.read_byte(), fileReader.read_byte(), fileReader.read_byte() )

    # block 29
    # have the game options
    # fileReader.find(b'GAMEOPTION', bb_pos[28]+32, bb_pos[29])
    # fileReader.pos -= 32
    # gameoptions = []
    # while fileReader.pos < bb_pos[29]:
    #    s = fileReader.read_string()
    #    if s == "":
    #        break
    #    state = fileReader.read_int()
    #    gameoptions.append((s, state))

    # TODO: block 30-31

    # TODO: block 32
    # contains the zlib compressed data

    civs = tuple(map(lambda civ, trait, leader:  (civ, trait, leader), civilizations, leader_traits, leaders))

    struct['civs'] = []
    for civ, trait, leader in civs:
        if trait in traits:
            struct['civs'].append(
                (civ,
                 traits[trait],
                 leader))

    struct['citystates'] = [civStates]

    struct['victories'] = [(victories[idx], victory) for idx, victory in enumerate(victorytypes, start=1)]

    # for gameoption in gameoptions:
    #     gameoptionXml.set('enabled', str(gameoption[1]))
    #     gameoptionXml.text = gameoption[0]

    return struct


def parse_compressed_payload(fileReader):
    struct = {}
    files = fileReader.extract_compressed_payloads()

    with fr.FileReader(files[0]) as f:
        f.read_int()  # 1?
        f.read_int()  # 0?
        f.read_int()  # current turn, already extracted in the main save file
        f.read_int()  # 0
        f.read_int()  # 0
        f.read_int()  # -4000 : starting year?
        f.read_int()  # 500  : max turn count?
        f.read_int()  # 500 : max turn count?
        playedtime = f.read_int()  # playing time in seconds + a last digit

        lastDigit = playedtime % 10
        totalSeconds = int((playedtime - lastDigit) / 10)

        hours, totalSeconds = divmod(totalSeconds, 3600)

        minutes, seconds = divmod(totalSeconds, 60)
        # seconds = (totalSeconds - hours * 3600 - minutes * 60)

        # print(hours, minutes, seconds)

        p.set('hours', str(hours))
        p.set('minutes', str(minutes))
        p.set('seconds', str(seconds))
        p.set('last', str(lastDigit))

        f.read_int()  # 0?

        # bunch of bytes. TODO: investigate
        f.skip_bytes(90)

        # comes a list of string stuff.TODO: what do they refer to?
        nb_notes = f.read_int()
        struct['notes'] = []
        for note in range(0, nb_notes):
            struct['notes'].append(f.read_string())

        # fast forward to another list skipping some unknown bytes for now
        f.pos = f.find_first('0xC1F2439C016F26110F014A49D3CA01A564ABAD01')[0] + 20 * 8

        # skipping some 20 bytes long blocks
        nb = f.read_int()
        for i in range(0, nb):
            f.skip_bytes(24)

        # i get some city stuff notification
        nb_cities = f.read_int()
        struct['city_notes'] = []
        for i in range(0, nb_cities):
            struct['city_notes'].append(f.read_string())

        # get some notes about great persons
        struct['gp_notes'] = []
        nb_great_persons = f.read_int()
        for i in range(0, nb_great_persons):
            struct['gp_notes'].append(f.read_string())

        histograms = {}
        histogram_labels = {}

        # histograms data
        # it seems that a lot of this data has been poluted with FFs. I"ll remove them for now.
        histograms_pos = f.findall(b'REPLAYDATASET_SCORE')

        for pos in histograms_pos:
            f.pos = pos + 19*8  # had to skip because of a bug somewhere. TODO: investigate
            # data_sets = f.read_int()
            data_sets = 27  # 1B. has to be hardcoded because of a bug somewhere TODO: investigate

            histogram_labels[0] = 'REPLAYDATASET_SCORE'
            histograms[0] = {}

            for i in range(1, data_sets):
                h = f.read_string_safe()
                histogram_labels[i] = h
                histograms[i] = {}

            n_ent = f.read_byte(3)

            for i in range(0, n_ent):
                n_data = f.read_byte(3)
                for j in range(0, n_data):
                    histograms[i][j] = {}
                    n_turns = f.read_byte(skip=3)
                    if n_turns > 0:
                        for k in range(0, n_turns):
                            turn = f.read_byte(skip=3)
                            value = f.read_byte(skip=3)
                            histograms[i][j][k] = value

            jar = open('histograms.{0}.pickle'.format(pos), 'wb')
            pickle.dump(histograms, jar)
            jar.close()

if __name__ == "__main__":
    import sys
    parse(sys.argv[1])
