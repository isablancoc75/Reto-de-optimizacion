from pulp import LpVariable, LpProblem, LpMinimize, lpSum, value
import pandas as pd

# Load demand and capacity data
demanda = pd.read_csv("demanda.csv")
capacidad = pd.read_csv("capacidad.csv")

# Define the time slots from 7:30 AM to 6:30 PM
time_slots = list(range(7, 19))  # Assuming 15-minute slots for simplicity
days_of_week = range(1, 6)  # Assuming a work week from Monday to Friday

# Create a binary variable for each employee, day of the week, time slot, and state
employees = list(capacidad['documento'])
states = ['Trabaja', 'Pausa Activa', 'Almuerza', 'Nada']

# Create a binary variable for each employee, day of the week, time slot, and state
x = LpVariable.dicts('x', (employees, days_of_week, time_slots, states), cat='Binary')

# Create the LP problem
prob = LpProblem("Employee_Schedule_Optimization", LpMinimize)

# Replace column names with the correct names in the demanda DataFrame
for e in employees:
    for d in days_of_week:
        for t in time_slots:
            prob += lpSum(x[e][d][t][s] for s in states) == 1  # Employee is in one state at a time
            
            # Verificar si hay al menos una fila que cumple con la condición
            demanda_filtrada = demanda[(demanda['suc_cod'] == 834) & (demanda['fecha_hora'] == f'12/11/2023 {t}:00')]
            
            if not demanda_filtrada.empty:
                prob += x[e][d][t]['Trabaja'] - demanda_filtrada['demanda'].values[0] <= 0


# Restricciones de trabajo continuo antes de pausa o almuerzo
for e in employees:
    for d in days_of_week:
        for t in time_slots:
            if t + 3 in time_slots:
                prob += lpSum(x[e][d][t + i]['Trabaja'] for i in range(4) if t + i in time_slots) >= x[e][d][t]['Trabaja']

            if t + 8 in time_slots:
                prob += lpSum(x[e][d][t + i]['Trabaja'] for i in range(9) if t + i in time_slots) <= 2 * x[e][d][t]['Trabaja']

            if t + 4 in time_slots and t + 12 in time_slots:
                prob += lpSum(x[e][d][t + i]['Almuerza'] for i in range(9) if t + i in time_slots) == 1

            if t + 4 in time_slots:
                prob += lpSum(x[e][d][t + i]['Almuerza'] for i in range(5) if t + i in time_slots) == 1

            if t + 12 in time_slots:
                prob += lpSum(x[e][d][t + i]['Almuerza'] for i in range(13, 15) if t + i in time_slots) == 1

# Restricciones para pausas activas
for e in employees:
    for d in days_of_week:
        for t in time_slots:
            if t + 3 in time_slots:
                prob += lpSum(x[e][d][t + i]['Pausa Activa'] for i in range(4) if t + i in time_slots) <= x[e][d][t]['Trabaja']

# Restricción: Al menos 1 empleado debe estar en algún estado en cada franja horaria
for d in days_of_week:
    for t in time_slots:
        prob += lpSum(x[e][d][t]['Trabaja'] for e in employees) >= 1

# Restricción: Duración de la jornada laboral de 8 horas
for e in employees:
    for d in days_of_week:
        prob += lpSum(x[e][d][t]['Trabaja'] for t in time_slots) == 8

# Restricción: El horario de los empleados debe ser continuo
for e in employees:
    for d in days_of_week:
        for t in time_slots:
            prob += lpSum(x[e][d][t][s] for s in states if s != 'Nada') <= 1

# Restricción: Último estado de la jornada laboral debe ser Trabaja
for e in employees:
    for d in days_of_week:
        prob += lpSum(x[e][d][t][s] for t in time_slots for s in states if s == 'Trabaja') == 1

# Restricción: Duración de la franja de trabajo entre 1 y 2 horas
for d in days_of_week:
    for t in time_slots:
        prob += lpSum(x[e][d][t][s] for e in employees for s in states if s != 'Nada') >= 1
        prob += lpSum(x[e][d][t][s] for e in employees for s in states if s != 'Nada') <= 2

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
schedule_df.to_csv("horario_parte1.csv", index_label=["day", "hour"])













