import random
import mariadb
import dbcreds

# Database setup
conn = mariadb.connect(
            user=dbcreds.user,
            password=dbcreds.password,
            host=dbcreds.host,
            port=dbcreds.port,
            database=dbcreds.database
        )

cursor = conn.cursor()

# Game functions
def signup():
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    cursor.callproc("add_client", (username, password))
    conn.commit()

def signin():
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    cursor.callproc("get_client", (username, password))
    user = cursor.fetchone()
    if user:
        return user[0]
    else:
        print("Invalid username or password. Try again.")
        return None

def create_fighter(client_id):
    name = input("Enter your fighter's name: ")
    moves = select_moves()
    fighter_moves = random.sample(moves, 4)
    cursor.callproc("add_fighter", [client_id, *fighter_moves, name])
    conn.commit()

def select_moves():
    cursor.callproc("get_moves")
    moves = cursor.fetchall()
    for move in moves:
        print(f"{move[0]}. {move[1]} ({move[2]} - {move[3]})")
    selected_moves = []
    for _ in range(4):
        move_id = int(input("Select a move by entering its ID: "))
        selected_moves.append(move_id)
    return selected_moves

def fight(user_id, opponent_strength):
    user_fighter = select_fighter(user_id)
    computer_fighter = select_computer_fighter(opponent_strength)

    print(f"You are fighting {computer_fighter[3]}!")

    while int(user_fighter[6]) > 0 and int(computer_fighter[2]) > 0:
        user_move = select_move(user_fighter)
        user_damage = calculate_damage(user_move)
        computer_damage = calculate_damage(random.choice([computer_fighter[4], computer_fighter[5], computer_fighter[6], computer_fighter[7]]))

        print(f"You dealt {user_damage} damage!")
        print(f"{computer_fighter[3]} dealt {computer_damage} damage!")

        user_fighter[6] -= computer_damage
        computer_fighter[2] -= user_damage

        print(f"Your health: {user_fighter[6]} | {computer_fighter[3]}'s health: {computer_fighter[2]}\n")

    if int(user_fighter[6]) > 0:
        print(f"You defeated {computer_fighter[3]}! You earned {opponent_strength} points!")
        cursor.callproc("add_points", (user_id, opponent_strength))
        conn.commit()
    else:
        print(f"You were defeated by {computer_fighter[3]}. Try again!")

def select_fighter(user_id):
    cursor.callproc("get_fighters", (user_id,))
    fighters = cursor.fetchall()
    print(fighters)
    for fighter in fighters:
        print(f"{fighter[0]}. {fighter[1]}")
    
    while True:
        try:
            fighter_id = int(input("Select a fighter by entering its ID: "))
            cursor.callproc("get_fighter", (fighter_id,))
            user_fighter = cursor.fetchone()

            if user_fighter is not None:
                # Convert health and points to integers
                user_fighter = list(user_fighter)  # Convert to list to allow modifications
                user_fighter[6] = int(user_fighter[6])
                user_fighter[7] = int(user_fighter[7])

                return user_fighter
            else:
                print("Invalid fighter ID. Please enter a valid ID.")
        except ValueError:
            print("Invalid input. Please enter a valid fighter ID.")

def select_computer_fighter(opponent_strength):
    cursor.callproc("get_computer_fighter", (opponent_strength,))
    return cursor.fetchone()

def select_move(user_fighter):
    while True:
        moves = [user_fighter[2], user_fighter[3], user_fighter[4], user_fighter[5]]
        for move in moves:
            cursor.callproc("get_move", (move,))
            print(cursor.fetchone())
        move_id = int(input("Select a move by entering its ID: "))
        if move_id in moves:
            cursor.callproc("get_move", (move_id,))
            return cursor.fetchone()
        else:
            print("Invalid move ID. Please select a valid move.")

def calculate_damage(move):
    return random.randint(move[2], move[3])

def show_leaderboard():
    cursor.execute("SELECT username, points FROM client ORDER BY points DESC LIMIT 10")
    leaderboard = cursor.fetchall()
    print("----- Leaderboard -----")
    for rank, (username, points) in enumerate(leaderboard, start=1):
        print(f"{rank}. {username}: {points} points")

def main():
    while True:
        print("1. Sign Up")
        print("2. Sign In")
        print("3. Leaderboard")
        print("4. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            signup()
        elif choice == '2':
            user_id = signin()
            if user_id:
                print("Welcome!")
                print("1. Create a new fighter")
                print("2. Choose an existing fighter")
                print("3. View fighter details")
                print("4. Fight")
                print("5. Return to Main Menu")
                sub_choice = input("Select an option: ")

                if sub_choice == '1':
                    create_fighter(user_id)
                elif sub_choice == '2':
                    user_fighter = select_fighter(user_id)
                    if user_fighter:
                        print(f"You selected {user_fighter[1]}!")
                elif sub_choice == '3':
                    user_fighter = select_fighter(user_id)
                    if user_fighter:
                        print(f"Fighter Details:")
                        print(f"Name: {user_fighter[1]}")
                        print(f"Health: {user_fighter[6]}")
                        print(f"Points: {user_fighter[7]}")
                        moves = [user_fighter[2], user_fighter[3], user_fighter[4], user_fighter[5]]
                        print("Moves:")
                        for move_id in moves:
                            cursor.callproc("get_move", (move_id,))
                            move = cursor.fetchone()
                            print(f"{move[1]} ({move[2]} - {move[3]})")
                elif sub_choice == '4':
                    print("1. Fight a weak opponent")
                    print("2. Fight a fair opponent")
                    print("3. Fight a strong opponent")
                    print("4. Return to Fighter Menu")
                    opponent_choice = input("Select an opponent: ")

                    if opponent_choice in ('1', '2', '3'):
                        fight(user_id, int(opponent_choice))
                    elif opponent_choice == '4':
                        pass
                    else:
                        print("Invalid choice.")
                elif sub_choice == '5':
                    break
                else:
                    print("Invalid choice.")
        elif choice == '3':
            show_leaderboard()
        elif choice == '4':
            print("Exiting the game. Goodbye!")
            break
        else:
            print("Invalid choice.")

def main_menu():
    while True:
        print("1. Start Game")
        print("2. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            main()
        elif choice == '2':
            print("Exiting the game. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
