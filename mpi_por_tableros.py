import argparse
import time
from pathlib import Path

from baseline_secuencial import leer_seeds
from sudoku import resolver

from mpi4py import MPI

# Inicialización de MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def dividir_tableros(seeds: dict) -> list:
    """Divide los tableros de Sudoku en bloques para cada proceso."""
    tableros = list(seeds.items())
    num_tableros, sobrantes = divmod(len(tableros), size)
    chunks = []
    inicio = 0
    for indice in range(size):
        cantidad = num_tableros + (1 if indice < sobrantes else 0)
        chunks.append(tableros[inicio:inicio + cantidad])
        inicio += cantidad
    return chunks

def resolver_por_tablero_mpi(chunk: list) -> bool:
    """Resuelve un tablero de Sudoku dado usando MPI y devuelve True si se resolvió, False si no tiene solución."""
    # Procesamiento de los tableros asignados a cada proceso
    todo_ok = True
    for id, tablero in chunk:
        resuelto = resolver(tablero)
        if resuelto:
            print(f"Proceso {rank} resolvió el tablero con ID: {id}")
        else:
            print(f"Proceso {rank} no encontró solución para el tablero con ID: {id}")
            todo_ok = False
    return todo_ok

def main():
    # Lectura de argumentos
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ruta", type=Path, default=Path(__file__).parent / "seeds.txt",
                        help="archivo de seeds (por defecto: seeds.txt junto a este programa)")
    args = parser.parse_args()

    try:
        seeds = leer_seeds(args.ruta)
        if not seeds:
            parser.error(f"no se encontraron seeds en {args.ruta}")

        # Dividir los tableros en bloques para cada proceso
        if rank == 0:
            chunks = dividir_tableros(seeds)
            print(f"Proceso {rank}: División de tableros en {len(chunks)} bloques para {size} procesos.")
        else:
            chunks = None
        chunk = comm.scatter(chunks, root=0)  # Distribuir los bloques a cada proceso
        
        # Ejecución del trabajo
        if rank == 0:
            start_time = time.perf_counter()
        result = resolver_por_tablero_mpi(chunk)
        print(f"Proceso {rank}: todos los tableros procesados. Resultado: {'Todo ok :)' if result else 'ehmmm...'}")
        comm.Barrier()  # Espera a que todos los procesos terminen
        results = comm.gather(result, root=0)  # Recopilar resultados de todos los procesos
        if rank == 0:
            print(f"Resultado final: {'Todos los tableros resueltos' if all(results) else 'Algunos tableros no tienen solución'}")
            end_time = time.perf_counter()
            print(f"Tiempo total de ejecución: {end_time - start_time:.2f} segundos")

    except OSError as error:
        parser.error(f"no se pudo leer {args.ruta}: {error}")


if __name__ == "__main__":
    main()