from pulp import LpVariable, LpProblem, LpMinimize, lpSum, value
import pandas as pd

# Load demand and capacity data
demanda = pd.read_csv("demanda.csv")
capacidad = pd.read_csv("capacidad.csv")

# Define the time slots from 7:30 AM to 6:30 PM
time_slots = list(range(7, 19))  # Assuming 15-minute slots for simplicity
days_of_week = range(1, 7)  # Assuming a work week from Monday to Saturday

# Create a binary variable for each employee, day of the week, time slot, and state
employees = list(capacidad['documento'])
states = ['Trabaja', 'Pausa Activa', 'Almuerza', 'Nada']

# Create a binary variable for each employee, day of the week, time slot, and state
x = LpVariable.dicts('x', (employees, days_of_week, time_slots, states), cat='Binary')

# Create the LP problem
prob = LpProblem("Employee_Schedule_Optimization", LpMinimize)

# Demand and Capacity constraints for Part 1
for t in time_slots:
    for d in days_of_week:
        prob += lpSum(x[e][d][t]['Trabaja'] for e in employees) >= demanda.at[t, 'demanda']
        prob += lpSum(x[e][d][t]['Trabaja'] for e in employees) <= capacidad[(capacidad['contrato'] == 'TC')]['documento'].count()

# Additional constraints for Part 2
for e in employees:
    for d in days_of_week:
        if capacidad.loc[capacidad['documento'] == e, 'contrato'].values[0] == 'TC':
            # Time for lunch for full-time employees on weekdays
            prob += lpSum(x[e][d][t]['Almuerza'] for t in time_slots) == 1.5
            # Constant start and end time for full-time employees on weekdays
            prob += lpSum(x[e][d][t]['Trabaja'] for t in time_slots if t < 7 or t >= 19) == 0  # no work before 7:30 am and after 4:30 pm
        else:
            # Constant start time for part-time employees on weekdays
            prob += lpSum(x[e][d][t]['Trabaja'] for t in time_slots if t < 7 or t >= 19) == 0  # no work before 7:30 am and after 4:30 pm

        # Additional constraints for almuerzo
        if d in range(1, 6):  # Check if it's a weekday
            if capacidad.loc[capacidad['documento'] == e, 'contrato'].values[0] == 'TC':
                prob += lpSum(x[e][d][t]['Almuerza'] for t in range(7, 19)) == 1.5  # Lunch from 12:00 pm to 1:30 pm
                prob += lpSum(x[e][d][t]['Almuerza'] for t in range(1, 7)if t in time_slots) == 0  # No lunch before 7:30 am
                prob += lpSum(x[e][d][t]['Almuerza'] for t in range(19, 24)if t in time_slots) == 0  # No lunch after 4:30 pm
            else:
                prob += lpSum(x[e][d][t]['Almuerza'] for t in time_slots) == 0  # No lunch for part-time employees

# Additional constraints for MT employees
for e in employees:
    contrato_empleado = capacidad.loc[capacidad['documento'] == e, 'contrato'].iloc[0]
    if contrato_empleado == 'MT':
        for d in days_of_week:
            # No lunch for MT employees
            prob += lpSum(x[e][d][t]['Almuerza'] for t in time_slots) == 0

            # Constant start and end time for MT employees on weekdays
            prob += lpSum(x[e][d][t]['Trabaja'] for t in range(1, 7)if t in time_slots) == 0  # no work before 7:30 am
            prob += lpSum(x[e][d][t]['Trabaja'] for t in range(18, 24)if t in time_slots) == 0  # no work after 4:30 pm

# Constant end time for all employees on all days
for e in employees:
    prob += lpSum(x[e][d][t]['Trabaja'] for d in days_of_week for t in range(18, 24)if t in time_slots) == 0  # no work after 4:30 pm

# All employees must start work between 7:30 am and 4:30 pm on weekdays
for e in employees:
    prob += lpSum(x[e][d][t]['Trabaja'] for d in days_of_week for t in range(7, 19)) >= 1
    prob += lpSum(x[e][d][t]['Trabaja'] for d in days_of_week for t in range(18, 24)if t in time_slots) == 0

# All employees must start work between 7:30 am and 11:00 am on Saturdays
for e in employees:
    for d in days_of_week:
        if d == 6:  # Check if it's Saturday
            prob += lpSum(x[e][d][t]['Trabaja'] for t in range(1, 7)if t in time_slots) == 0  # no work before 7:30 am
            prob += lpSum(x[e][d][t]['Trabaja'] for t in range(11, 24)if t in time_slots) == 0  # no work after 11:00 am

# Solve the problem
prob.solve()

# Create a DataFrame to store the schedule
schedule_df = pd.DataFrame(index=pd.MultiIndex.from_product([days_of_week, time_slots], names=['day', 'hour']),
                           columns=employees, data="")

# Populate the DataFrame with the optimized schedule
for d in days_of_week:
    for t in time_slots:
        for e in employees:
            for s in states:
                if value(x[e][d][t][s]) == 1:
                    schedule_df.at[(d, t), e] = s

# Export the DataFrame to a CSV file
schedule_df.to_csv("horario_parte2.csv", index_label=["day", "hour"])


