from pulp import LpVariable, LpProblem, LpMinimize, lpSum, value
import pandas as pd

# Load demand and capacity data for multiple branches
demanda = pd.read_csv("demanda.csv")
capacidad = pd.read_csv("capacidad.csv")

# Define the time slots from 7:30 AM to 6:30 PM
time_slots = list(range(7, 19))  # Assuming 15-minute slots for simplicity
days_of_week = range(1, 6)  # Assuming a work week from Monday to Friday

# Create a binary variable for each employee, day of the week, time slot, state, branch, and contract type
employees = [1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024]
states = ['Trabaja', 'Pausa Activa', 'Nada']
branches = [60, 61, 62, 63, 64]  # Example branches, adjust as needed
contract_types = ['TC', 'MT']  # Time Completo (TC) and Medio Tiempo (MT)

# Create a binary variable for the absolute difference between demand and capacity
abs_diff = LpVariable.dicts('abs_diff', (days_of_week, time_slots, branches), cat='Binary')

# Create a binary variable for each employee, day of the week, time slot, state, branch, and contract type
x = LpVariable.dicts('x', (days_of_week, time_slots, employees, states, branches, contract_types), cat='Binary')

# Create the LP problem
prob = LpProblem("Employee_Schedule_Optimization_Parte2", LpMinimize)

# Define the function objective to minimize the absolute difference
prob += lpSum(abs_diff[d][t][b] for d in days_of_week for t in time_slots for b in branches)

# Add constraints to ensure that abs_diff reflects the absolute difference
for d in days_of_week:
    for t in time_slots:
        for b in branches:
            for ct in contract_types:
                for e in employees:
                    for s in states:
                        prob += abs_diff[d][t][b] >= x[d][t][e][s][b][ct] * demanda.at[t - 7, 'demanda']

# Restricciones de trabajo continuo antes de pausa o almuerzo (adaptadas para múltiples sucursales)
for d in days_of_week:
    for t in time_slots:
        for b in branches:
            for ct in contract_types:
                for e in employees:
                    if t + 3 in time_slots:
                        prob += lpSum(x[d][t + i][e]['Trabaja'][b][ct] for i in range(4) if t + i in time_slots) >= x[d][t][e]['Trabaja'][b][ct]

                    if t + 8 in time_slots:
                        prob += lpSum(x[d][t + i][e]['Trabaja'][b][ct] for i in range(9) if t + i in time_slots) <= 2 * x[d][t][e]['Trabaja'][b][ct]

# Restricciones para pausas activas (adaptadas para múltiples sucursales)
for d in days_of_week:
    for t in time_slots:
        for b in branches:
            for ct in contract_types:
                for e in employees:
                    if t + 3 in time_slots:
                        prob += lpSum(x[d][t + i]['Pausa Activa'][b][ct] for i in range(4) if t + i in time_slots) <= x[d][t][e]['Trabaja'][b][ct]

# Restricción: Al menos 1 empleado debe estar en algún estado en cada franja horaria
for d in days_of_week:
    for t in time_slots:
        for b in branches:
            for ct in contract_types:
                prob += lpSum(x[d][t][e]['Trabaja'][b][ct] for e in employees) >= 1

# Restricción: Duración de la jornada laboral de 8 horas
for d in days_of_week:
    for b in branches:
        for ct in contract_types:
            for e in employees:
                prob += lpSum(x[d][t][e]['Trabaja'][b][ct] for t in time_slots) == 8

# Restricción: El horario de los empleados debe ser continuo
for d in days_of_week:
    for t in time_slots:
        for b in branches:
            for ct in contract_types:
                for e in employees:
                    prob += lpSum(x[d][t][e][s][b][ct] for s in states if s != 'Nada') <= 1

# Restricción: Último estado de la jornada laboral debe ser Trabaja
for d in days_of_week:
    for b in branches:
        for ct in contract_types:
            for e in employees:
                prob += lpSum(x[d][t][e][s][b][ct] for t in time_slots for s in states if s == 'Trabaja') == 1

# Restricción: Duración de la franja de trabajo entre 1 y 2 horas
for d in days_of_week:
    for t in time_slots:
        for b in branches:
            for ct in contract_types:
                for e in employees:
                    prob += lpSum(x[d][t][e][s][b][ct] for s in states if s != 'Nada') >= 1
                    prob += lpSum(x[d][t][e][s][b][ct] for s in states if s != 'Nada') <= 2

# Solve the problem
prob.solve()

# Create a DataFrame to store the schedule
schedule_df = pd.DataFrame(index=pd.MultiIndex.from_product([days_of_week, time_slots], names=['day', 'hour']),
                           columns=pd.MultiIndex.from_product([employees, branches, contract_types], names=['employee', 'branch', 'contract_type']), data="")

# Populate the DataFrame with the optimized schedule
for d in days_of_week:
    for t in time_slots:
        for b in branches:
            for ct in contract_types:
                for e in employees:
                    for s in states:
                        if value(x[d][t][e][s][b][ct]) == 1:
                            schedule_df.at[(d, t), (e, b, ct)] = s

# Export the DataFrame to a CSV file
schedule_df.to_csv("optimized_horario_parte2.csv", index_label=["day", "hour"])
print("Resultados guardados en el archivo optimized_horario_parte2.csv")



