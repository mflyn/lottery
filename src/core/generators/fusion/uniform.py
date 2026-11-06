"""Uniform legal ticket/portfolio sampling, independent of scoring preferences."""
import math


def uniform_ticket(areas, rng):
    return tuple(tuple(sorted(int(x) for x in rng.choice(n,k,replace=False)+1)) for n,k in areas)


def unrank_combination(rank, n, k):
    values, start = [], 1
    for remaining in range(k,0,-1):
        for value in range(start,n+1):
            block = math.comb(n-value,remaining-1)
            if rank < block:
                values.append(value); start = value+1
                break
            rank -= block
    return tuple(values)


def uniform_portfolio(count, areas, rng):
    sizes = [math.comb(n,k) for n,k in areas]
    total = math.prod(sizes)
    tickets = []
    for index in rng.choice(total,count,replace=False):
        rank, ticket = int(index), []
        for (n,k), size in zip(areas,sizes):
            rank, area_rank = divmod(rank,size)
            ticket.append(unrank_combination(area_rank,n,k))
        tickets.append(tuple(ticket))
    return tickets
