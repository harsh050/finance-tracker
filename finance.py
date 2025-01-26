import json
import datetime

class FinanceManager:
    def __init__(self):
        self.data = {
            "income": 0,
            "expenses": {},
            "budget": 0,
            "investments": [],
            "savings_goal": 0,
            "transaction_history": []
        }

    def set_income(self):
        try:
            income = float(input("What's your monthly income? "))
            self.data["income"] = income
            print(f"Great! Your monthly income is set to {income}.")
        except ValueError:
            print("Oops! Please enter a valid number.")

    def set_budget(self):
        try:
            budget = float(input("How much do you want to allocate as your monthly budget? "))
            self.data["budget"] = budget
            print(f"Your budget of {budget} has been successfully saved.")
        except ValueError:
            print("Oops! Please enter a valid number.")

    def set_savings_goal(self):
        try:
            goal = float(input("What is your savings goal for this month? "))
            self.data["savings_goal"] = goal
            print(f"Savings goal of {goal} is now set.")
        except ValueError:
            print("Oops! Please enter a valid number.")

    def add_expense(self):
        category = input("Enter the category of your expense (e.g., food, rent): ").strip()
        try:
            amount = float(input(f"How much did you spend on {category}? "))
            if category in self.data["expenses"]:
                self.data["expenses"][category] += amount
            else:
                self.data["expenses"][category] = amount
            print(f"Expense of {amount} added to {category}.")

            # Log the transaction
            self.data["transaction_history"].append({
                "type": "expense",
                "category": category,
                "amount": amount,
                "date": str(datetime.datetime.now())
            })
        except ValueError:
            print("Oops! Please enter a valid number.")

    def view_expenses(self):
        print("\nHere are your expenses so far:")
        for category, amount in self.data["expenses"].items():
            print(f"  - {category}: {amount}")

        total_expenses = sum(self.data["expenses"].values())
        print(f"Total Expenses: {total_expenses}")

        if total_expenses > self.data["budget"]:
            print("Heads up! You've exceeded your budget.")
        else:
            remaining_budget = self.data["budget"] - total_expenses
            print(f"You still have {remaining_budget} left in your budget.")

    def add_investment(self):
        investment = input("What kind of investment did you make (e.g., mutual fund, stock)? ").strip()
        try:
            amount = float(input(f"How much did you invest in {investment}? "))
            self.data["investments"].append({"type": investment, "amount": amount, "date": str(datetime.datetime.now())})
            print(f"Your investment of {amount} in {investment} has been recorded.")
        except ValueError:
            print("Oops! Please enter a valid number.")

    def view_investments(self):
        print("\nHere are your investments:")
        for inv in self.data["investments"]:
            print(f"  - {inv['type']}: {inv['amount']} (Date: {inv['date']})")

    def view_transaction_history(self):
        print("\nTransaction History:")
        for transaction in self.data["transaction_history"]:
            print(f"  {transaction['date']} - {transaction['type'].capitalize()} - {transaction['category'] if 'category' in transaction else transaction['type']}: {transaction['amount']}")

    def calculate_savings(self):
        total_expenses = sum(self.data["expenses"].values())
        savings = self.data["income"] - total_expenses
        print(f"\nYour current savings amount to: {savings}")
        if savings < self.data["savings_goal"]:
            print(f"You're {self.data['savings_goal'] - savings} short of your savings goal.")
        else:
            print("Fantastic! You've achieved your savings goal.")

    def save_data(self):
        with open("finance_data.json", "w") as file:
            json.dump(self.data, file, indent=4)
        print("All your data has been saved securely.")

    def load_data(self):
        try:
            with open("finance_data.json", "r") as file:
                self.data = json.load(file)
            print("Previous data loaded successfully.")
        except FileNotFoundError:
            print("No previous data found. Starting fresh.")

    def run(self):
        self.load_data()

        while True:
            print("\nWelcome to the Finance Manager!")
            print("1. Set Your Income")
            print("2. Define Your Budget")
            print("3. Set a Savings Goal")
            print("4. Add an Expense")
            print("5. View Your Expenses")
            print("6. Record an Investment")
            print("7. Check Your Investments")
            print("8. Review Your Transaction History")
            print("9. Calculate Your Savings")
            print("10. Save and Exit")

            choice = input("What would you like to do? Choose an option: ")

            if choice == "1":
                self.set_income()
            elif choice == "2":
                self.set_budget()
            elif choice == "3":
                self.set_savings_goal()
            elif choice == "4":
                self.add_expense()
            elif choice == "5":
                self.view_expenses()
            elif choice == "6":
                self.add_investment()
            elif choice == "7":
                self.view_investments()
            elif choice == "8":
                self.view_transaction_history()
            elif choice == "9":
                self.calculate_savings()
            elif choice == "10":
                self.save_data()
                print("Thank you for using the Finance Manager. Goodbye!")
                break
            else:
                print("Sorry, I didn't catch that. Please select a valid option.")

if __name__ == "__main__":
    manager = FinanceManager()
    manager.run()
