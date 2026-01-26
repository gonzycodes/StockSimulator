"""
Main module for StockSimulator
Starts the application and handles main menu loop 
"""

import sys

def print_help():
    """Prints a simple help menu to the console."""
    print("\n--- Help Menu ---")
    print("1. In the Main Menu, choose 'Start' to enter the simulation.")
    print("2. Inside the simulation, type 'exit' or 'quit' to go back to the menu.")
    print("---------------------")
    input("\nPress Enter to return to the main menu...")
    
def run_simulation():
    """
    Active simulation loop.
    Runs when user selects 'start' from the main menu.
    """
    print("\n--- Stock Simulator ---")
    print("Type 'exit' or 'quit' to return to the main menu.")
    
    running = True
    while running: 
        # input prompt for the simulation
        user_input = input("\nStocksimulator (Active) > ").strip().lower()
        
        if user_input == "":
            continue
        
        if user_input in ["exit", "quit"]:
            print("Saving Data... Returning to main menu.")
            running = False  # breaks the loop to return to main menu

        elif user_input == "help":
            print_help()
            
        else:
            print(f"Unknown command: '{user_input}'. Type 'help' for assistance.")
            
def main_menu():
    """
    Shows the start menu options.
    Allows user to start the simulation, get help, or exit.
    """

    while True:
        print("\n===============================")
        print("   Welcome to StockSimulator   ")
        print("===============================")
        print("1. Start Simulation")
        print("2. Help")
        print("3. Exit")
        print("===============================")
        
        choice = input("Please select an option (1-3): ").strip()
        
        if choice == "1":
            run_simulation() # starts the simulation loop
        elif choice == "2":
            print_help()     # shows help menu
        elif choice == "3":
            print("Exiting StockSimulator. Goodbye!")
            sys.exit(0)      # exits the application
        else:
            print("Invalid choice. Please select 1, 2, or 3.")
            
if __name__ == "__main__":
    main_menu()  # start the main menu loop
