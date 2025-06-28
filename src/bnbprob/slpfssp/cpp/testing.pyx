from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr, make_shared

from bnpprob.slpfssp.cpp.environ import Job, JobPtr, Sigma


cdef vector[vector[int]] py2vec2d(list l):
    cdef vector[vector[int]] out
    cdef vector[int] vrow

    for row in l:
        vrow = vector[int]()
        for x in row:
            vrow.push_back(<int>x)
        out.push_back(vrow)
    return out

cdef vector[int] py2vec1d(list l):
    cdef vector[int] out
    for x in l:
        out.push_back(<int>x)
    return out

cpdef list[list[int]] job_to_bottom(
    j: int,
    p: list[list[int]],
    r: list[list[int]],
    q: list[list[int]],
    C: list[list[int]],
    m: list[int]
):
    cdef vector[vector[int]] p_ = py2vec2d(p)
    cdef vector[vector[int]] r_ = py2vec2d(r)
    cdef vector[vector[int]] q_ = py2vec2d(q)
    cdef vector[vector[int]] C_ = py2vec2d(C)
    cdef vector[int] m_ = py2vec1d(m)
    cdef shared_ptr[vector[vector[int]]] p_ptr = make_shared[vector[vector[int]]](p_)
    cdef shared_ptr[vector[int]] m_ptr = make_shared[vector[int]](m_)
    cdef JobPtr job = make_shared[Job](j, p_ptr)
    cdef Sigma sigma = Sigma(m_ptr, vector[JobPtr](), C_)
    job.r = r_
    job.q = q_
    sigma.job_to_bottom(job)
    # Convert sigma.C back to Python list
    return [[int(x) for x in row] for row in sigma.C]

cpdef list[list[int]] job_to_top(
    j: int,
    p: list[list[int]],
    r: list[list[int]],
    q: list[list[int]],
    C: list[list[int]],
    m: list[int]
):
    cdef vector[vector[int]] p_ = py2vec2d(p)
    cdef vector[vector[int]] r_ = py2vec2d(r)
    cdef vector[vector[int]] q_ = py2vec2d(q)
    cdef vector[vector[int]] C_ = py2vec2d(C)
    cdef vector[int] m_ = py2vec1d(m)
    cdef shared_ptr[vector[vector[int]]] p_ptr = make_shared[vector[vector[int]]](p_)
    cdef shared_ptr[vector[int]] m_ptr = make_shared[vector[int]](m_)
    cdef JobPtr job = make_shared[Job](j, p_ptr)
    cdef Sigma sigma = Sigma(m_ptr, vector[JobPtr](), C_)
    job.r = r_
    job.q = q_
    sigma.job_to_top(job)
    # Convert sigma.C back to Python list
    return [[int(x) for x in row] for row in sigma.C]
