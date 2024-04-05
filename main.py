import pandas as pd
import json
from categories import read_category_data, add_item_to_category, write_categories

#TODO: replace this with the path to your payments CSV file
csv_file_path = "payments.example.csv"
budget_file_path = "budget.example.json"
output_file_path = f"categorized-{csv_file_path}"

df_raw = pd.read_csv(csv_file_path, delimiter=';')
df_raw["amount"] = pd.to_numeric(df_raw["Betrag (€)"].str.replace(',', '.'), errors='coerce') * -1
df_raw['payment_name'] = df_raw['Zahlungsempfänger*in'].str.lower()
df = df_raw[['payment_name', 'amount']].copy() 
df.loc[:, 'category'] = None

category_map = read_category_data()

for index, row in df.iterrows():
    payment_name = row['payment_name'].lower()
    category_assigned = False

    for category, terms in category_map.items():
        if any(term.lower() in payment_name for term in terms):
            df.at[index, 'category'] = category
            category_assigned = True
            break

    if not category_assigned:
        print()
        categories_list = list(category_map.keys())
        print(f"No category found for: {payment_name}")
        print("Choose a category for this payment from the following list:")
        for i, category in enumerate(categories_list, 1):
            print(f"{i}. {category}")
        print(f"{len(categories_list)+1}. Add a new category")

        try:
            category_choice = int(input("Enter the number for the selected category: "))
            if 1 <= category_choice <= len(categories_list):
                user_category = categories_list[category_choice - 1]
                user_term = input(f"Enter a matching term for this payment to recognize similar payments in the future under '{user_category}' (leave empty to add the original name): ")
                if len(user_term) == 0:
                    user_term = payment_name
                category_map[user_category].append(user_term)
                df.at[index, 'category'] = user_category
                add_item_to_category(user_category, user_term)
            else:
                print("Invalid choice. Skipping this payment.")
        except ValueError:
            print("Invalid input. Skipping this payment.")

df = df[df['category'] != 'Ignore'] 
df = df.sort_values(by='category')

df['row_number'] = range(2, len(df) + 2)

category_rows = df.groupby('category')['row_number'].agg(first='min', last='max').reset_index()

df = pd.merge(df, category_rows, on='category', how='left')
spent_per_category = df[['category', 'first', 'last']].drop_duplicates('category')
spent_per_category['spent'] = '=SUM(B' + spent_per_category['first'].astype(str) + ':B' + spent_per_category['last'].astype(str) + ')'

with open(budget_file_path, 'r') as file:
    budget = json.load(file)

spent_per_category['budget'] = spent_per_category['category'].apply(lambda x: budget.get(x, 0))
total_rows_before_budget = len(df) + 5
diffs = [f'=B{i}-C{i}' for i in range(total_rows_before_budget, total_rows_before_budget + 4)]
spent_per_category['diff'] = diffs

spent_per_category = spent_per_category[['category', 'budget', 'spent', 'diff']]

df = df.drop(columns=['row_number', 'first', 'last'])
df.to_csv(output_file_path, index=False)
with open(output_file_path, 'a') as f:
    f.write("\n\n")
spent_per_category.to_csv(output_file_path, mode='a', index=False)

write_categories(category_map)

