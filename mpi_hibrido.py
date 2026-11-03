import argparse
import time
from pathlib import Path

from baseline_secuencial import leer_seeds
from sudoku import puede_colocar

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

TAG_TRABAJO = 20
TAG_RESULTADO = 21
TAG_FIN = 22


def crear_ramas(tablero):
    """Crea ramas a partir de la primera casilla vacía."""
    for fila in range(9):
        for columna in range(9):
            if tablero[fila][columna] != 0:
                continue
            ramas = []
            for valor in range(1, 10):
                if puede_colocar(tablero, fila, columna, valor):
                    rama = [fila[:] for fila in tablero]
                    rama[fila][columna] = valor
                    ramas.append(rama)
            return ramas
    return [tablero]


def resolver_rama(tablero, coordinador=None):
    """Resuelve una rama y permite cancelarla cuando el grupo ya tiene solución."""
    for fila in range(9):
        for columna in range(9):
            if coordinador is not None and comm.Iprobe(source=coordinador, tag=TAG_FIN):
                comm.recv(source=coordinador, tag=TAG_FIN)
                return False, None
            if tablero[fila][columna] != 0:
                continue
            for valor in range(1, 10):
                if puede_colocar(tablero, fila, columna, valor):
                    tablero[fila][columna] = valor
                    resuelto, solucion = resolver_rama(tablero, coordinador)
                    if resuelto:
                        return True, solucion
                    tablero[fila][columna] = 0
            return False, None
    return True, tablero


def repartir_ramas(tablero, trabajadores):
    """Reparte ramas dentro de un grupo y espera una solución."""
    if not trabajadores:
        return resolver_rama([fila[:] for fila in tablero])[0]

    ramas = crear_ramas(tablero)
    pendientes = list(ramas)
    activos = set()

    for trabajador in trabajadores:
        if pendientes:
            comm.send(pendientes.pop(0), dest=trabajador, tag=TAG_TRABAJO)
            activos.add(trabajador)
        else:
            comm.send(None, dest=trabajador, tag=TAG_FIN)

    solucion = None
    while activos and solucion is None:
        estado = MPI.Status()
        resultado = comm.recv(source=MPI.ANY_SOURCE, tag=TAG_RESULTADO, status=estado)
        trabajador = estado.Get_source()
        activos.discard(trabajador)
        resuelto, candidato = resultado
        if resuelto:
            solucion = candidato
            for destino in activos | {trabajador}:
                comm.send(None, dest=destino, tag=TAG_FIN)
        elif pendientes:
            comm.send(pendientes.pop(0), dest=trabajador, tag=TAG_TRABAJO)
            activos.add(trabajador)
        else:
            comm.send(None, dest=trabajador, tag=TAG_FIN)
    return solucion is not None


def grupo_de_rank(rangos):
    """Devuelve el índice y los ranks del grupo al que pertenece este proceso."""
    for indice, (inicio, fin) in enumerate(rangos):
        if inicio <= rank < fin:
            return indice, list(range(inicio, fin))
    raise RuntimeError(f"rank {rank} no pertenece a ningún grupo")


def trabajar():
    """Resuelve ramas que le envía el líder de su grupo."""
    indice, rangos = grupo_de_rank(rangos_grupos)
    lider = rangos[0]
    if rank == lider:
        return
    while True:
        rama = comm.recv(source=lider, tag=MPI.ANY_TAG)
        if rama is None:
            return
        comm.send(resolver_rama(rama, lider), dest=lider, tag=TAG_RESULTADO)


def main():
    global args, rangos_grupos
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ruta", type=Path, default=Path(__file__).parent / "seeds.txt",
                        help="archivo de seeds (por defecto: ../seeds.txt)")
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--id", "--seed", help="resolver solo la seed con este ID")
    seleccion.add_argument("--all", action="store_true", help="resolver todos los seeds")
    args = parser.parse_args()

    if rank == 0:
        try:
            seeds = leer_seeds(args.ruta)
            if not seeds:
                parser.error(f"no se encontraron seeds en {args.ruta}")
            if args.id:
                if args.id not in seeds:
                    parser.error(f"ID '{args.id}' no existe. Disponibles: {', '.join(seeds)}")
                seleccionados = [(args.id, seeds[args.id])]
            else:
                seleccionados = list(seeds.items())
        except OSError as error:
            parser.error(f"no se pudo leer {args.ruta}: {error}")
    else:
        seleccionados = None

    seleccionados = comm.bcast(seleccionados, root=0)
    grupos = min(size, len(seleccionados))
    rangos_grupos = []
    for indice in range(grupos):
        inicio = indice * size // grupos
        fin = (indice + 1) * size // grupos
        rangos_grupos.append((inicio, fin))

    indice_grupo, rangos = grupo_de_rank(rangos_grupos)
    lider = rangos[0]
    ids_grupo = seleccionados[indice_grupo::grupos]
    semillas = dict(seleccionados)

    comm.Barrier()
    inicio_total = time.perf_counter() if rank == 0 else None
    resultados = []
    if rank == lider:
        trabajadores = rangos[1:]
        for identificador, _ in ids_grupo:
            inicio = time.perf_counter()
            resuelto = repartir_ramas(semillas[identificador], trabajadores)
            segundos = time.perf_counter() - inicio
            resultados.append((identificador, resuelto, segundos))
            print(f"\nID: {identificador}")
            print("Resuelto" if resuelto else "Sin solución")
            print(f"{'Tiempo' if args.id else 'Tiempo parcial'}: {segundos:.6f} segundos",
                  flush=True)
    else:
        trabajar()

    comm.Barrier()
    if rank == 0 and not args.id:
        print(f"\nTiempo total: {time.perf_counter() - inicio_total:.6f} segundos")


if __name__ == "__main__":
    main()
