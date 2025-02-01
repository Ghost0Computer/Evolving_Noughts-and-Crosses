from tkinter import *
from tkinter import messagebox
from random import randint as ran
from random import shuffle


class Board:
    # Allows for easy board creation and redoing
    def __init__(self, axes, contents):
        self.axes = axes
        self.contents = contents


class Unit:
    def __init__(self, team, character):
        self.team = team
        self.character = character
        self.sprite = PhotoImage(file=image_dir + character + str(team) + ".png")


image_dir = "images/"
games_dir = "games/"
events_dir = "events/"
game_count = 0
board = Board(axes=[range(1, 2), range(1, 2)], contents=dict())
rules = dict()
controls = []
actions = dict()
events = []
sprite_height = 50
sprite_width = 50
buttons = []
labelsX = []
labelsY = []
cam_pos = {"y": -8, "x": 1}
rows = 0
cols = 0
button_history = 0
winner = 1
turn = 1
player_count = 2
move_list = []
this_turn = []
popup_memory = []
popup_images = []
rounds = 1

with open('Games.txt', 'r') as f:
    # The line-up of games you will play
    games = f.read().splitlines()


def start_game():
    global games, rules, game_count, board, cam_pos, window, button_history, winner, turn, sprite_width, controls, \
        actions, events, popup_memory, popup_images
    turn = winner
    window.title(f"Player {turn}'s turn")
    board = Board(axes=[range(1, 2), range(1, 2)], contents=dict())
    events = []
    controls = []
    for popup in popup_memory:
        popup.destroy()
    popup_memory.clear()
    popup_images.clear()
    if button_history == 0:
        button = Button()
        button.destroy()
        button_history += 1
    with open(f'{games_dir}{games[game_count]}.txt', 'r') as ff:
        # All the rules and setup requirements for the current game
        current_game = ff.read().splitlines()
        rules = dict()
        for line in current_game:
            # This checks the type of setup action
            rule_type = line[0]
            line = line[1:]
            # This asserts the length of each axis
            match rule_type:
                case "@":
                    line = line.split("/")
                    board.axes.clear()
                    for edge in line:
                        edge = [int(e) for e in edge.split("^")]
                        board.axes.append(range(edge[0], edge[1]))
                # Adds a key-list pair to "rules"
                case "*":
                    line = line.split("/")
                    rules.update({line[0]: line[1]})
                # Adding a true or false rule
                case "!":
                    line = line.split("/")
                    if line[1] == "1":
                        rules.update({line[0]: True})
                    else:
                        rules.update({line[0]: False})
                case "#":
                    line = line.split("/")
                    rules.update({line[0]: int(line[1])})
                case "+":
                    line = line.split("/")
                    controls.append(line)
                case "%":
                    line = line.split("/")
                    actions.update({line[0]: [int(_) for _ in line[1:]]})
                case "&":
                    events.append(line)
        events = tuple(events)
        controls = tuple(controls)
    display()


def display():
    global buttons, rows, cols, board, cam_pos
    count = -1
    cam_y = cam_pos.get("y")
    cam_x = cam_pos.get("x")
    colours = rules.get("colours").split(",")
    height_var = sprite_height - sprite_height * 0.1
    width_var = sprite_width - sprite_width * 0.1
    for fy in range(rows):
        for fx in range(cols):
            count += 1
            target = f"{fy + cam_y},{fx + cam_x}"
            if validate(target):
                colour = colours[(sum([int(t) for t in target.split(",")]) % (len(colours) - 1)) + 1]
            else:
                colour = colours[0]
            if target in board.contents:
                buttons[count].config(image=board.contents.get(target).sprite, bg=colour, height=height_var,
                                      width=width_var)
            else:
                buttons[count].config(image=empty, bg=colour, height=height_var, width=width_var)

    for fy in range(rows):
        labelsY[fy].config(text=str(0 - (fy + cam_y)))
    for fx in range(cols):
        labelsX[fx].config(text=str(fx + cam_x))


def validate(target_pos):
    global board, rules
    target_pos = [int(t) for t in target_pos.split(",")]
    if "Endless" in rules:
        if rules.get("Endless"):
            return True
    for axis_index, axis in enumerate(board.axes):
        if target_pos[axis_index] not in axis:
            return False
    return True


