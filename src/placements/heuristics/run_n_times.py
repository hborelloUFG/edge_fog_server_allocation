import os
import sys

# Verifica se pelo menos um argumento foi passado
if len(sys.argv) < 2:
    print("Uso: python meu_script.py <argumento numero inteiro>")
    sys.exit(1)

# O primeiro argumento (sys.argv[0]) é o nome do script, então o argumento real começa em sys.argv[1]
model = sys.argv[1]
num_execucoes = int(sys.argv[2])

dict_model = {'m1': 'm1_nodes_minimize_allocations.py ',
              'm2': 'm2_nodes_minimize_allocations.py ',
              'm3': 'm3_nodes_minimize_hops.py ',
              'm4': 'm4_nodes_minimize_hops_limited.py ',}

# Defina o comando ou script que deseja executar
comando_experimento = dict_model[model]

# print(comando_experimento, num_execucoes)

# Loop para executar o experimento várias vezes
for i in range(num_execucoes):
    # Gere um nome de arquivo único para cada execução
    comando = "python " + comando_experimento + f"{i + 1}"
    # print(comando)
    
    # Execute o comando do experimento e redirecione a saída para o arquivo de resultados
    os.system(f"{comando}")
    
    print(f"Execution {i + 1} completed and results saved!")
