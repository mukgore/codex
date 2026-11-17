"""Bounded bisection of unresolved interval evaluations, never point sampling.

The evaluator owns the enclosure assumptions. A finite return value does not
validate those assumptions or certify collision clearance.
"""
import math


def refine(evaluate, start, end, *, max_depth, unresolved_type, retry_reason):
    if (not callable(evaluate) or type(max_depth) is not int or not 0 <= max_depth <= 8
            or not all(math.isfinite(t) for t in (start, end)) or not start < end
            or not isinstance(unresolved_type, type) or not issubclass(unresolved_type, Exception)
            or not isinstance(retry_reason, str) or not retry_reason):
        raise ValueError('Finite increasing interval and bounded explicit refinement required')
    attempts = []; terminals = []; values = {}

    def visit(a, b, depth, address):
        row = dict(address=address, depth=depth, start=a, end=b)
        attempts.append(row)
        try:
            value = evaluate(a, b)
        except unresolved_type as error:
            row.update(status='UNRESOLVED', reason=str(error))
            midpoint = a+(b-a)/2
            if str(error) == retry_reason and depth < max_depth and a < midpoint < b:
                row['status'] = 'SPLIT'
                visit(a, midpoint, depth+1, address+'0')
                visit(midpoint, b, depth+1, address+'1')
                return
            row['stop_reason'] = ('NON_RETRYABLE_REASON' if str(error) != retry_reason else
                                  'DEPTH_LIMIT' if depth == max_depth else 'NO_INTERIOR_FLOAT')
        else:
            row.update(status='CONDITIONAL_CANDIDATE')
            values[address] = value
        terminals.append(dict(row))

    visit(float(start), float(end), 0, 'r')
    if (len(attempts) > 2**(max_depth+1)-1 or terminals[0]['start'] != start
            or terminals[-1]['end'] != end
            or any(a['end'] != b['start'] for a, b in zip(terminals, terminals[1:]))):
        raise AssertionError('Refinement partition/accounting invariant failed')
    return dict(attempts=attempts, terminals=terminals, values=values,
                complete=all(r['status'] == 'CONDITIONAL_CANDIDATE' for r in terminals),
                backend_error_bounds_validated=False, CCD_clearance=False)