def win_check(target):
    global board, turn, rules
    line_length = rules.get("win_line")
    win_lines = []
    for line in [[1, 0], [0, 1], [1, 1], [1, -1]]:
        for point in range(0 - line_length, line_length):
            goal = (str(int(target.split(",")[0]) + point * line[0]) + "," +
                    str(int(target.split(",")[1]) + point * line[1]))
            if goal not in board.contents:
                win_lines.append(0)
                continue
            win_lines.append(board.contents.get(goal).team)
        win_lines.append(0)
    goal = 0
    for line in win_lines:
        goal += 1
        if line != turn:
            goal = 0
        if goal >= line_length:
            break
    else:
        return False
    return True


def win():
    global games, game_count, turn, winner
    display()
    winner = turn
    messagebox.showinfo(title="We have a winner!", message=f"Player {turn} has won this game of {games[game_count]}!")
    game_count += 1
    if game_count >= len(games):
        if len(games) > 1:
            messagebox.showinfo(title="That's all folks", message="You have completed all games!")
        quit()
    start_game()


def inpt(pressed):
    global cam_pos, controls, actions
    key_press = pressed.keysym
    if key_press == "space":
        resize()
    if key_press == "BackSpace":
        undo()
    move_keys = ["Up", "Down", "Left", "Right"]
    if key_press in move_keys:
        destination = [[-1, 0], [1, 0], [0, -1], [0, 1]][move_keys.index(key_press)]
        cam_y = cam_pos.get("y")
        cam_x = cam_pos.get("x")
        cam_pos.update({"y": cam_y + destination[0], "x": cam_x + destination[1]})
        display()

    for control in controls:
        if control[0] == key_press:
            match control[1]:
                case "ChangeBoard":
                    execute("", "", "", [int(control[-3]), int(control[-2]),
                                         int(control[-1])], control[2])
                    turn_gate()
                    display()


def click(button_id):
    global button_history, buttons, board, rows, turn, actions
    cam_y = cam_pos.get("y")
    cam_x = cam_pos.get("x")
    clicked = int(str(button_id).removeprefix(".!button")) - button_history - 1
    target = str(f"{clicked // cols + cam_y},{clicked % cols + cam_x}")
    if target in board.contents:
        return
    if not validate(target):
        return
    cross = Unit(team=turn, character="Cross")
    execute(cross, "", target, "", "Noughts&Crosses")
    turn_gate()


def turn_gate():
    global actions, turn, player_count, actions, move_list, this_turn, window, rounds

    for value in actions.values():
        if value[1] > value[2]:
            return

    for value in actions.values():
        value[1] = value[0]

    for moves in this_turn:
        if moves[2]:
            if win_check(moves[2]):
                win()
                return
    turn = turn % player_count + 1
    if turn == 1:
        rounds += 1
    window.title(f"Player {turn}'s turn, round {rounds}")
    event_gate()
    move_list.append(this_turn.copy())
    this_turn.clear()


def execute(unit, old_pos, target, board_move_dir, gate_input):
    global board, move_list
    gate = actions.get(gate_input)
    if gate[1] <= gate[2]:
        return
    actions.update({gate_input: [gate[0], gate[1] - 1, gate[2]]})
    if board_move_dir:
        board.axes[board_move_dir[0]] = range(board.axes[board_move_dir[0]][0] + board_move_dir[1],
                                              board.axes[board_move_dir[0]][-1] + board_move_dir[2] + 1)
    if target:
        if old_pos:
            board.contents.popitem(old_pos)
        board.contents.update({target: unit})
    this_turn.append([unit, old_pos, target, board_move_dir, gate_input])
    display()


