"""
Application entry point for TradeSim.

This module initializes logging, logs app start/exit, and provides a main()
function that returns a process exit code. It handles the main menu loop.
"""

import sys
from src.logger import init_logging_from_env, get_logger

# Initialize logger
log = get_logger(__name__)

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
        user_input = input("\nTradeSim (Active) > ").strip().lower()
        
        if user_input == "":
            continue
        
        if user_input in ["exit", "quit"]:
            log.info("User returned to main menu from simulation")
            print("Saving Data... Returning to main menu.")
            running = False 

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
        print("   Welcome to TradeSim         ")
        print("===============================")
        print("1. Start Simulation")
        print("2. Help")
        print("3. Exit")
        print("===============================")
        
        choice = input("Please select an option (1-3): ").strip()
        
        if choice == "1":
            log.info("User started simulation")
            run_simulation()
        elif choice == "2":
            print_help()
        elif choice == "3":
            print("Exiting TradeSim. Goodbye!")
            # We use return instead of sys.exit() so main() can log the exit event
            return
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

def main() -> int:
    """
    Run the application and return an exit code.
    Wraps the main_menu in error handling and logging.
    
    Returns:
        0 on success, 1 on unhandled errors.
    """
    init_logging_from_env()
    log.info("App start")

    try:
        # Launch the main menu loop
        main_menu()
        return 0
    except Exception:
        log.exception("Unhandled exception")
        return 1
    finally:
        log.info("App exit")

if __name__ == "__main__":
    sys.exit(main())