def undo():
    global board, this_turn, move_list, turn, player_count, actions, rounds
    if rounds < 2:
        messagebox.showinfo(title="Restart the game if you need to.", message="---THE-PAST-MAY-NOT-BE-UNDONE---\n"
                                                                              "You may not redo the first round.")
        return
    if this_turn == list():
        this_turn = move_list[-1]
        move_list.pop()
        turn -= 1
        if turn < 1:
            turn = player_count
            rounds -= 1
        window.title(f"Player {turn}'s turn, round {rounds}")

        for key in actions.keys():
            value = actions.get(key)
            value[1] = value[0] - [gate[4] for gate in this_turn].count(key)

    undo_target = this_turn[-1]
    unit = undo_target[0]
    old_pos = undo_target[1]
    target = undo_target[2]
    board_move_dir = undo_target[3]
    gate_input = undo_target[4]
    this_turn.pop()
    gate = actions.get(gate_input)
    actions.update({gate_input: [gate[0], gate[1] + 1, gate[2]]})

    if board_move_dir:
        board.axes[board_move_dir[0]] = range(board.axes[board_move_dir[0]][0] - board_move_dir[1],
                                              board.axes[board_move_dir[0]][-1] - board_move_dir[2] + 1)
    if target:
        board.contents.pop(target)
    if old_pos:
        board.contents.update({old_pos: unit})
    display()


def event_gate():
    global events, board, events_dir
    for event in events:
        with open(events_dir + event + "_req.txt", 'r') as ff:
            instructions = tuple(ff.read().splitlines())
        for instruction in instructions:
            instruction = instruction.split("/")
            if instruction[0] in board.contents:
                value = board.contents.get(instruction[0]).character + str(board.contents.get(instruction[0]).team)
                if value == instruction[1]:
                    continue
                else:
                    break
            else:
                break
        else:
            event_trigger(event)


def event_trigger(event):
    global events_dir, popup_images, popup_memory
    with open(events_dir + event + "_comp.txt", 'r') as ff:
        instructions = tuple(ff.read().splitlines())

    for instruction in instructions:
        rule_type = instruction[0]
        instruction = instruction[1:].split("/")
        popups = []
        match rule_type:
            case "-":
                popups = range(int(instruction[1]), int(instruction[2]) + 1, int(instruction[3]))
            case "%":
                popups = [ran(int(instruction[1]), int(instruction[2]))]
            case "~":
                popups = range(int(instruction[1]), int(instruction[2]) + 1)
                shuffle(list(popups))
            case "*":
                for images in range(int(instruction[1]), int(instruction[2]) + 1):
                    popups.append(ran(int(instruction[1]), int(instruction[2])))

        for popper in popups:
            ad_name = instruction[0] + str(popper) + ".png"
            ad_image = PhotoImage(file=image_dir + "event_images/" + ad_name)
            popup_images.append(ad_image)
            popup = Toplevel(window)
            popup_memory.append(popup)
            popup.title("Click to close!")
            popup.config(height=ad_image.height(), width=ad_image.width())
            ad_container = Label(popup, image=ad_image)
            ad_container.pack(expand=True)
            popup.bind("<Button-1>", lambda ad, p=popup: p.destroy())

            popup.geometry(f"{ad_image.width()}x{ad_image.height()}+"
                           f"{ran(0, popup.winfo_screenwidth() - ad_image.width())}+"
                           f"{ran(0, popup.winfo_screenheight() - ad_image.height())}")


def resize():
    global window, rows, cols, sprite_height, sprite_width, buttons, button_history
    rows = int(window.winfo_height() / sprite_height)
    cols = int(window.winfo_width() / sprite_width)
    button_history += len(buttons)
    for button in buttons:
        button.destroy()
    buttons.clear()
    for fy in range(rows):
        for fx in range(cols):
            button = Button(window)
            button.config(command=lambda b=button: click(b))
            button.place(y=fy * sprite_height, x=fx * sprite_width)
            buttons.append(button)

    for label in labelsY:
        label.destroy()
    labelsY.clear()
    for fy in range(rows):
        label = Label(window)
        label.place(y=fy * sprite_height, x=0)
        labelsY.append(label)
    for label in labelsX:
        label.destroy()
    labelsX.clear()
    for fx in range(cols):
        label = Label(window)
        label.place(y=int(rows * sprite_height - sprite_height * 0.4), x=fx * sprite_width + sprite_width * 0.7)
        labelsX.append(label)

    display()


if __name__ == '__main__':
    window = Tk()
    window.config(height=8 * sprite_height, width=8 * sprite_width)
    start_game()
    window.bind("<Key>", inpt)
    empty = PhotoImage(file=f"{image_dir}Empty.png")
    window.mainloop()
